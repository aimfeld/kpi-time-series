# Config file, see https://stackoverflow.com/a/46720989/94289
# Properties without assigned value must be set in the project notebooks.
# Properties may be overwritten in the project notebooks.

from ligado.constants import DataSource
from typing import List
import pandas as pd

class paths:
    # E.g. 'erni-ligado', 'sbb-ligado'
    project_dir: str

class data:
    source: str = DataSource.REMOTE_DB

    # Survey ID of ligado survey, see project json file
    ligado_survey_id: int

class kpi:
    # Min value for likert answer
    likert_min: int

    # Max value for likert answer
    likert_max: int

    # List of KPI names with negative polarity
    neg_polarity: list

class nodes:
    # ID of the root org node
    root: int

    # List of org node IDs to analyze
    selected: List[int] = []

class stats:
    # Minimum number of answers required for aggregating a timeline datapoint
    min_answers = 8

    # Day interval between timeline datapoints
    step_days = 7

    # Minimum number of datapoints required for plotting a timeline
    min_datapoints = 3

    # Time window length in days for moving average
    period_days = 30

class threshold:
    # Mark p-values as significant if below
    p_value = 0.05

    # Lower boundaries of effect sizes, see https://www.statisticshowto.datasciencecentral.com/cohens-d/
    z_small = 0.2
    z_medium = 0.5
    z_large = 0.8

    # Z-score cutoffs for traffic light color (could be based on cohen's, no real difference)
    z_yellow = -0.5
    z_red = -0.8

    # Z-score y-axis range for timeline plots
    z_limit = 1.2

class alert:
    # Minimual number of consecutive critical datapoints for alert
    min_datapoints = 3

    # For adding links to the cockpit, e.g. 'https://sbb.ligado.ch'
    base_url: str

    # This config must match the FilterPlugins, see
    # https://github.com/cloud-solutions/ligado-shared/tree/master/src/Cockpit/FilterPlugin
    filters = pd.DataFrame([
        {'type': 'none', 'description': 'No filter'},
        {'type': 'nominal', 'plugin': 'SexFilter', 'category': 'm',
         'variable': 'sex', 'value': 'm', 'description': 'Sex: male'},
        {'type': 'nominal', 'plugin': 'SexFilter', 'category': 'f',
         'variable': 'sex', 'value': 'f', 'description': 'Sex: female'},
        {'type': 'range', 'plugin': 'AgeGroupFilter', 'category': 'group1',
         'variable': 'age', 'min': 0, 'max': 29, 'description': 'Age group: less than 30 years'},
        {'type': 'range', 'plugin': 'AgeGroupFilter', 'category': 'group2',
         'variable': 'age', 'min': 30, 'max': 49, 'description': 'Age group: 30 to 49 years'},
        {'type': 'range', 'plugin': 'AgeGroupFilter', 'category': 'group3',
         'variable': 'age', 'min': 50, 'max': 120, 'description': 'Age group: more than 50 years'},
        {'type': 'range', 'plugin': 'EmploymentDurationFilter', 'category': 'group1',
         'variable': 'employment', 'min': 0, 'max': 0, 'description': 'Employment duration: less than a year'},
        {'type': 'range', 'plugin': 'EmploymentDurationFilter', 'category': 'group2',
         'variable': 'employment', 'min': 1, 'max': 2, 'description': 'Employment duration: 1 to 3 years'},
        {'type': 'range', 'plugin': 'EmploymentDurationFilter', 'category': 'group3',
         'variable': 'employment', 'min': 3, 'max': 100, 'description': 'Employment duration: more than 3 years'},
    ])
