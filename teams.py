import sys
import random
import smtplib
import ssl
import string

import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm

from flask import flash, Flask, g, redirect, render_template, request, session, url_for
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config.from_pyfile('config.py')

bcrypt = Bcrypt(app)

MAX_MEMBERS = 3


class Database:
    SCHEMA = 'schema.sql'

    def __init__(self):
        self._engine = sqlalchemy.create_engine(app.config['DATABASE_URI'], convert_unicode=True)
        self._session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autocommit=False, autoflush=False, bind=self._engine))

    def init(self):
        with app.open_resource(self.SCHEMA, mode='r') as f:
            self._session.execute(f.read())
        self._session.commit()

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


def get_new_secret(length):
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def send_confirmation_email(receiver_email, secret):
    # Create a secure SSL context
    context = ssl.create_default_context()

    sender_email = "noreply@itacpc.it"
    message = render_template('registration_confirm.jinja2', secret=secret, receiver_email=receiver_email)

    try:
        with smtplib.SMTP_SSL(app.config['SMTP_SERVER'], app.config['SMTP_PORT'], context=context) as server:
            server.login(app.config['SMTP_USER'], app.config['SMTP_PASSWORD'])
            server.sendmail(sender_email, receiver_email, message)
    except smtplib.SMTPException as e:
        if not app.debug:
            raise e
        print("Not sending email -- in debug mode", file=sys.stderr)
        print(f"Here is the {message}", file=sys.stderr)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    unis = get_db().query("""
        SELECT u.id, u.name, (
            SELECT count(*) 
            FROM teams t 
            WHERE university = u.id AND (
                SELECT count(*) 
                FROM students
                 WHERE team = t.id) > 0
        ), (
            SELECT count(*) 
            FROM students 
            WHERE university = u.id and confirmed
        ) 
        FROM universities u 
        ORDER BY 3 DESC, 4 DESC, upper(u.name)
    """)

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

    team_count = get_db().query("""
        SELECT count(*) 
        FROM teams t 
        WHERE (SELECT count(*) FROM students WHERE team = t.id) > 0
    """, one=True)

    students_count = get_db().query("SELECT count(*) FROM students WHERE confirmed", one=True)

    return render_template("home.html", unis=unis, team_count=team_count, students_count=students_count)


from wtforms import Form, StringField, PasswordField, SubmitField, validators


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
    args = {'uni': uni}
    uni_full, = get_db().query("SELECT name FROM universities WHERE id = :uni", args, one=True)

    teams = get_db().query("""
        SELECT id, name 
        FROM teams t 
        WHERE t.university = :uni AND (select count(*) from students where team = t.id) > 0 
        ORDER BY 1
    """, args)

    students = get_db().query("""
        SELECT team, first_name, last_name, olinfo_handle, codeforces_handle, topcoder_handle 
        FROM students 
        WHERE confirmed AND team IS NOT NULL AND university = :uni 
        ORDER BY 1, 2, 3
    """, args)

    students_left = get_db().query("""
        SELECT first_name, last_name, olinfo_handle, codeforces_handle, topcoder_handle
        FROM students 
        WHERE confirmed AND team IS NULL AND university = :uni
    """, args)

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
    uni_full, uni_domain = get_db().query("SELECT name, domain FROM universities WHERE id = :uni", {'uni': uni}, one=True)

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
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        secret = get_new_secret(30)

        fname = form.first_name.data.title()
        lname = form.last_name.data.title()

        try:
            args = {
                'fname': fname, 
                'lname': lname, 
                'email': form.email.data, 
                'pw_hash': pw_hash, 
                'uni': uni, 
                'secret': secret,
                'olinfo': form.olinfo_handle.data or None, 
                'codeforces': form.codeforces_handle.data or None,
                'topcoder': form.topcoder_handle.data or None,
            }
            get_db().query("""
                INSERT INTO students(first_name, last_name, email, password, university, secret, olinfo_handle, codeforces_handle, topcoder_handle) 
                VALUES (:fname, :lname, :email, :pw_hash, :uni, :secret, :olinfo, :codeforces, :topcoder)
            """, args)

            send_confirmation_email(form.email.data, secret)

            get_db().commit()

        except smtplib.SMTPRecipientsRefused:
            return "Email address is invalid", 400

        except sqlalchemy.exc.IntegrityError:
            return "Email address already in use", 409

        return render_template('check-inbox.html', uni=uni, email=form.email.data, student_full=form.first_name.data + " " + form.last_name.data)

    return render_template('new-student.html', form=form, uni=uni, uni_domain=uni_domain, uni_full=uni_full)


@app.route('/confirm-email/<secret>')
def confirm_email(secret):
    student = get_db().query("SELECT id FROM students WHERE secret = :secret", {'secret': secret}, one=True)

    if student is None:
        return "The URL looks wrong, did you copy and paste it correctly?", 400

    get_db().query("UPDATE students SET confirmed = TRUE WHERE id = :id", {'id': student[0]})
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

    uni_full, = get_db().query("SELECT name FROM universities WHERE id = :uni", {'uni': uni}, one=True)

    if session["university"] != uni:
        flash("You can only create teams in your own university!")
        return redirect(url_for('new_team', uni=session["university"]))

    class TeamCreationForm(Form):
        team_name = StringField('Team Name', [validators.Length(min=1, max=50)])

    form = TeamCreationForm(request.form)

    if request.method == 'POST' and form.validate():
        secret = get_new_secret(30)

        team_id, = get_db().query("""
            INSERT INTO teams(name, university, secret)
            VALUES (:team_name, :uni, :secret)
            RETURNING id
        """, {'team_name': form.team_name.data, 'uni': uni, 'secret': secret}, one=True)

        get_db().query("UPDATE students SET team = :team_id WHERE email = :email", {'team_id': team_id, 'email': session["email"]})
        get_db().commit()

        # set team in session
        session["team"] = team_id

        return render_template('new-team-created.html', uni=uni, uni_full=uni_full, team_name=form.team_name.data, secret=secret)

    return render_template('new-team.html', form=form, uni=uni, uni_full=uni_full)


@app.route('/<uni>/join/<secret>', methods=['GET', 'POST'])
def join_team(uni, secret):
    if "email" not in session:
        return redirect(url_for('login'))

    student_full, = get_db().query("SELECT first_name || ' ' || last_name FROM students WHERE email = :email", {'email': session["email"]}, one=True)

    try:
        team_id, university = get_db().query("SELECT id, university FROM teams WHERE secret = :secret", {'secret': secret}, one=True)
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
        current_team, = get_db().query("SELECT team FROM students WHERE email = :email", {'email': session["email"]}, one=True)

        if current_team is None:
            current_members, = get_db().query(
                "SELECT count(*) FROM students WHERE team = :team_id",
                {'team_id': team_id},
                one=True
            )

            if current_members >= MAX_MEMBERS:
                message = "This team has reached the maximum number of members :("
            else:
                student_id, = get_db().query(
                    "SELECT id FROM students WHERE email = :email",
                    {'email': session["email"]},
                    one=True
                )

                get_db().query(
                    "UPDATE students SET team = :team_id WHERE id = :student_id",
                    {'team_id': team_id, 'student_id': student_id}
                )

                get_db().query(
                    "INSERT INTO teamjoinlog(student, team, joining) VALUES (:student_id, :team_id, :joining)",
                    {'student_id': student_id, 'team_id': team_id, 'joining': True}
                )
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

    uni, team_id, student_full = get_db().query("""
            SELECT s.university, s.team, s.first_name || ' ' || s.last_name 
            FROM students s 
            WHERE s.email = :email
        """, {'email': session["email"]}, one=True)

    if team_id is not None:
        args = {'team_id': team_id}
        team_name, team_secret = get_db().query("SELECT name, secret FROM teams WHERE id = :team_id", args, one=True)
        team_members = get_db().query("SELECT first_name || ' ' || last_name FROM students WHERE team = :team_id", args)
    else:
        team_name, team_secret = None, None
        team_members = []

    return render_template('my-profile.html', uni=uni, team_name=team_name, student_full=student_full,
                           team_members=team_members, secret=team_secret)


@app.route('/leave-team', methods=['GET', 'POST'])
def leave_team():
    if "email" not in session:
        return redirect(url_for('login'))

    args = {'email': session["email"]}
    student_full, = get_db().query("SELECT first_name || ' ' || last_name FROM students WHERE email = :email", args, one=True)
    uni, team_id = get_db().query("SELECT university, team FROM students WHERE email = :email", args, one=True)

    if request.method == "POST":
        student_id, = get_db().query("SELECT id FROM students WHERE email = :email", args, one=True)
        get_db().query("UPDATE students SET team = NULL WHERE id = :student_id", {'student_id': student_id})

        get_db().query(
            "INSERT INTO teamjoinlog(student, team, joining) VALUES (:student_id, :team_id, :joining)",
            {'student_id': student_id, 'team_id': team_id, 'joining': False}
        )

        get_db().query(
            "UPDATE teams SET secret = :secret WHERE id = :team_id",
            {'secret': get_new_secret(30), 'team_id': team_id}
        )

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
            pw_hash, university, team, confirmed = get_db().query(
                "SELECT password, university, team, confirmed FROM students WHERE email = :email",
                {'email': form.email.data},
                one=True
            )

            if not confirmed:
                flash("You should first confirm your email address")
            elif bcrypt.check_password_hash(pw_hash.encode('utf-8'), form.password.data):
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
    return "", 404
