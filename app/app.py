from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from forms import RegisterForm, LoginForm
from models import db, User
from flask_bcrypt import Bcrypt
from better_profanity import profanity
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()
profanity.load_censor_words()
#==================================================================================================================================================================#
#                                                                                                                                                                  #
#Project: CIT Signups                                                                                                                                              #
#Contact: Lynne Norris (lmnorris@henrico.k12.va.us)                                                                                                                #
#                                                                                                                                                                  #
#Deep Run High School Restricted                                                                                                                                   #
#                                                                                                                                                                  #
#DO NOT MODIFY                                                                                                                                                     #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#@brief Has User table(flask) for Login and Register forms                                                                                                         #
#                                                                                                                                                                  #
#@author Omkar Deshmukh | (hcps-deshmukop@henricostudents.org)                                                                                                     #                                                 
#                                                                                                                                                                  #
#@version 1.0                                                                                                                                                      #
#                                                                                                                                                                  #
#@date Date_Of_Creation 2/17/25                                                                                                                                    #
#                                                                                                                                                                  #
#@date Last_Modification 2/17/25                                                                                                                                   #
#                                                                                                                                                                  #
#==================================================================================================================================================================#

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "Internship 2026-OD")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URI")

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')

    mail = Mail(app)
    bcrypt = Bcrypt(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    def generate_confirmation_token(email):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return serializer.dumps(email, salt='email-confirm-salt')

    def confirm_token(token, expiration=3600):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            return serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
        except:
            return False

    def send_confirmation_email(user_email):
        token = generate_confirmation_token(user_email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('confirm_email.html', confirm_url=confirm_url)
        msg = Message("Confirm Your Registration",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[user_email])
        msg.html = html
        mail.send(msg)

    @app.route("/intr/", methods=['GET', 'POST'])
    def index():
        form = LoginForm()

        if request.method == 'POST' and form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()

            if not user:
                flash("Email does not exist.", "danger")
                return redirect(url_for('index'))

            if not bcrypt.check_password_hash(user.password, form.password.data):
                flash("Incorrect password.", "danger")
                return redirect(url_for('index'))

            is_admin = user.is_admin
            is_teacher = user.is_teacher
            is_mentor = user.is_mentor

            try:
                security_code = int(form.securityCode.data)

                if security_code == int(os.environ.get('ADMIN_CODE')):
                    user.is_admin = True
                    is_admin = True
                elif security_code == int(os.environ.get('MENTOR_CODE')):
                    user.is_mentor = True
                    is_mentor = True
                elif security_code == int(os.environ.get('TEACHER_CODE')):
                    user.is_teacher = True
                    is_teacher = True

                db.session.commit()

            except:
                pass

            session['email'] = user.email
            session['organization'] = user.organization
            session['is_admin'] = is_admin
            session['is_teacher'] = is_teacher
            session['is_mentor'] = is_mentor

            return redirect(url_for('index'))

        return render_template("login.html", form=form)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.route("/intr/register", methods=['GET', 'POST'])
    def register():
        form = RegisterForm()

        if request.method == 'POST' and form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                flash("Email already in use.", "danger")
                return redirect(url_for('register'))

            if profanity.contains_profanity(form.first_name.data) or profanity.contains_profanity(form.last_name.data):
                flash("No profanity allowed.", "danger")
                return redirect(url_for('register'))

            if form.password.data != form.confirmPassword.data:
                flash("Passwords do not match.", "danger")
                return redirect(url_for('register'))

            if len(form.password.data) < 8:
                flash("Password must be at least 8 characters.", "danger")
                return redirect(url_for('register'))

            session['pending_user'] = {
                "email": form.email.data,
                "first_name": form.first_name.data,
                "last_name": form.last_name.data,
                "password": bcrypt.generate_password_hash(form.password.data).decode('utf-8'),
                "grade": form.grade.data,
                "is_admin": form.is_admin.data
            }

            send_confirmation_email(form.email.data)
            flash("A confirmation email has been sent.", "info")
            return redirect(url_for('index'))

        return render_template("register.html", form=form)

    @app.route('/intr/confirm/<token>/')
    def confirm_email(token):
        email = confirm_token(token)
        if not email:
            flash("Invalid or expired confirmation link.", "danger")
            return redirect(url_for('register'))

        pending = session.get('pending_user')
        if not pending or pending['email'] != email:
            flash("No matching pending registration.", "danger")
            return redirect(url_for('register'))

        new_user = User(**pending)
        db.session.add(new_user)
        db.session.commit()
        session.pop('pending_user', None)

        flash("Registration confirmed!", "success")
        return redirect(url_for('index'))

    return app


def main():
    app = create_app()
    app.run(debug=True, port=5044)


if __name__ == "__main__":
    main()