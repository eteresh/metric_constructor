#!/usr/bin/env python
# coding=utf-8


from application import app
from routes import init_routes

if __name__ == '__main__':
    init_routes(app)
    app.run(debug=True, host='0.0.0.0')
