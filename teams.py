import random
import smtplib
import sqlite3
import ssl
import string

from flask import flash, Flask, g, make_response, redirect, render_template, request, session, url_for
from flask_bcrypt import Bcrypt

app = Flask(__name__)
from secret import secret as my_long_secret
app.secret_key = my_long_secret
#app.config["APPLICATION_ROOT"] = "/teams/"
bcrypt = Bcrypt(app)


DATABASE = 'teams.sqlite3'
SCHEMA = 'schema.sql'
MAX_MEMBERS = 3


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource(SCHEMA, mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_new_secret(length):
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def send_confirmation_email(address, secret):
    port = 465  # For SSL
    password = open("mailapikey.txt").read().strip()

    # Create a secure SSL context
    context = ssl.create_default_context()

    sender_email = "noreply@itacpc.it"
    receiver_email = address
    message = """\
From: ITACPC <noreply@itacpc.it>
To: %s
Subject: ITACPC Registration

Hello, thanks for registering to the ITACPC website. In order to confirm your account you should visit the following URL and then login:

https://teams.itacpc.it/confirm-email/%s

After you successfully login, you will be able to either create a team or join an existing one. Now it's time to find team mates!

See you in the next contest,
ITACPC Staff""" % (receiver_email, secret)

    with smtplib.SMTP_SSL("smtp.sendgrid.net", port, context=context) as server:
        server.login("apikey", password)
        server.sendmail(sender_email, receiver_email, message)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    unis = query_db("select u.id, u.name, "
                        "(select count(*) from teams t where university = u.id and (select count(*) from students where team = t.id) > 0), "
                        "(select count(*) from students where university = u.id and confirmed = 1) "
                    "from universities u order by 3 desc, 4 desc, 2 collate nocase asc")

    # Move the "other" university to the top
    index = -1
    for i in range(len(unis)):
        if unis[i][0] == "other":
            index = i
            break

    if index >= 0:
        unis = [unis[index]] + unis[:index] + unis[index + 1:]

    # If the user belongs to some university, move THAT to the top
    if "university" in session:
        index = -1
        for i in range(len(unis)):
            if unis[i][0] == session["university"]:
                index = i
                break

        if index >= 0:
            unis = [unis[index]] + unis[:index] + unis[index + 1:]

    team_count = query_db("select count(*) from teams t where (select count(*) from students where team = t.id) > 0", one=True)
    students_count = query_db("select count(*) from students where confirmed = 1", one=True)

    return render_template("home.html", unis=unis, team_count=team_count, students_count=students_count)


from wtforms import Form, BooleanField, StringField, PasswordField, SubmitField, validators
from flask_wtf import FlaskForm

class DomainValidator:
    def __init__(self, domain):
        self.domain = domain

    def __call__(self, form, field):
        if self.domain == '*':
            return

        for dom in self.domain.split(","):
            if field.data.endswith('@' + dom) or field.data.endswith('.' + dom):
                return

        raise validators.ValidationError('Use your institutional email address')

@app.route('/<uni>')
def uni_page(uni):
    uni_full, = query_db("select name from universities where id = ?", (uni,), one=True)
    teams = query_db("select id, name from teams t where t.university = ? "
                     "and (select count(*) from students where team = t.id) > 0 "
                     "order by 1", (uni,))
    students = query_db("select team, first_name, last_name, olinfo_handle, codeforces_handle, "
                        "topcoder_handle from students where confirmed = 1 and team is not null "
                        "and university = ? order by 1, 2, 3", (uni,))
    students_left = query_db("select first_name, last_name, olinfo_handle, codeforces_handle, "
                             "topcoder_handle from students where confirmed = 1 and team is null "
                             "and university = ?", (uni,))

    # Show team formation
    grouped = []

    if len(teams) > 0:
        t = 0
        grouped.append([teams[t][0], [students[0][1:]]])
        for i in range(1, len(students)):
            if students[i][0] == grouped[-1][0]:
                grouped[-1][1].append(students[i][1:])
            else:
                t += 1
                grouped.append([teams[t][0], [students[i][1:]]])

        for i in range(len(grouped)):
            grouped[i][0] = teams[i][1]

    return render_template('uni-page.html', uni=uni, uni_full=uni_full, teams=teams, grouped=grouped, students_left=students_left)

@app.route('/<uni>/new-student', methods=['GET', 'POST'])
def new_student(uni):
    uni_full, uni_domain = query_db("select name, domain from universities where id = ?", (uni,), one=True)

    class RegistrationForm(Form):
        first_name = StringField('First Name', [validators.Length(min=1, max=100)])
        last_name = StringField('Last Name', [validators.Length(min=1, max=100)])
        email = StringField('Email Address', [validators.Length(min=6, max=100), DomainValidator(uni_domain), validators.Regexp(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", message="Invalid characters in email address")])
        password = PasswordField('New Password', [
            validators.DataRequired(),
            validators.EqualTo('confirm', message='Passwords must match')
        ])
        confirm = PasswordField('Repeat Password')

        olinfo_handle = StringField('(Optional) Your username on training.olinfo.it', [validators.Length(max=100)])
        codeforces_handle = StringField('(Optional) Your username on codeforces.com', [validators.Length(max=100)])
        topcoder_handle = StringField('(Optional) Your username on topcoder.com', [validators.Length(max=100)])

    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
        pw_hash = bcrypt.generate_password_hash(form.password.data)
        secret = get_new_secret(30)

        fname = form.first_name.data.title()
        lname = form.last_name.data.title()

        try:
            query_db("insert into students(first_name, last_name, email, password, university, secret, "
                    "olinfo_handle, codeforces_handle, topcoder_handle) values(?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    fname, lname, form.email.data, pw_hash, uni, secret,
                    form.olinfo_handle.data or None, form.codeforces_handle.data or None,
                    form.topcoder_handle.data or None))

            send_confirmation_email(form.email.data, secret)

            get_db().commit()

        except smtplib.SMTPRecipientsRefused:
            return ("Email address is invalid", 400)

        except sqlite3.IntegrityError:
            return ("Email address already in use", 409)

        return render_template('check-inbox.html', uni=uni, email=form.email.data, student_full=form.first_name.data + " " + form.last_name.data)

    return render_template('new-student.html', form=form, uni=uni, uni_domain=uni_domain, uni_full=uni_full)

@app.route('/confirm-email/<secret>')
def confirm_email(secret):
    student = query_db("select id from students where secret = ?", (secret,), one=True)

    if student is None:
        return ("The URL looks wrong, did you copy and paste it correctly?", 400)

    query_db("update students set confirmed = 1 where id = ?", (student[0],))
    get_db().commit()
    flash("Email address confirmed!")
    return redirect(url_for('login'))

@app.route('/<uni>/new-team', methods=['GET', 'POST'])
def new_team(uni):
    if "email" not in session:
        return redirect(url_for('login'))

    if "team" in session:
        flash("You are already part of a team!")
        return redirect(url_for('my_profile'))

    uni_full, = query_db("select name from universities where id = ?", (uni,), one=True)

    if session["university"] != uni:
        flash("You can only create teams in your own university!")
        return redirect(url_for('new_team', uni=session["university"]))

    class TeamCreationForm(Form):
        team_name = StringField('Team Name', [validators.Length(min=1, max=50)])

    form = TeamCreationForm(request.form)

    if request.method == 'POST' and form.validate():
        secret = get_new_secret(30)
        query_db("insert into teams(name, university, secret) "
                 "values(?, ?, ?)", (form.team_name.data, uni, secret))
        team_id, = query_db("select last_insert_rowid()", one=True)
        query_db("update students set team = ? where email = ?", (team_id, session["email"]))
        get_db().commit()

        # set team in session
        session["team"] = team_id

        return render_template('new-team-created.html', uni=uni, uni_full=uni_full, team_name=form.team_name.data, secret=secret)

    return render_template('new-team.html', form=form, uni=uni, uni_full=uni_full)

@app.route('/<uni>/join/<secret>', methods=['GET', 'POST'])
def join_team(uni, secret):
    if "email" not in session:
        return redirect(url_for('login'))

    student_full, = query_db("select first_name || ' ' || last_name from students where email = ?", (session["email"],), one=True)

    try:
        team_id, university = query_db("select id, university from teams where secret = ?", (secret,), one=True)
    except TypeError:
        message = "The secret string to join the team was not recognized, check if you copied and pasted the correct URL."
        return render_template('team-join.html', uni=uni, student_full=student_full, message=message)

    if university != uni:
        message = "The URL looks wrong, did you copy and paste it correctly?"
        return render_template('team-join.html', uni=uni, student_full=student_full, message=message)

    if session["university"] != uni:
        message = "You can only join teams from your university!"
        return render_template('team-join.html', uni=uni, student_full=student_full, message=message)

    if request.method == "GET":
        return render_template("team-join-confirm.html", uni=uni, student_full=student_full)

    elif request.method == "POST":
        current_team, = query_db("select team from students where email = ?", (session["email"],), one=True)

        if current_team is None:
            current_members, = query_db("select count(*) from students where team = ?", (team_id,), one=True)
            if current_members >= MAX_MEMBERS:
                message = "This team has reached the maximum number of members :("
            else:
                student_id, = query_db("select id from students where email = ?", (session["email"],), one=True)
                query_db("update students set team = ? where id = ?", (team_id, student_id))
                query_db("insert into teamjoinlog(student, team, joining) values (?, ?, ?)", (student_id, team_id, 1))
                get_db().commit()

                # set team in session
                session["team"] = team_id

                message = "You successfully joined the team. Go to your profile to verify it."
        else:
            if current_team == team_id:
                message = "You're set! You already joined the team by visiting this URL. Go to your profile to verify it."
            else:
                message = "You can't join a new team, you should first leave your current team."

        return render_template('team-join.html', uni=uni, student_full=student_full, message=message)

@app.route('/my-profile')
def my_profile():
    if "email" not in session:
        return redirect(url_for('login'))

    uni, team_id, student_full = \
        query_db("select s.university, s.team, s.first_name || ' ' || s.last_name from students s where s.email = ?",
                 (session["email"],), one=True)

    if team_id is not None:
        team_name, team_secret = query_db("select name, secret from teams where id = ?", (team_id,), one=True)
        team_members = query_db("select first_name || ' ' || last_name from students where team = ?", (team_id,))
    else:
        team_name, team_secret = None, None
        team_members = []


    return render_template('my-profile.html', uni=uni, team_name=team_name, student_full=student_full, team_members=team_members, secret=team_secret)

@app.route('/leave-team', methods=['GET', 'POST'])
def leave_team():
    if "email" not in session:
        return redirect(url_for('login'))

    student_full, = query_db("select first_name || ' ' || last_name from students where email = ?", (session["email"],), one=True)
    uni, team_id = query_db("select university, team from students where email = ?", (session["email"],), one=True)

    if request.method == "POST":
        student_id, = query_db("select id from students where email = ?", (session["email"],), one=True)
        query_db("update students set team = null where id = ?", (student_id,))
        query_db("insert into teamjoinlog(student, team, joining) values (?, ?, ?)", (student_id, team_id, 0))
        query_db("update teams set secret = ? where id = ?", (get_new_secret(30), team_id,))
        get_db().commit()

        # remove team from session
        session.pop("team", None)

        return redirect(url_for('my_profile'))

    return render_template('leave-team.html', uni=uni, student_full=student_full)

@app.route('/login', methods=['GET', 'POST'])
def login():
    class LoginForm(Form):
        email = StringField('Email Address')
        password = PasswordField('Password')
        submit = SubmitField('Submit')

    form = LoginForm(request.form)

    if "email" in session:
        return redirect(url_for("index"))

    if request.method == 'POST' and form.validate():
        try:
            pw_hash, university, team, confirmed = query_db("select password, university, team, confirmed from students where email = ?", (form.email.data,), one=True)

            if not confirmed:
                flash("You should first confirm your email address")
            elif bcrypt.check_password_hash(pw_hash, form.password.data):
                session['email'] = request.form['email']
                session['university'] = university
                if team is not None:
                    session['team'] = team
                return redirect(url_for('uni_page', uni=university))
            else:
                flash("Wrong email or password!")
        except TypeError:
            flash("Wrong email or password!")

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('university', None)
    session.pop('team', None)
    return redirect(url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return ("", 404)
