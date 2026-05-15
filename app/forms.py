from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DateField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional, URL


import os
import psycopg2
from psycopg2.extras import DictCursor

def get_database_settings():
    db_name = os.environ.get("DB")
    db_user = os.environ.get("DB_UN")
    db_password = os.environ.get("DB_PW")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = int(os.environ.get("DB_PORT", "5432"))

    if db_name and db_user and db_password:
        return {
            "dbname": db_name,
            "user": db_user,
            "password": db_password,
            "host": db_host,
            "port": db_port,
        }

    database_uri = os.environ.get("DATABASE_URI")
    if database_uri:
        return {"database_uri": database_uri}

    raise ValueError("Database configuration is missing. Set DB, DB_UN, and DB_PW in env.")

def get_db_connection():
    settings = get_database_settings()
    if "database_uri" in settings:
        return psycopg2.connect(settings["database_uri"])

    return psycopg2.connect(
        dbname=settings["dbname"],
        user=settings["user"],
        password=settings["password"],
        host=settings["host"],
        port=settings["port"],
    )

def fetch_organizations():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory= DictCursor) as cur:
            cur.execute(
                """
                SELECT id, organization_name
                FROM organizations
                ORDER BY organization_name
                """
            )
            return cur.fetchall()
    finally:
        conn.close()

def fetch_mentors():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory= DictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM mentors;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()

def fetch_students():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory= DictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM students;
                """
            )
            return cur.fetchall()
    finally:
        conn.close()

#==================================================================================================================================================================#
#                                                                                                                                                                  #
#Project: CIT Internship Tracker                                                                                                                                   #
#Contact: Lynne Norris (lmnorris@henrico.k12.va.us)                                                                                                                #
#                                                                                                                                                                  #
#Deep Run High School Restricted                                                                                                                                   #
#                                                                                                                                                                  #
#DO NOT MODIFY                                                                                                                                                     #
#------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#@brief Has frontend field                                                                                                                                         #
#                                                                                                                                                                  #
#@author Omkar Deshmukh | (hcps-deshmukop@henricostudents.org)                                                                                                     #                                                 
#                                                                                                                                                                  #
#@version 1.0                                                                                                                                                      #
#                                                                                                                                                                  #
#@date Date_Of_Creation 2/14/26                                                                                                                                    #
#                                                                                                                                                                  #
#@date Last_Modification 2/14/26                                                                                                                                   #
#                                                                                                                                                                  #
#==================================================================================================================================================================#

class RegisterForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()], filters=[lambda x: x.strip() if x else None])
    first_name = StringField('First Name', validators = [DataRequired()])
    last_name = StringField('Last Name', validators = [DataRequired()])
    role = SelectField("I am a...", choices= [("", "Select Role"), ("student", "Student"), ("mentor", "Mentor"), ("admin", "Admin")])
    organization_id = SelectField("Organizations", choices = [("", "Select your organization")] + [(org['id'], org['organization_name']) for org in fetch_organizations()])
    mentor_id = SelectField("Mentors", choices = [("", "Select your mentor")] + [(mentor['id'], f"{mentor['first_name']} {mentor['last_name']}") for mentor in fetch_mentors()])
    security_code = StringField("Security Code", validators=[Optional()])
    password = PasswordField('Password', validators = [DataRequired()])
    confirmPassword = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Sign In')

class AddOrganizationForm(FlaskForm):
    organization_name = StringField('Organization Name', validators = [DataRequired()])
    email = StringField('Email', validators = [DataRequired(), Email()], filters=[lambda x: x.strip() if x else None])
    phone_number = StringField('Phone Number', validators= [DataRequired(), ])
    address = StringField('Address', validators= [DataRequired()])
    city = StringField('City', validators= [DataRequired()])
    state = StringField('State', validators= [DataRequired()])
    zip_code = StringField('Zip Code', validators= [DataRequired()])
    website = StringField('Website', validators= [DataRequired(), URL(require_tld = True)])
    type_of_screening = StringField('Type Of Screen', validators= [DataRequired()])
    wbl_checklist = FileField('WBL checklist', validators = [FileRequired(), FileAllowed(['pdf'], 'Must upload a pdf fillable form')])
    training_agreement_form = FileField('Training Agreement Form', validators = [FileRequired(), FileAllowed(['pdf'], 'Must upload a pdf fillable form')])
    submit = SubmitField('Add organization')

class AdminStudentForm(FlaskForm):
    selected_student_id = SelectField("Students", choices = [("", "Select a student")] + [(student['id'], f"{student['first_name']} {student['last_name']}") for student in fetch_students()])
    submit = SubmitField('View Student')