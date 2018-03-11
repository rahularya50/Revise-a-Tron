# coding=utf-8
import os
import sqlite3
import uuid

from flask import Flask, g, render_template, request, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(__name__)

DISPLAY_COLS = ["Paper", "Year", "Month", "Person"]
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

    sql = 'SELECT {0} FROM entries'.format(", ".join(DISPLAY_COLS))
    cur = db.execute(sql + where_clause + " ORDER BY ROWID", args)
    display_entries = cur.fetchall()

    sql = 'SELECT {0} FROM entries'.format(", ".join(HIDDEN_COLS))
    cur = db.execute("{0}{1} ORDER BY ROWID".format(sql, where_clause), args)
    hidden_entries = cur.fetchall()

    sql = 'SELECT ROWID FROM entries'
    cur = db.execute(sql + where_clause + " ORDER BY ROWID", args)
    rowids = cur.fetchall()

    uniques = {}
    for col in DISPLAY_COLS:
        cur = db.execute('SELECT DISTINCT ' + col + ' FROM entries')
        uniques[col] = list(i[0] for i in cur.fetchall())
    return render_template('table.html',
                           cols=DISPLAY_COLS,
                           hiddens=HIDDEN_COLS,
                           entries=display_entries,
                           hidden_entries=hidden_entries,
                           uniques=uniques,
                           rowids=rowids)


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
                to_add = request.form.get(col).split(",")  # TODO: WAT
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
