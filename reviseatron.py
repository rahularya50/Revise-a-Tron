# coding=utf-8
import json
import os
import sqlite3
import uuid
from collections import defaultdict

from flask import Flask, g, render_template, request, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(__name__)

DISPLAY_COLS = ["Paper", "Year", "Month", "Question_num", "Person"]
LINKED_COLS = {"Topics": "topics_table"}
HIDDEN_COLS = ["Question_link", "Answer_link"]

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_PATH = './static/user_imgs/'
UPLOAD_FOLDER = os.path.join(APP_ROOT, LOCAL_PATH)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    UPLOAD_FOLDER=UPLOAD_FOLDER
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
    g.sqlite_db.execute("PRAGMA foreign_keys = ON")
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def main():
    db = get_db()

    uniques = {}
    for col in DISPLAY_COLS:
        cur = db.execute('SELECT DISTINCT ' + col + ' FROM entries')
        uniques[col] = list(i[0] for i in cur.fetchall())

    for col in LINKED_COLS:
        cur = db.execute('SELECT DISTINCT value FROM {0}'.format(LINKED_COLS[col]))
        uniques[col] = list(i[0] for i in cur.fetchall())

    return render_template('layout.html', cols=DISPLAY_COLS, hiddens=HIDDEN_COLS, uniques=uniques, linked=LINKED_COLS)


@app.route('/table_gen')
def gen_tables():
    db = get_db()

    sql = 'SELECT ROWID FROM entries'
    cur = db.execute(sql)
    ids = set(cur.fetchall())

    for col in LINKED_COLS:
        if col in request.args:
            where_clause = ' WHERE ('
            args = []
            for arg in request.args.getlist(col):
                where_clause += "value=? OR "
                args.append(arg)
            where_clause = where_clause[:-4] + ")"
            sql = 'SELECT id FROM {0}'.format(LINKED_COLS[col])
            cur = db.execute(sql + where_clause + " ORDER BY ROWID", args)
            if ids is None:
                ids = set(cur.fetchall())
            else:
                ids &= set(cur.fetchall())

    ids_clause = " AND ("
    id_args = []
    for id in ids:
        ids_clause += "id = ? OR "
        id_args.append(id)
    ids_clause = ids_clause[:-4] + ")"

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

            where_clause = where_clause[:-4] + ")"

    sql = 'SELECT {0} FROM entries'.format(", ".join(DISPLAY_COLS))
    print(sql + where_clause + ids_clause)
    cur = db.execute(sql + where_clause + ids_clause + " ORDER BY ROWID", args + id_args)
    display_entries = cur.fetchall()

    sql = 'SELECT {0} FROM entries'.format(", ".join(HIDDEN_COLS))
    cur = db.execute(sql + where_clause + ids_clause + " ORDER BY ROWID", args + id_args)
    hidden_entries = cur.fetchall()

    sql = 'SELECT ROWID FROM entries'
    cur = db.execute(sql + where_clause + ids_clause + " ORDER BY ROWID", args + id_args)
    rowids = cur.fetchall()

    linked_entries = []
    for _ in rowids:
        linked_entries.append({})

    for i, col in enumerate(LINKED_COLS):
        for j, id in enumerate(rowids):
            sql = 'SELECT value FROM {0} WHERE id={1} ORDER BY ROWID'.format(LINKED_COLS[col], id[0])
            print(sql)
            cur = db.execute(sql)
            linked_entries[j][col] = [x[0] for x in cur.fetchall()]

    uniques = {}
    for col in DISPLAY_COLS:
        cur = db.execute('SELECT DISTINCT ' + col + ' FROM entries')
        uniques[col] = list(i[0] for i in cur.fetchall())
    for col in LINKED_COLS:
        cur = db.execute('SELECT DISTINCT value FROM {0}'.format(LINKED_COLS[col]))
        uniques[col] = list(i[0] for i in cur.fetchall())

    return render_template('table.html',
                           cols=DISPLAY_COLS,
                           hiddens=HIDDEN_COLS,
                           linked=[*LINKED_COLS.keys()],
                           entries=display_entries,
                           hidden_entries=hidden_entries,
                           linked_entries=linked_entries,
                           uniques=uniques,
                           rowids=rowids,
                           jsonify=json.dumps)


@app.route('/receiver', methods=["GET", "POST"])
def receiver():
    if request.method == "POST":
        data = []
        if 'rowid' not in request.form:
            return ''
        rowid = request.form['rowid']

        changed_cols = []
        for col in DISPLAY_COLS:
            changed_cols.append(col)
            data.append(request.form[col])
        for target_name in HIDDEN_COLS:
            x = save_file(target_name)
            if x:
                changed_cols.append(target_name)
                data.append(x)

        if rowid != '-1':
            sql = "UPDATE entries SET {0} = ? WHERE ROWID = ?".format(" = ?, ".join(changed_cols))
            data.append(rowid)
        else:
            sql = "INSERT INTO entries ({0}) VALUES ({1})".format(", ".join(changed_cols),
                                                                  ", ".join("?" * len(changed_cols)))

        print(sql)
        print(data)
        db = get_db()

        try:
            lastrowid = db.execute(sql, data).lastrowid
        except sqlite3.Error as er:
            return "fail"

        lastrowid = lastrowid if lastrowid else rowid

        try:
            for col in LINKED_COLS:
                print(col)
                sql = "DELETE FROM {0} WHERE id = ?".format(LINKED_COLS[col])
                print(sql)
                db.execute(sql, [lastrowid])
                to_add = request.form.get(col).split(",")  # TODO: Implement list decomposition properly!
                for elem in to_add:
                    sql = "INSERT INTO {0} (id, value) VALUES (?, ?)".format(LINKED_COLS[col])
                    print(sql)
                    db.execute(sql, [lastrowid, elem])
            db.commit()
        except sqlite3.Error as er:
            return "fail"

        return str(lastrowid)

    return "fail"


@app.route('/delete_entry')
def delete_entry():
    if 'rowid' not in request.args:
        return False
    rowid = request.args["rowid"]

    db = get_db()
    db.execute("DELETE FROM entries WHERE ROWID = ?", [rowid])
    db.commit()

    return "Deleted {}".format(rowid)


def save_file(target_name):
    if target_name not in request.files:
        return False
    file = request.files[target_name]
    if file and allowed_file(file.filename):
        local_path = secure_filename(file.filename)+str(uuid.uuid4())+"."+get_extension(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, local_path))
        return LOCAL_PATH + local_path
    return ""


def allowed_file(filename):
    return '.' in filename and \
           get_extension(filename) in ALLOWED_EXTENSIONS


def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()


if __name__ == '__main__':
    app.run(use_reloader=True)
