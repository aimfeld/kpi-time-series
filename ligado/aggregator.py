# ----------------------------------------------------------------------------------------------------------------------
# Data preprocessing and aggregation
# ----------------------------------------------------------------------------------------------------------------------

from ligado import config as cfg
from datetime import timedelta
import numpy as np
import pandas as pd
from numpy import NaN
from scipy.stats import ttest_1samp
from typing import List

def get_kpi_values_pivot(df_kpi_values: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a pivoted kpi values dataframe, useful for plotting.
    """
    return df_kpi_values.pivot_table(index='meanID', columns='kpiName', values='value')


def filter_by_org_node(df: pd.DataFrame, org_node: pd.Series) -> pd.DataFrame:
    """
    Return a dataframe containing only data of a given org node and its children.
    The dataframe must contain orgNodeLeft and orgNodeRight fields.
    """
    return df.loc[(df['orgNodeLeft'] >= org_node.left) & (df['orgNodeRight'] <= org_node.right)]


def get_kpi_aggregates(df_kpi_values: pd.DataFrame, timebin: str, mean_only=False) -> pd.DataFrame:
    """
    Returns a dataframe containing the KPI mean and the number of item answer for every timebin
    
    Parameters
    ----------
    df_kpi_values   : Dataframe with kpi data
    timebin         : string 'day'|'week'|'month'
    mean_only       : If true, drop multi level columns and return only mean value
    """
    period_map = {'day': 'D', 'week': 'W', 'month': 'M'}

    # Extract yyyy-mm from datetime index and assign to new column 'month'
    df_kpi_values[timebin] = df_kpi_values.index.to_period(period_map[timebin])

    # Aggregate the data by month and calculate the mean of the KPI values and the sum of item answers
    aggregator = {'value': 'mean', 'answers': 'sum'}
    df_kpi_binned = df_kpi_values.pivot_table(index=timebin, columns='kpiName', values=['value', 'answers'],
                                              aggfunc=aggregator)

    # Swap column levels so kpi name is on top of aggregation
    df_kpi_binned = df_kpi_binned.swaplevel(0, 1, axis='columns').sort_index(axis='columns')
    # Rename aggregations
    df_kpi_binned.rename({'value': 'mean'}, axis='columns', level=1, inplace=True)
    # Round float values
    df_kpi_binned = np.round(df_kpi_binned, 2)

    if mean_only:
        df_kpi_binned = df_kpi_binned.iloc[:, df_kpi_binned.columns.get_level_values(1) == 'mean']
        df_kpi_binned.columns = df_kpi_binned.columns.droplevel(1)

    # Merge column levels
    # df_kpi_binned.columns = ["_".join(x) for x in df_kpi_binned.columns.ravel()]

    return df_kpi_binned


def get_participation_timelines(df_surveys: pd.DataFrame, org_node: pd.Series) -> pd.DataFrame:
    """
    Returns a dataframe containing participation timeline data for a given org node.
    """
    if df_surveys.empty:
        return pd.DataFrame()

    date_max = df_surveys['dateStart'].max()
    date_start = df_surveys['dateStart'].min()

    participation: List[dict] = []

    df_surveys_node = filter_by_org_node(df_surveys, org_node)
    period_end = date_start
    while period_end <= date_max:
        period_start = period_end - timedelta(days=cfg.stats.period_days)
        df_surveys_period = df_surveys_node.loc[
            (df_surveys_node['dateStart'] >= period_start) & (df_surveys_node['dateStart'] <= period_end)]
        df_surveys_period_mail = df_surveys_period.loc[df_surveys_period['mobileConnectionCount'] == 0]
        df_surveys_period_mobile = df_surveys_period.loc[df_surveys_period['mobileConnectionCount'] > 0]
        row = {
            'period_start': period_start,
            'period_end': period_end,
            'surveyCount': len(df_surveys_period.index),
            'completeCount': df_surveys_period['isComplete'].sum(),
            'percentComplete': round(df_surveys_period['isComplete'].mean() * 100, 2),
            'surveyCountByMail': len(df_surveys_period_mail.index),
            'completeCountByMail': df_surveys_period_mail['isComplete'].sum(),
            'percentCompleteByMail': round(df_surveys_period_mail['isComplete'].mean() * 100, 2),
            'surveyCountByMobile': len(df_surveys_period_mobile.index),
            'completeCountByMobile': df_surveys_period_mobile['isComplete'].sum(),
            'percentCompleteByMobile': round(df_surveys_period_mobile['isComplete'].mean() * 100, 2),
        }

        participation.append(row)

        period_end += timedelta(days=cfg.stats.step_days)

    return pd.DataFrame(participation).set_index('period_end')


def get_node_participation(df_surveys: pd.DataFrame, org_nodes: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a dataframe with participation info per org node.
    """
    df_node_participation = org_nodes[['label', 'level', 'left', 'right', 'users']]
    df_node_participation = df_node_participation.assign(users_count=0, surveys_complete=0, surveys_incomplete=0,
                                                         percent_complete=0)

    for node_id, node in df_node_participation.iterrows():
        df_surveys_org = df_surveys.loc[
            (df_surveys['orgNodeLeft'] >= node['left']) & (df_surveys['orgNodeRight'] <= node['right'])]

        surveys_count = len(df_surveys_org.index)
        surveys_complete = int(df_surveys_org['isComplete'].sum())
        surveys_incomplete = int(surveys_count - surveys_complete)

        df_node_participation.at[node_id, 'users_count'] = node['users']
        df_node_participation.at[node_id, 'surveys_complete'] = surveys_complete
        df_node_participation.at[node_id, 'surveys_incomplete'] = surveys_incomplete
        df_node_participation.at[node_id, 'percent_complete'] = round(
            surveys_complete / surveys_count * 100) if surveys_count > 0 else None

        # Convert all floats to int, works only for columns without NaN though
    # df_node_participation = df_node_participation.apply(pd.to_numeric, errors='ignore', downcast='integer')
    df_node_participation = df_node_participation.drop(['left', 'right', 'users'], axis='columns')

    return df_node_participation


def get_kpi_timeline(df_node: pd.DataFrame, df_benchmarks: pd.DataFrame, kpi: pd.Series) -> pd.DataFrame:
    """
    Returns a kpi timeline dataframe containing moving average statistics.
    """
    if df_node.empty:
        return pd.DataFrame()

    timeline: List[dict] = []
    period_interval = timedelta(days=cfg.stats.period_days)
    date_max = df_node.index.max()
    date_start = df_node.index.min()

    benchmark = df_benchmarks.loc[kpi['name']]
    min_answers = cfg.stats.min_answers

    # Date at the end of the shifitng time period and moved to previous monday
    date = date_start - timedelta(days=date_start.weekday())
    df_node_kpi = df_node.loc[df_node['kpiName'] == kpi['name']]
    while date <= date_max:
        period_mask = (df_node_kpi.index >= date - period_interval) & (df_node_kpi.index <= date)
        df_period = df_node_kpi.loc[period_mask]
        values = df_period['value']
        n = len(values.index)
        n_answers = df_period['answers'].sum()
        mean = values.mean() if n >= min_answers else NaN

        _, p_value = ttest_1samp(values, benchmark['mean']) if n >= min_answers else (NaN, NaN)

        timeline.append({
            'date': date,
            'n': n,
            'answers': n_answers,
            'mean': round(mean, 2) if n >= min_answers else NaN,
            'std': round(values.std(), 2) if n >= min_answers else NaN,
            'z_score': round((mean - benchmark['mean']) / benchmark['std'], 2) if n >= min_answers else NaN,
            'bm_z_score': 0,
            'p_value': round(p_value, 5) if n >= min_answers else NaN,
        })

        date += timedelta(days=cfg.stats.step_days)

    return pd.DataFrame(timeline).set_index('date')
