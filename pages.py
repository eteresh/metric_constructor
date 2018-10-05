# coding=utf-8

from flask import render_template, request
from clickhouse_driver import Client

client = Client('localhost')


def get_main_page():
    query = """
        SELECT action, COUNT(DISTINCT uid) AS users, ROUND(AVG(user_actions), 4) AS actions_per_user, SUM(user_actions) AS actions
        FROM (
            SELECT action, uid, SUM(1.0) AS user_actions
            FROM actions
            GROUP BY action, uid
        ) AS t
        GROUP BY action;
    """

    if 'actions' in request.args:
        action_names = request.args['actions'].split(',')
    actions = client.execute(query)
    keys = ['name', 'users', 'actions_per_user', 'actions']
    actions = [{k: v  for k, v in zip(keys, action)} for action in actions]
    return render_template('index.html', actions=actions)
