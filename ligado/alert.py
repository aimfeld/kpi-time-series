# ----------------------------------------------------------------------------------------------------------------------
# Smart Alerts
# ----------------------------------------------------------------------------------------------------------------------

from ligado import config as cfg, aggregator
import numpy as np
import pandas as pd
from urllib.parse import quote
import json
from typing import List

def _get_df_kpi_filtered(df_kpi: pd.DataFrame, kpi_filter: pd.Series) -> pd.DataFrame:
    """
    Returns a filtered kpi dataframe
    """
    if kpi_filter.type == 'nominal':
        return df_kpi.loc[df_kpi[kpi_filter['variable']] == kpi_filter['value']]
    elif kpi_filter.type == 'range':
        return df_kpi.loc[(df_kpi[kpi_filter['variable']] >= kpi_filter['min']) &
                          (df_kpi[kpi_filter['variable']] <= kpi_filter['max'])]
    else:
        return df_kpi


def _add_alert(df_kpi_timeline: pd.DataFrame, alerts: List[dict], critical_dates: List[np.datetime64],
               kpi_filter: pd.Series, node: pd.Series, kpi: pd.Series):
    """
    Adds an alert to the list of alerts.
    """

    url_filters = {} if kpi_filter['type'] == 'none' else {
        'kpi-filters':  {
            kpi_filter['plugin']: {
                'split': '0',
                'selected': [kpi_filter['category']]
            }
        }
    }

    url = '{}/cockpit/index/orgNodeID/{}/kpiID/{}/filters/{}#kpiTimelines'.format(
        cfg.alert.base_url, node['nodeID'], kpi['kpiID'], quote(json.dumps(url_filters))
    )
    alerts.append({
        'start': critical_dates[0],
        'end': critical_dates[-1],
        'length': len(critical_dates),
        'mean_answers': np.round(df_kpi_timeline.loc[critical_dates]['n'].mean(), 1),
        'node_id': node['nodeID'],
        'node_label': node['label'],
        'kpi': kpi['label'],
        'filter': kpi_filter['description'],
        'url': url
    })

def _get_filter_alerts(df_kpi_timeline: pd.DataFrame, kpi_filter: pd.Series, node: pd.Series, kpi: pd.Series) -> List[dict]:
    """
    Loops through a filtered KPI timeline (df_kpi_timeline) and returns a list of alerts. Alerts are critical segments
    of the KPI timeline.
    """
    alerts: List[dict] = []
    if df_kpi_timeline.empty:
        return alerts
    # z_score is NaN if there are not enough answers
    critical = (df_kpi_timeline['z_score'] is not np.NaN) & \
               (df_kpi_timeline['z_score'] * kpi['polarity'] <= cfg.threshold.z_yellow) & \
               (df_kpi_timeline['p_value'] <= cfg.threshold.p_value)

    is_critical = False
    critical_dates: List[np.datetime64] = []
    for date, is_critical in critical.items():
        if is_critical:
            critical_dates.append(date)
        else:
            if len(critical_dates) >= cfg.alert.min_datapoints:
                _add_alert(df_kpi_timeline, alerts, critical_dates, kpi_filter, node, kpi)

            critical_dates = []

    # Add (unterminated) alert at the end if critical
    if is_critical and len(critical_dates) >= cfg.alert.min_datapoints:
        _add_alert(df_kpi_timeline, alerts, critical_dates, kpi_filter, node, kpi)

    return alerts


def get_alerts(df_kpi_values: pd.DataFrame, org_nodes: pd.DataFrame, kpis: pd.DataFrame,
               df_benchmarks: pd.DataFrame) -> pd.DataFrame:
    alerts: List[dict] = []

    for node_id, node in org_nodes.iterrows():
        for _, kpi in kpis.iterrows():
            for _, kpi_filter in cfg.alert.filters.iterrows():
                df_node = aggregator.filter_by_org_node(df_kpi_values, node)
                df_filtered = _get_df_kpi_filtered(df_node, kpi_filter)
                df_kpi_timeline = aggregator.get_kpi_timeline(df_filtered, df_benchmarks, kpi)

                alerts += _get_filter_alerts(df_kpi_timeline, kpi_filter, node, kpi)

    df_alerts = pd.DataFrame(alerts).set_index('start').sort_index()
    # df_alerts.to_excel('output/alerts.xlsx', index=False)
    df_alerts.to_csv('output/alerts.csv', sep='\t', encoding='utf-8')

    return df_alerts
