# coding=utf-8

from flask import render_template


def get_main_page():
    return render_template('index.html')
