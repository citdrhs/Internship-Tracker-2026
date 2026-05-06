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
    organization = StringField('Organization')
    security_code = StringField("Security Code", validators=[Optional()])
    password = PasswordField('Password', validators = [DataRequired()])
    confirmPassword = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Sign In')
