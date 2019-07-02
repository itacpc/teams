import sys
import random
import smtplib
import ssl
import string

import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm

from datetime import datetime, timedelta

from flask import flash, Flask, g, redirect, render_template, request, session, url_for
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config.from_pyfile('config.py')

bcrypt = Bcrypt(app)

MAX_MEMBERS = 3
GENERATED_SECRET_LENGTH = 30
RESET_PASSWORD_INTERVAL = timedelta(days=1)


class Database:
    SCHEMA = 'schema.sql'

    def __init__(self):
        self._engine = sqlalchemy.create_engine(app.config['DATABASE_URI'], convert_unicode=True)
        self._session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autocommit=False, autoflush=False, bind=self._engine))

    def query(self, query, args=None, one=False):
        cur = self._session.execute(query, args)
        try:
            rv = cur.fetchall()
        except sqlalchemy.exc.ResourceClosedError:
            rv = None
        cur.close()
        return (rv[0] if rv else None) if one else rv

    def commit(self):
        self._session.commit()

    def close(self):
        self._session.close()


def get_db():
    if not hasattr(g, '_database'):
        g._database = Database()

    return g._database


def get_new_secret(length=None):
    if length is None:
        length = GENERATED_SECRET_LENGTH

    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def send_email(receiver_email, email_template, **template_args):
    sender_email = "noreply@itacpc.it"
    message = render_template(email_template, receiver_email=receiver_email, **template_args)

    if app.debug:
        print(f"[would send this email to {receiver_email}]:", file=sys.stderr)
        print(message, file=sys.stderr)
    else:
        with smtplib.SMTP_SSL(app.config['SMTP_SERVER'], app.config['SMTP_PORT'],
                              context=ssl.create_default_context()) as server:
            server.login(app.config['SMTP_USER'], app.config['SMTP_PASSWORD'])
            server.sendmail(sender_email, receiver_email, message)


def send_confirmation_email(receiver_email, secret):
    send_email(receiver_email, 'email_registration_confirm.jinja2', secret=secret)


def send_forgot_password_email(receiver_email, secret):
    send_email(receiver_email, 'email_forgot_password.jinja2', secret=secret)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return render_template("maintenance.html")

@app.route('/<uni>')
def uni_page(uni):
    return redirect(url_for('index'))

@app.route('/<uni>/join/<secret>', methods=['GET', 'POST'])
def join_team(uni, secret):
    return redirect(url_for('index'))

@app.route('/login', methods=["GET", "POST"])
def login():
    return redirect(url_for('index'))

@app.route('/my-profile', methods=["GET", "POST"])
def my_profile():
    return redirect(url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return "", 404
