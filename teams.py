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
        SELECT first_name, last_name, olinfo_handle, codeforces_handle, topcoder_handle, kattis_handle, github_handle
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
        email = StringField('Email Address', [
                            validators.Length(min=6, max=100), DomainValidator(uni_domain),
                            validators.Regexp(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
                                              message="Invalid characters in email address")])

        first_name = StringField('First Name', [validators.Length(min=1, max=100)])
        last_name = StringField('Last Name', [validators.Length(min=1, max=100)])

    form = RegistrationForm(request.form)

    if request.method == 'POST' and form.validate():
        secret = get_new_secret()

        args = {
            'fname': form.first_name.data.title(),
            'lname': form.last_name.data.title(),
            'email': form.email.data.lower(),
            'uni': uni,
            'secret': secret,
        }

        try:
            get_db().query("""
                INSERT INTO students(first_name, last_name, email, university, secret)
                VALUES (:fname, :lname, :email, :uni, :secret)
            """, args)

            send_confirmation_email(args['email'], secret)

            get_db().commit()

        except smtplib.SMTPRecipientsRefused:
            return "Email address is invalid", 400

        except sqlalchemy.exc.IntegrityError:
            return "Email address already in use", 409

        return render_template('check-inbox.html', uni=uni, email=form.email.data, student_full=form.first_name.data + " " + form.last_name.data)

    return render_template('new-student.html', form=form, uni=uni, uni_domain=uni_domain, uni_full=uni_full)


@app.route('/confirm-email/<secret>', methods=['GET', 'POST'])
def confirm_email(secret):
    try:
        student_id, student_email, student_full, uni = get_db().query("SELECT id, email, first_name || ' ' || last_name, university FROM students WHERE secret = :secret", {'secret': secret}, one=True)
    except TypeError:
        return "The URL looks wrong, did you copy and paste it correctly?", 400

    class ConfirmForm(Form):
        password = PasswordField('New Password', [
            validators.DataRequired(),
            validators.EqualTo('confirm', message='Passwords must match')
        ])
        confirm = PasswordField('Repeat Password')

        olinfo_handle = StringField('(Optional) Your username on training.olinfo.it', [validators.Length(max=100)])
        codeforces_handle = StringField('(Optional) Your username on codeforces.com', [validators.Length(max=100)])
        topcoder_handle = StringField('(Optional) Your username on topcoder.com', [validators.Length(max=100)])
        kattis_handle = StringField('(Optional) Your username on open.kattis.com', [validators.Length(max=100)])
        github_handle = StringField('(Optional) Your username on github.com', [validators.Length(max=100)])

    form = ConfirmForm(request.form)

    if request.method == 'POST' and form.validate():
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        args = {
            'id': student_id,
            'pw_hash': pw_hash,
            'olinfo': form.olinfo_handle.data or None,
            'codeforces': form.codeforces_handle.data or None,
            'topcoder': form.topcoder_handle.data or None,
            'kattis': form.kattis_handle.data or None,
            'github': form.github_handle.data or None,
        }
        get_db().query("""UPDATE students SET
            confirmed = TRUE, password = :pw_hash,
            olinfo_handle = :olinfo, codeforces_handle = :codeforces,
            topcoder_handle = :topcoder, kattis_handle = :kattis,
            github_handle = :github
            WHERE id = :id""", args)
        get_db().commit()
        flash("Account confirmed!")
        return redirect(url_for('login'))

    return render_template('confirm_email.html', form=form, email=student_email, student_full=student_full, uni=uni)


@app.route('/reset-password/<secret>', methods=['GET', 'POST'])
def reset_password(secret):
    try:
        student_id, student_email, student_full, uni, secret_valid_until = get_db().query("SELECT id, email, first_name || ' ' || last_name, university, secret_valid_until FROM students WHERE secret = :secret", {'secret': secret}, one=True)
    except TypeError:
        return "The URL looks wrong, did you copy and paste it correctly?", 400

    class ResetPasswordForm(Form):
        password = PasswordField('New Password', [
            validators.DataRequired(),
            validators.EqualTo('confirm', message='Passwords must match')
        ])
        confirm = PasswordField('Repeat Password')

    form = ResetPasswordForm(request.form)

    if datetime.now() > secret_valid_until:
        flash('The link has expired, you should request a new password reset.')
        return redirect(url_for('login'))

    if request.method == 'POST' and form.validate():
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        args = {
            'id': student_id,
            'pw_hash': pw_hash,
        }
        get_db().query("""UPDATE students SET
            password = :pw_hash,
            secret_valid_until = current_timestamp
            WHERE id = :id""", args)
        get_db().commit()
        flash("Password reset was successful!")
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form, email=student_email, student_full=student_full, uni=uni)


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
        secret = get_new_secret()

        student_id, = get_db().query(
            "SELECT id FROM students WHERE email = :email",
            {'email': session["email"]}, one=True
        )

        team_id, = get_db().query("""
            INSERT INTO teams(name, university, secret)
            VALUES (:team_name, :uni, :secret)
            RETURNING id
        """, {'team_name': form.team_name.data, 'uni': uni, 'secret': secret}, one=True)

        get_db().query(
            "INSERT INTO teamjoinlog(student, team, joining) VALUES (:student_id, :team_id, :joining)",
            {'student_id': student_id, 'team_id': team_id, 'joining': True}
        )

        get_db().query(
            "UPDATE students SET team = :team_id WHERE id = :student_id",
            {'team_id': team_id, 'student_id': student_id}
        )
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


@app.route('/my-profile', methods=["GET", "POST"])
def my_profile():
    if "email" not in session:
        return redirect(url_for('login'))

    uni, team_id, student_full, olinfo, codeforces, topcoder, kattis, github = get_db().query("""
            SELECT
                s.university,
                s.team,
                s.first_name || ' ' || s.last_name,
                s.olinfo_handle,
                s.codeforces_handle,
                s.topcoder_handle,
                s.kattis_handle,
                s.github_handle
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

    class EditProfileForm(Form):
        olinfo_handle = StringField('Username on training.olinfo.it', [validators.Length(max=100)], default=olinfo)
        codeforces_handle = StringField('Username on codeforces.com', [validators.Length(max=100)], default=codeforces)
        topcoder_handle = StringField('Username on topcoder.com', [validators.Length(max=100)], default=topcoder)
        kattis_handle = StringField('Username on open.kattis.com', [validators.Length(max=100)], default=kattis)
        github_handle = StringField('Username on github.com', [validators.Length(max=100)], default=github)

    form = EditProfileForm(request.form)

    if request.method == "POST" and form.validate():
        args = {
            'email': session["email"],
            'olinfo': form.olinfo_handle.data,
            'codeforces': form.codeforces_handle.data,
            'topcoder': form.topcoder_handle.data,
            'kattis': form.kattis_handle.data,
            'github': form.github_handle.data,
        }

        get_db().query("""
            UPDATE students SET
                olinfo_handle = :olinfo, codeforces_handle = :codeforces,
                topcoder_handle = :topcoder, kattis_handle = :kattis,
                github_handle = :github
            WHERE email = :email""", args)
        get_db().commit()

        flash('Information was updated successfully!')

    return render_template('my-profile.html', form=form, email=session["email"], uni=uni, team_name=team_name,
                            student_full=student_full, team_members=team_members, secret=team_secret)


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

        # Reset team secret for additional security
        get_db().query(
            "UPDATE teams SET secret = :secret WHERE id = :team_id",
            {'secret': get_new_secret(), 'team_id': team_id}
        )

        get_db().commit()

        # Remove team from session
        session.pop("team", None)

        return redirect(url_for('my_profile'))

    return render_template('leave-team.html', uni=uni, student_full=student_full)


@app.route('/login', methods=['GET', 'POST'])
def login():
    class LoginForm(Form):
        email = StringField('Email Address', [
                            validators.Length(min=6, max=100),
                            validators.Regexp(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
                                              message="Invalid characters in email address")])
        password = PasswordField('Password')
        submit = SubmitField('Submit')

    form = LoginForm(request.form)

    if "email" in session:
        return redirect(url_for("index"))

    if request.method == 'POST' and form.validate():
        try:
            args = {'email': form.email.data.lower()}
            pw_hash, university, team, confirmed = get_db().query(
                "SELECT password, university, team, confirmed FROM students WHERE email = :email",
                args, one=True)

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


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    class ForgotPasswordForm(Form):
        email = StringField('Email Address', [
                            validators.Length(min=6, max=100),
                            validators.Regexp(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",
                                              message="Invalid characters in email address")])

    if "email" in session:
        return redirect(url_for("index"))

    form = ForgotPasswordForm(request.form)

    if request.method == 'POST' and form.validate():
        args = {
            'email': form.email.data.lower(),
            'validity': datetime.now() + RESET_PASSWORD_INTERVAL,
            'secret': get_new_secret()
        }

        try:
            secret_valid_until, = get_db().query("SELECT secret_valid_until FROM students WHERE email = :email", args, one=True)

            if datetime.now() > secret_valid_until:
                get_db().query(
                    "UPDATE students set secret = :secret, secret_valid_until = :validity WHERE email = :email",
                    args)
                get_db().commit()

                send_forgot_password_email(args["email"], args['secret'])

                flash('Done! Check you inbox (also the spam folder!) for the password reset link.')
            else:
                left = secret_valid_until - datetime.now()
                flash('You should wait about %d hours before another request' % (left // timedelta(hours=1)))
        except TypeError:
            flash("Email not found!")

    return render_template('forgot.html', form=form)


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('university', None)
    session.pop('team', None)
    return redirect(url_for('index'))


@app.route('/favicon.ico')
def favicon():
    return "", 404
