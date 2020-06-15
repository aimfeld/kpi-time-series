# ----------------------------------------------------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------------------------------------------------

from ligado import aggregator, config as cfg
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns  # pip install seaborn

def plot_answers_surveys(df_kpi_node: pd.DataFrame, org_node: pd.Series, kpis: pd.DataFrame):
    df_kpi_pivot = aggregator.get_kpi_values_pivot(df_kpi_node)
    # Assume all KPIs use the same likert scale
    likert_min = kpis['min'].iloc[0]
    likert_max = kpis['max'].iloc[0]
    bins = np.arange(likert_min, likert_max + 2) - 0.5
    df_kpi_pivot[kpis.index].plot(kind='hist', subplots=True, bins=bins, figsize=(8, len(kpis.index) * 1.2))
    plt.suptitle('{}: distribution of KPI values aggregated within surveys'.format(org_node.label))
    plt.xticks(range(likert_min, likert_max + 1))
    plt.show()


def plot_violin_answers_surveys(df_kpi_node: pd.DataFrame, org_node: pd.Series, kpis: pd.DataFrame):
    df_kpi_pivot = aggregator.get_kpi_values_pivot(df_kpi_node)
    _, ax = plt.subplots(figsize=(8, len(kpis.index) * 1.2))
    sns.violinplot(data=df_kpi_pivot[kpis.index], ax=ax, orient='h')
    plt.suptitle('{}: distribution of KPI values aggregated within surveys'.format(org_node.label))
    plt.show()


def plot_participation_completed_surveys(df_participants: pd.DataFrame, org_node: pd.Series):
    min_complete_surveys = int(df_participants['completeSurveys'].min())
    max_complete_surveys = int(df_participants['completeSurveys'].max())
    df_participants.hist(column='completeSurveys', bins=np.arange(min_complete_surveys, max_complete_surveys + 1),
                         align='left')
    plt.xticks(range(min_complete_surveys, max_complete_surveys + 1))
    plt.title('{}: completed surveys distribution'.format(org_node.label))
    plt.xlabel('Number of completed surveys')
    plt.ylabel('n')
    plt.show()


def plot_participation_completed_surveys_percent(df_participants: pd.DataFrame, org_node: pd.Series):
    df_participants.hist(column='completePercent', bins=range(-5, 105 + 1, 10))
    plt.title('{}: participation rate distribution'.format(org_node.label))
    plt.xticks(range(0, 110, 10))
    plt.xlabel('Percent completed surveys')
    plt.ylabel('n')
    plt.show()


def plot_participation_by_device(df_participation: pd.DataFrame, df_users: pd.DataFrame, org_node: pd.Series):
    users_count = len(df_users.index)
    mail_users_count = (df_users['mobileConnectionCount'] == 0).sum()
    mobile_users_count = (df_users['mobileConnectionCount'] > 0).sum()
    ax = df_participation.plot.line(y=['percentComplete', 'percentCompleteByMail', 'percentCompleteByMobile'],
                                    figsize=(12, 6))
    plt.title('{}: participation'.format(org_node.label))
    plt.ylabel('participation %')
    plt.xlabel('')
    plt.legend(['Overall: {} users'.format(users_count), 'E-Mail: {} users'.format(mail_users_count),
                'Mobile: {} users'.format(mobile_users_count)])
    ax.yaxis.grid(which="major", color='grey', linestyle='-')
    plt.show()

    # plt.savefig('output/participation.png')


def plot_participation_by_node(df_surveys: pd.DataFrame, org_nodes: pd.DataFrame, root_node: pd.Series):
    _, ax = plt.subplots(figsize=(12, 6))
    for node_id, node in org_nodes.iterrows():
        df_plot = aggregator.get_participation_timelines(df_surveys, node)
        linewidth = 3 if node_id == root_node.nodeID else 1
        df_plot.plot(kind='line', y='percentComplete', label=node.label, ax=ax, linewidth=linewidth)

    plt.title('Participation by unit over time')
    plt.ylabel('participation %')
    plt.xlabel('')
    plt.show()


# def plot_kpi_timelines(node: pd.Series, df_kpi_timeline: pd.DataFrame, kpi: pd.Series):
#     effect_map = {
#         'large neg. effect': {'min': -1000, 'max': -cfg.threshold.z_large, 'color': (0.7, 0, 0, 0.5), 'mark': True},
#         'medium neg. effect': {'min': -cfg.threshold.z_large, 'max': -cfg.threshold.z_medium, 'color': (1, 0.8, 0, 0.4), 'mark': True},
#         'small neg. effect': {'min': -cfg.threshold.z_medium, 'max': -cfg.threshold.z_small, 'color': (1, 0.8, 0, 0.2), 'mark': True},
#         'no effect': {'min': -cfg.threshold.z_small, 'max': cfg.threshold.z_small, 'color': (1, 1, 1, 1), 'mark': False},
#         'small pos. effect': {'min': cfg.threshold.z_small, 'max': cfg.threshold.z_medium, 'color': (0, 0.7, 0, 0.1), 'mark': True},
#         'medium pos. effect': {'min': cfg.threshold.z_medium, 'max': cfg.threshold.z_large, 'color': (0, 0.7, 0, 0.4), 'mark': True},
#         'large pos. effect': {'min': cfg.threshold.z_large, 'max': 1000, 'color': (0, 0.7, 0, 0.7), 'mark': True},
#     }
#
#     def mark_significant_effects(ax, df_plot: pd.DataFrame, kpi: pd.Series):
#         # noinspection PyUnresolvedReferences
#         trans = mpl.transforms.blended_transform_factory(ax.transData, ax.transAxes)
#         ylim = ax.get_ylim()
#         significant_mask = df_plot['p_value'] < cfg.threshold.p_value
#         z_score = df_plot['z_score'] * kpi.polarity
#
#         for effect in effect_map.values():
#             if effect['mark']:
#                 effect_mask = (z_score >= effect['min']) & (z_score < effect['max'])
#                 # ax.axvspan( i, i+.2, facecolor='0.2', alpha=0.5)
#                 ax.fill_between(df_plot.index, 0, 1, where=(significant_mask & effect_mask),
#                                 facecolor=effect['color'], interpolate=True, transform=trans)
#
#         ax.set_ylim(ylim)  # Workaround, y-range is changed sometimes by fill_between
#
#     def draw_datapoints(ax, df_plot, kpi: pd.Series):
#         df_datapoints = df_plot[df_plot['n'] >= cfg.stats.min_answers]
#         colors = pd.Series(
#             ['green' if z > cfg.threshold.z_yellow else 'gold' if z > cfg.threshold.z_red else 'red' for z in
#              df_datapoints['z_score'] * kpi.polarity],
#             df_datapoints.index)
#
#         ax.scatter(df_datapoints.index, df_datapoints['z_score'], 20, color=colors, zorder=2)
#
#     def effect_color_bar(ax):
#         effect_colors = [effect['color'] for label, effect in effect_map.items()]
#         n_colors = len(effect_colors)
#         ticks = np.linspace(1 / (n_colors * 2), 1 - 1 / (n_colors * 2), n_colors)
#         # noinspection PyUnresolvedReferences
#         cmap = mpl.colors.ListedColormap(effect_colors)
#         # noinspection PyUnresolvedReferences
#         cbar = mpl.colorbar.ColorbarBase(ax, cmap=cmap, ticks=ticks, )
#         cbar.ax.set_yticklabels([label for label, effect in effect_map.items()])
#         # cbar.ax.set_title('Significant effects', horizontalalignment='left')
#         cbar.ax.text(0, 1.025, 'Significant effects',
#                      fontsize='large')  # Manually position title, set_title does a bad job
#
#     if len(df_kpi_timeline.index) <= 1 or \
#             len(df_kpi_timeline[df_kpi_timeline['n'] >= cfg.stats.min_answers].index) < cfg.stats.min_datapoints:
#         print('\n{} (n={}): {}: No plot because fewer than {} datapoints with least {} answers.'.format(
#             node.label, node.users, kpi.label, cfg.stats.min_datapoints, cfg.stats.min_answers
#         ))
#         return
#
#     fig, (ax_mean, ax_colorbar) = plt.subplots(figsize=(12, 4), ncols=2, gridspec_kw={'width_ratios': [30, 1]})
#
#     title = '\n{} (n={}): {}'.format(node.label, node.users, kpi.label)
#     # print(title)
#
#     df_kpi_timeline.plot(kind='line', y=['z_score', 'bm_z_score'], style=['-', '--'],
#                    color=['grey', 'grey'], ax=ax_mean, zorder=1)
#
#     ax_mean.set_title(title)
#     ax_mean.legend(['{}-day period'.format(cfg.stats.period_days), 'benchmark'], loc='upper right')
#     ax_mean.set_ylabel('z-score')
#     ax_mean.xaxis.label.set_visible(False)
#     ax_mean.grid(True, axis='x', linestyle=':')
#     ax_mean.tick_params(axis='x', which='minor', bottom=False)
#
#     draw_datapoints(ax_mean, df_kpi_timeline, kpi)
#     mark_significant_effects(ax_mean, df_kpi_timeline, kpi)
#     effect_color_bar(ax_colorbar)
#     ax_mean.set_ylim(top=1.2, bottom=-1.2)
#
#     plt.show()


def plot_org_node_kpi_timelines(df_kpi_values: pd.DataFrame, df_benchmarks: pd.DataFrame,
                                org_nodes: pd.DataFrame, root_node: pd.Series, kpi: pd.Series):

    _, ax = plt.subplots(figsize=(16, 6))
    for node_id, node in org_nodes.iterrows():
        df_node = aggregator.filter_by_org_node(df_kpi_values, node)
        df_kpi_timeline = aggregator.get_kpi_timeline(df_node, df_benchmarks, kpi)

        linewidth = 3 if node_id == root_node.nodeID else 1
        df_kpi_timeline.plot(kind='line', y='z_score', label=node.label, ax=ax, linewidth=linewidth)

    # Mark traffic light areas
    ax.axhspan(cfg.threshold.z_yellow * kpi.polarity, cfg.threshold.z_red * kpi.polarity, color=(1, 0.8, 0, 0.2))
    ax.axhspan(cfg.threshold.z_red * kpi.polarity, cfg.threshold.z_limit * -1 * kpi.polarity, color=(0.7, 0, 0, 0.3))

    # Legend outside: https://stackoverflow.com/a/4701285
    # Shrink current axis's height by 10% on the bottom
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.2, box.width, box.height * 0.8])
    # Put a legend below current axis
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.20), ncol=3)

    title = kpi.label
    plt.title(title)
    plt.ylabel('z-score')
    plt.xlabel('')
    ax.set_ylim(top=cfg.threshold.z_limit, bottom=-cfg.threshold.z_limit)

    plt.show()


def plot_answer_timelines(node: pd.Series, df_node: pd.DataFrame,
                          df_benchmarks: pd.DataFrame, kpis: pd.DataFrame):
    _, ax = plt.subplots(figsize=(12, 6))
    for _, kpi in kpis.iterrows():
        df_kpi_timeline = aggregator.get_kpi_timeline(df_node, df_benchmarks, kpi)
        df_kpi_timeline.plot(kind='line', y='answers', label=kpi.label, ax=ax)

    title = '\n{} (n={}): Answers over time'.format(node.label, node.users)
    # print(title)
    plt.title(title)
    plt.ylabel('answers')
    plt.xlabel('')
    plt.legend(title='KPI')
    plt.show()

    # plt.savefig('output/answers-{}.png'.format(node.label))
