import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns  # pip install seaborn

def init_display():
    # Display more columns when printing dataframes
    # https://stackoverflow.com/questions/11707586/python-pandas-how-to-widen-output-display-to-see-more-columns
    pd.set_option('display.max_columns', 50)

    # https://stackoverflow.com/questions/27476642/matplotlib-get-rid-of-max-open-warning-output
    mpl.rcParams.update({'figure.max_open_warning': 0})

    # Make figure access visible with dark theme: https://stackoverflow.com/a/55436299
    plt.rcParams['figure.facecolor'] = 'white'

    # Set seaborn default style
    sns.set()
