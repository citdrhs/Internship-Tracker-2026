from flask_sqlalchemy import SQLAlchemy

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
#@author Omkar Deshmukh | (hcps-deshmukop@henricostudents.org)                                                                                                      #
#                                                                                                                                                                  #
#@version 1.0                                                                                                                                                      #
#                                                                                                                                                                  #
#@date Date_Of_Creation 2/17/25                                                                                                                                    #
#                                                                                                                                                                  #
#@date Last_Modification 2/17/25                                                                                                                                   #
#
# @editor Shlok Joshi | (hcps-joshis@henricostudents.org)
#
# date Last_Modification 5/16/26 
# 5/16/26 -- # 5/16/26 -- Split users into students, mentors, and admins; make DB init non-destructive                                                                                                                               #
#==================================================================================================================================================================#



db = SQLAlchemy()

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    organization_number = db.Column(db.String(200), nullable=True)
    organization_address = db.Column(db.String(200), nullable=True)
    organization_city = db.Column(db.String(200), nullable=True)
    organization_state = db.Column(db.String(200), nullable=True)
    organization_zip = db.Column(db.String(200), nullable=True)
    organization_web = db.Column(db.String(200), nullable=True)
    screening = db.Column(db.String(200), nullable=True)
    atmosphere = db.Column(db.Boolean, nullable=False, default=False)
    facilities = db.Column(db.Boolean, nullable=False, default=False)
    accommodation = db.Column(db.Boolean, nullable=False, default=False)
    pay = db.Column(db.Boolean, nullable=False, default=False)
    wage_requirements = db.Column(db.Boolean, nullable=False, default=False)
    equal_opportunity = db.Column(db.Boolean, nullable=False, default=False)
    va_verify = db.Column(db.Boolean, nullable=False, default=False)
    supervision = db.Column(db.Boolean, nullable=False, default=False)
    mentorship = db.Column(db.Boolean, nullable=False, default=False)
    virginia_5cs = db.Column(db.Boolean, nullable=False, default=False)
    hours = db.Column(db.Boolean, nullable=False, default=False)
    signature = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    grade = db.Column(db.String(3), nullable=True)
    organization = db.Column(db.String(200), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())


class Mentor(db.Model):
    __tablename__ = 'mentors'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    is_present_view = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())


class MentorAssignment(db.Model):
    __tablename__ = 'mentor_assignments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentors.id', ondelete='CASCADE'), nullable=False)
    assigned_at = db.Column(db.DateTime, server_default=db.func.now())
    __table_args__ = (db.UniqueConstraint('student_id', name='_student_mentor_uc'),)

class PendingUser(db.Model):
    __tablename__ = 'pending_users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="student")
    requested_mentor_id = db.Column(db.Integer, nullable=True)
    is_present_view = db.Column(db.Boolean, nullable=False, default=False)
    grade = db.Column(db.String(3), nullable=True)
