
from ligado.constants import *
from ligado import config as cfg
import os
import mysql.connector as sql  # conda install -c anaconda mysql-connector-python
import numpy as np
import pandas as pd
from dotenv import load_dotenv  # conda install -c conda-forge python-dotenv
from sshtunnel import SSHTunnelForwarder  # conda install -c conda-forge sshtunnel
from pathlib import Path

def _get_db_connection():
    load_dotenv(Path('.') / '.env')
    if cfg.data.source == DataSource.REMOTE_DB:
        tunnel = SSHTunnelForwarder(
            (os.getenv('REM_SSH_HOST'), int(os.getenv('REM_SSH_PORT'))),
            ssh_username=os.getenv('REM_SSH_USERNAME'),
            ssh_pkey=os.getenv('REM_SSH_PKEY'),
            remote_bind_address=(os.getenv('REM_BIND_HOST'), int(os.getenv('REM_BIND_PORT')))
        )
        tunnel.start()
        return sql.connect(host=os.getenv('REM_DB_HOST'), port=tunnel.local_bind_port,
                           database=os.getenv('REM_DB_NAME'), user=os.getenv('REM_DB_USERNAME'))

    else:
        return sql.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('DB_NAME'),
                           user=os.getenv('DB_USERNAME'), password=os.getenv('DB_PASSWORD'))


def get_df_kpis() -> pd.DataFrame:
    if cfg.data.source != DataSource.CSV:
        query = """
            SELECT i.itemsetID AS kpiID, i.exportName AS name, t.sourceText AS label
            FROM survey_itemsets AS i
            LEFT JOIN texts AS t ON i.labelTextID = t.textID
            WHERE i.labelTextID IS NOT NULL AND i.exportName IS NOT NULL"""
        db_connection = _get_db_connection()
        df_kpis = pd.read_sql(query, db_connection)
        db_connection.close()
        df_kpis.to_csv('output/import-kpis.csv', sep='\t', encoding='utf-8', index=False)
    else:
        df_kpis = pd.read_csv('data/import-kpis.csv', delimiter='\t')

    # Easier for plotting and joining dataframes to use name as index instead of kpiID
    df_kpis.set_index('name', drop=False, inplace=True)

    # Set KPI range and polarities
    df_kpis.loc[:, 'min'] = cfg.kpi.likert_min
    df_kpis.loc[:, 'max'] = cfg.kpi.likert_max
    df_kpis.loc[:, 'polarity'] = 1
    df_kpis.loc[cfg.kpi.neg_polarity, 'polarity'] = -1

    return df_kpis


def get_df_kpi_values() -> pd.DataFrame:
    if cfg.data.source != DataSource.CSV:
        query = """
            SELECT im.meanID, im.userSurveyID, im.`value`, im.itemValueCount AS answers,
                   DATE(us.dateStart) AS dateStart, DATE(us.dateCompleted) AS dateCompleted,
                   i.itemsetID, i.exportName AS kpiName,
                   u.isDeleted, u.sex, us.birthDate, us.entryDate, 
                   YEAR(us.dateStart) - YEAR(us.birthDate) AS age,
                   YEAR(us.dateStart) - YEAR(us.entryDate) AS employment,
                   o.nodeID AS orgNodeID, o.label AS orgNodeLabel, o.shortLabel AS orgNodeShortLabel,
                   o.left AS orgNodeLeft, o.right AS orgNodeRight, o.`level` AS orgNodeLevel
            FROM itemset_means AS im
            LEFT JOIN user_surveys AS us USING (userSurveyID)
            LEFT JOIN users AS u USING (userID)
            LEFT JOIN survey_itemsets AS i USING (itemsetID)
            LEFT JOIN org_nodes AS o ON us.orgNodeID = o.nodeID
            WHERE u.roleID = 2 AND us.surveyID = {}""".format(cfg.data.ligado_survey_id)
        db_connection = _get_db_connection()
        df_kpi_values = pd.read_sql(query, db_connection, parse_dates=['dateStart', 'dateCompleted'],
                                    index_col='dateCompleted')
        db_connection.close()
        df_kpi_values.to_csv('output/import-kpi-values.csv', sep='\t', encoding='utf-8')
    else:
        df_kpi_values = pd.read_csv('data/import-kpi-values.csv', delimiter='\t',
                                    parse_dates=['dateStart', 'dateCompleted'], index_col='dateCompleted')

    return df_kpi_values


def get_df_org_nodes() -> pd.DataFrame:
    if cfg.data.source != DataSource.CSV:
        query = """
            SELECT o.*, COUNT(sub.userID) AS users, SUM(IF(sub.isActive = 1, 1, 0)) AS activeUsers FROM org_nodes AS o
            LEFT JOIN (
                SELECT sub_u.userID, sub_u.isActive, sub_o.nodeID, sub_o.`left`, sub_o.`right` FROM users AS sub_u
                LEFT JOIN org_nodes AS sub_o ON sub_u.orgNodeID = sub_o.nodeID
            ) AS sub ON sub.`left` >= o.`left` AND sub.`right` <= o.`right`
            GROUP BY o.nodeID
            ORDER BY o.`level`, o.parentNodeID, o.nodeID """
        db_connection = _get_db_connection()
        df_org_nodes = pd.read_sql(query, db_connection, coerce_float=False)
        db_connection.close()
        df_org_nodes.to_csv('output/import-org-nodes.csv', sep='\t', encoding='utf-8', index=False)
    else:
        df_org_nodes = pd.read_csv('data/import-org-nodes.csv', delimiter='\t')

    df_org_nodes.set_index('nodeID', drop=False, inplace=True)

    return df_org_nodes


def get_df_participants() -> pd.DataFrame:
    if cfg.data.source != DataSource.CSV:
        query = """
            SELECT u.importKey, u.isDeleted, 
                SUM(us.dateCompleted IS NOT NULL) AS completeSurveys,
                SUM(us.dateCompleted IS NULL) AS incompleteSurveys
            FROM users AS u
            LEFT JOIN user_surveys AS us ON u.userID = us.userID
            WHERE u.roleID = 2 AND us.surveyID = {}
            GROUP BY u.userID""".format(cfg.data.ligado_survey_id)
        db_connection = _get_db_connection()
        df_participants = pd.read_sql(query, db_connection, index_col='importKey')
        db_connection.close()
        df_participants.to_csv('output/import-participation.csv', sep='\t', encoding='utf-8')
    else:
        df_participants = pd.read_csv('data/import-participation.csv', delimiter='\t', index_col='importKey')

    df_participants['completePercent'] = np.round(
        df_participants.completeSurveys / (df_participants.completeSurveys + df_participants.incompleteSurveys) * 100
    )
    return df_participants


def get_df_surveys() -> pd.DataFrame:
    if cfg.data.source != DataSource.CSV:
        query = """
            SELECT us.userSurveyID, u.userID, u.isDeleted AS userIsDeleted,
                DATE(us.dateStart) AS dateStart, DATE(us.dateCompleted) AS dateCompleted, 
                us.dateCompleted IS NOT NULL AS isComplete, 
                COUNT(DISTINCT (CASE WHEN mc.isEnabled = 1 AND mc.identifier != '' THEN mc.userID END)) 
                AS mobileConnectionCount,
                u.orgNodeID, o.left AS orgNodeLeft, o.right AS orgNodeRight
            FROM user_surveys AS us
            LEFT JOIN users AS u ON u.userID = us.userID
            LEFT JOIN org_nodes AS o ON u.orgNodeID = o.nodeID
            LEFT JOIN mobile_connections AS mc ON mc.userID = u.userID
            WHERE u.roleID = 2 AND us.surveyID = {}
            GROUP BY us.userSurveyID""".format(cfg.data.ligado_survey_id)
        db_connection = _get_db_connection()
        df_surveys = pd.read_sql(query, db_connection, index_col='userSurveyID',
                                 parse_dates=['dateStart', 'dateCompleted'])
        db_connection.close()
        df_surveys.to_csv('output/import-surveys.csv', sep='\t', encoding='utf-8')
    else:
        df_surveys = pd.read_csv('data/import-surveys.csv', delimiter='\t', index_col='userSurveyID',
                                 parse_dates=['dateStart', 'dateCompleted'])

    return df_surveys


def get_df_users() -> pd.DataFrame:
    if cfg.data.source != DataSource.CSV:
        query = """
            SELECT u.userID, u.isDeleted,
                   COUNT(DISTINCT (CASE WHEN mc.isEnabled = 1 AND mc.identifier != '' THEN mc.userID END)) 
                   AS mobileConnectionCount
            FROM users AS u
            LEFT JOIN mobile_connections AS mc ON mc.userID = u.userID
            WHERE u.roleID = 2
            GROUP BY u.userID"""
        db_connection = _get_db_connection()
        df_users = pd.read_sql(query, db_connection, index_col='userID')
        db_connection.close()
        df_users.to_csv('output/import-users.csv', sep='\t', encoding='utf-8')
    else:
        df_users = pd.read_csv('data/import-users.csv', delimiter='\t', index_col='userID')

    return df_users
