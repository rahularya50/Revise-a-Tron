# coding=utf-8
import os
import sqlite3
from flask import Flask, g, render_template, request

app = Flask(__name__)
app.config.from_object(__name__)


DISPLAY_COLS = ["Paper", "Year", "Month", "Topics", "Person"]
HIDDEN_COLS = ["Question_link", "Answer_link"]


# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def main():
    return render_template('layout.html', cols=DISPLAY_COLS, hiddens=HIDDEN_COLS)


@app.route('/table_gen')
def gen_tables():
    db = get_db()

    where_clause = ''
    args = []
    for col in DISPLAY_COLS:
        if col in request.args:
            if args:
                where_clause += " AND ("
            else:
                where_clause += " WHERE ("

            for arg in request.args.getlist(col):
                where_clause += "{}=? OR ".format(col)
                args.append(arg)

                where_clause = where_clause[:-4]
                where_clause += ")"

    sql = 'SELECT ' + ", ".join(DISPLAY_COLS) + ' FROM entries'
    cur = db.execute(sql + where_clause, args)
    display_entries = cur.fetchall()

    sql = 'SELECT ' + ", ".join(HIDDEN_COLS) + ' FROM entries'
    cur = db.execute(sql + where_clause, args)
    hidden_entries = cur.fetchall()

    uniques = {}
    for col in DISPLAY_COLS:
        cur = db.execute('SELECT DISTINCT ' + col + ' FROM entries')
        uniques[col] = list(i[0] for i in cur.fetchall())
    return render_template('table.html',
                           cols=DISPLAY_COLS,
                           hiddens=HIDDEN_COLS,
                           entries=display_entries,
                           hidden_entries=hidden_entries,
                           uniques=uniques)


if __name__ == '__main__':
    app.run(use_reloader=True)
