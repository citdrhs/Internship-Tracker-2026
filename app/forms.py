from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DateField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional

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
    email = StringField('Email', validators = [DataRequired(), Email()])
    first_name = StringField('First Name', validators = [DataRequired()])
    last_name = StringField('Last Name', validators = [DataRequired()])
    grade = SelectField('Grade', choices=[('8', '8'),('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('n/a', 'n/a')], default = 'n/a')
    organization = StringField('Organization')
    password = PasswordField('Password', validators = [DataRequired()])
    confirmPassword = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    security_code = IntegerField('Security Code', validators=[Optional()])
    submit = SubmitField('Sign In')
