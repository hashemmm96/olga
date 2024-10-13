import re
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.create_function("REGEXP", 2, regexp)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


def init_app(app):
    app.teardown_appcontext(close_db)
