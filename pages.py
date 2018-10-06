# coding=utf-8

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from flask import render_template, request, jsonify
from clickhouse_driver import Client
from hashlib import sha256
from functools import partial
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AB_HASH_LENGTH = 15
client = Client('localhost')


matplotlib.rcParams['figure.figsize'] = (18, 12)
matplotlib.rcParams['figure.titlesize'] = 24
matplotlib.rcParams['font.size'] = 20
matplotlib.rcParams['legend.fontsize'] = 20
matplotlib.rcParams['axes.titlesize'] = 28
matplotlib.rcParams['axes.labelsize'] = 24
matplotlib.rcParams['xtick.labelsize'] = 17
matplotlib.rcParams['ytick.labelsize'] = 17


def get_main_page():
    start_date = request.args.get('start', '2018-01-01')
    end_date = request.args.get('end', '2018-12-31')

    query = """
        SELECT platform, COUNT(DISTINCT uid) AS users, COUNT(DISTINCT action) AS uniq_actions, COUNT(action) AS actions
        FROM actions
        WHERE dt BETWEEN '{}' AND '{}'
        GROUP BY platform;
    """.format(start_date, end_date)

    platforms = client.execute(query)
    keys = ['name', 'users', 'uniq_actions', 'actions']
    platforms = [{k: v  for k, v in zip(keys, item)} for item in platforms]

    query = """
        SELECT action, COUNT(DISTINCT uid) AS users, ROUND(AVG(user_actions), 2) AS actions_per_user, SUM(user_actions) AS actions
        FROM (
            SELECT action, uid, SUM(1.0) AS user_actions
            FROM actions
            WHERE dt BETWEEN '{}' AND '{}'
            GROUP BY action, uid
        ) AS t
        GROUP BY action
        ORDER BY actions DESC;
    """.format(start_date, end_date)

    actions = client.execute(query)
    keys = ['name', 'users', 'actions_per_user', 'actions']
    actions = [{k: v  for k, v in zip(keys, action)} for action in actions]
    return render_template('index.html', platforms=platforms, actions=actions)


def get_platforms():
    start_date = request.args.get('start', '2018-01-01')
    end_date = request.args.get('end', '2018-12-31')
    query = """
        SELECT platform, COUNT(DISTINCT uid) AS users, COUNT(DISTINCT action) AS uniq_actions, COUNT(action) AS actions
        FROM actions
        WHERE dt BETWEEN '{}' AND '{}'
        GROUP BY platform;
    """.format(start_date, end_date)
    print(query)
    platforms = client.execute(query)
    keys = ['name', 'users', 'uniq_actions', 'actions']
    platforms = [{k: v  for k, v in zip(keys, item)} for item in platforms]
    return jsonify(platforms)


def get_split(uid, salt, n_splits):
    uid_hash = sha256(str(uid) + salt).hexdigest()
    return int(uid_hash[:AB_HASH_LENGTH], base=16) % n_splits


def bootstrap(values, n_bootstrap_iterations=10 ** 4, aggregate='mean'):
    np.random.seed()
    results = []
    for _ in xrange(n_bootstrap_iterations):
        bootstrapped_values = np.random.choice(values, len(values), replace=True)
        results.append(getattr(np, aggregate)(bootstrapped_values))
    return np.array(results)


def partition_indices(total, part, nparts):
    if not (0 <= part < nparts):
        raise ValueError()
    part_size = total / nparts
    left = total % nparts
    lower = part_size * part + min(left, part)
    return lower, lower + part_size + (1 if part < left else 0)


def bootstrap_parallel(values, n_bootstrap_iterations=10**4, aggregate='mean', n_jobs=8):
    jobs = []
    for partition_index in xrange(n_jobs):
        start, end = partition_indices(n_bootstrap_iterations, partition_index, n_jobs)
        job_iterations = end - start
        jobs.append(delayed(bootstrap)(values, n_bootstrap_iterations=job_iterations, aggregate=aggregate))
    results = np.hstack(Parallel(n_jobs=n_jobs)(jobs))
    return results


def bootstrap_test(left_array, right_array, n_bootstrap_iterations=3*10**3, aggregate='mean', alpha=0.05):
    left_array_bootstrap = bootstrap_parallel(left_array, n_bootstrap_iterations, aggregate=aggregate)
    right_array_bootstrap = bootstrap_parallel(right_array, n_bootstrap_iterations, aggregate=aggregate)

    deltas = right_array_bootstrap - left_array_bootstrap
    left_percentile, right_percentile = np.percentile(deltas, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return deltas, left_percentile, right_percentile


def plot_results(delta, deltas, left_percentile, right_percentile):
    plt.hist(deltas, bins=100, normed=True)
    plt.axvline(0.0, color='k', linewidth=3, label=u'Ноль')
    plt.axvline(left_percentile, color='g', linewidth=3, label=u'Перцентили')
    plt.axvline(right_percentile, color='g', linewidth=3)

    plt.xlabel(u'Разность значений метрики между экспериментом и контролем')
    plt.ylabel(u'Кол-во испытаний бутстрэпа')
    plt.title(u'Распределение для разности метрики\nмежду экспериментальной и контрольной группой\n')
    plt.grid()
    plt.legend()
    plt.savefig('bootstrap_test.png')


def stat_test(data, control_splits, splits, aggregation):
    control_values = data.loc[data['split'].isin(control_splits), 'actions']
    control_group_users = len((data.loc[data['split'].isin(control_splits), 'uid']).unique())
    experiment_group_users = len((data.loc[data['split'].isin(splits), 'uid']).unique())
    values = data.loc[data['split'].isin(splits), 'actions']
    control_group_value = getattr(np, aggregation)(control_values)
    experiment_group_value = getattr(np, aggregation)(values)
    delta = experiment_group_value - control_group_value
    deltas, left_percentile, right_percentile = bootstrap_test(control_values, values, aggregate=aggregation)
    plot_results(delta, deltas, left_percentile, right_percentile)
    result = {'groups': [
        {'name': u'Контроль', u'users': control_group_users, 'value': control_group_value},
        {'name': u'Эксперимент', u'users': experiment_group_users, 'value': experiment_group_value},
        {'name': u'Разность', u'users': experiment_group_users - control_group_users, 'value': delta},
    ]}
    result['delta'] = delta
    result['left_percentile'] = left_percentile
    result['right_percentile'] = right_percentile
    result['deltas'] = deltas
    result['significant'] = not (left_percentile <= 0.0 <= right_percentile)
    result['success'] = result['significant'] and 0.0 < left_percentile
    return result


def get_result():
    start_date = request.args.get('start', None)
    end_date = request.args.get('end', None)
    platforms = request.args.get('platforms', None)
    if platforms:
        platforms = platforms.split(',')
    metric_type = request.args.get('metric_type', 'single')
    aggregation = request.args.get('agg', 'sum')
    actions = request.args.get('actions', None)
    if actions:
        actions = actions.split(',')
    salt = request.args['salt']
    control_splits = request.args['c'].split(',')
    splits = request.args['s'].split(',')
    n_splits =  int(request.args['splits'])
    filter = []
    if start_date is not None:
        filter.append("dt >= '{}'".format(start_date))
    if end_date is not None:
        filter.append("dt <= '{}'".format(end_date))
    print(platforms)
    if platforms:
        filter.append("platform IN ({})".format(', '.join(map(lambda item: "'{}'".format(item), platforms))))
    if actions:
        filter.append("action IN ({})".format(', '.join(map(lambda item: "'{}'".format(item), actions))))
    if filter:
        filter = 'WHERE ({})'.format(' AND '.join(filter))
    else:
        filter = ''
    query = """
        SELECT action, uid, SUM(1.0) AS actions
        FROM actions
        {}
        GROUP BY action, uid;
    """.format(filter)
    data = pd.DataFrame(client.execute(query), columns=['action', 'uid', 'actions'])
    data['split'] = data['uid'].apply(partial(get_split,  salt=salt, n_splits=n_splits))
    data = data.loc[data['split'].isin(set(map(int, control_splits + splits)))].reset_index(drop=True)
    actions = data['action'].unique()

    results = []
    for action in actions:
        result = stat_test(data.loc[data['action'] == action].reset_index(drop=True), control_splits, splits, aggregation)
        result['action'] = action
        results.append(result)
    return render_template('result.html', results=results, start_date=start_date, end_date=end_date, salt=salt, control_splits=', '.join(control_splits), splits=', '.join(splits), n_splits=n_splits, aggregation=aggregation)
