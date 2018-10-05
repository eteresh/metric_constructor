# coding=utf-8

from pages import get_main_page


def init_routes(app):
    app.add_url_rule('/', 'index', get_main_page)
    app.add_url_rule('/index', 'index', get_main_page)
