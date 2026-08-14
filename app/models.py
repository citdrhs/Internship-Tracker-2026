from flask_sqlalchemy import SQLAlchemy

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
    excluded = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class OrganizationMentorEmail(db.Model):
    __tablename__ = 'organization_mentor_emails'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    invited_at = db.Column(db.DateTime, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class Mentor(db.Model):
    __tablename__ = 'mentors'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(200), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class MentorAssignment(db.Model):
    __tablename__ = 'mentor_assignments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentors.id', ondelete='CASCADE'), nullable=False)
    assigned_at = db.Column(db.DateTime, server_default=db.func.now())
    __table_args__ = (db.UniqueConstraint('student_id', name='_student_mentor_uc'),)


class ProgressCheck(db.Model):
    __tablename__ = 'progress_checks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    day_worked = db.Column(db.Date, nullable=False)
    hours_worked = db.Column(db.Numeric(5, 2), nullable=False)
    what_they_did = db.Column(db.Text, nullable=False)
    mentor_questions = db.Column(db.Text, nullable=True)
    reflection = db.Column(db.Text, nullable=True)
    next_steps = db.Column(db.Text, nullable=True)
    self_questions = db.Column(db.Text, nullable=True)
    mentor_response = db.Column(db.Text, nullable=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    is_rejected = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    __table_args__ = (
        db.CheckConstraint("hours_worked >= 0 AND hours_worked <= 24", name="progress_checks_hours_range"),
        db.UniqueConstraint("student_id", "day_worked", name="progress_checks_student_day_uc"),
    )


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentors.id', ondelete='CASCADE'), nullable=True)
    week = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    action_items = db.Column(db.Text, nullable=True)
    focus_areas = db.Column(db.Text, nullable=True)
    quality = db.Column(db.SmallInteger, nullable=False)
    professionalism = db.Column(db.SmallInteger, nullable=False)
    timeliness = db.Column(db.SmallInteger, nullable=False)
    initiative = db.Column(db.SmallInteger, nullable=False)
    softskills = db.Column(db.SmallInteger, nullable=False)
    rating = db.Column(db.Numeric(4, 2), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    __table_args__ = (
        db.CheckConstraint("week BETWEEN 1 AND 52", name="feedback_week_range"),
        db.CheckConstraint("quality BETWEEN 1 AND 5", name="feedback_quality_range"),
        db.CheckConstraint("professionalism BETWEEN 1 AND 5", name="feedback_professionalism_range"),
        db.CheckConstraint("timeliness BETWEEN 1 AND 5", name="feedback_timeliness_range"),
        db.CheckConstraint("initiative BETWEEN 1 AND 5", name="feedback_initiative_range"),
        db.CheckConstraint("softskills BETWEEN 1 AND 5", name="feedback_softskills_range"),
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="feedback_rating_range"),
    )


class FinalEvaluation(db.Model):
    __tablename__ = 'final_evaluations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, unique=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentors.id', ondelete='SET NULL'), nullable=True)
    # I. Specific internship responsibilities
    takes_on_tasks = db.Column(db.SmallInteger, nullable=False)
    seeks_opportunities = db.Column(db.SmallInteger, nullable=False)
    maintains_contact = db.Column(db.SmallInteger, nullable=False)
    accomplished_tasks = db.Column(db.SmallInteger, nullable=False)
    responsibilities_comments = db.Column(db.Text, nullable=True)
    # II. General intern characteristics
    team_member = db.Column(db.SmallInteger, nullable=False)
    enthusiasm = db.Column(db.SmallInteger, nullable=False)
    communication = db.Column(db.SmallInteger, nullable=False)
    problem_solving = db.Column(db.SmallInteger, nullable=False)
    work_ethic = db.Column(db.SmallInteger, nullable=False)
    positive_attitude = db.Column(db.SmallInteger, nullable=False)
    initiative = db.Column(db.SmallInteger, nullable=False)
    attendance = db.Column(db.SmallInteger, nullable=False)
    characteristics_comments = db.Column(db.Text, nullable=True)
    # III. Overall assessment
    overall_rating = db.Column(db.SmallInteger, nullable=False)
    is_reviewed = db.Column(db.Boolean, nullable=False, default=False)
    submitted_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    __table_args__ = tuple(
        db.CheckConstraint(f"{column} BETWEEN 1 AND 5", name=f"final_evaluations_{column}_range")
        for column in (
            "takes_on_tasks", "seeks_opportunities", "maintains_contact", "accomplished_tasks",
            "team_member", "enthusiasm", "communication", "problem_solving",
            "work_ethic", "positive_attitude", "initiative", "attendance", "overall_rating",
        )
    )


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
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class StudentDocument(db.Model):
    __tablename__ = 'student_documents'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.String(1000), nullable=True)
    file_data = db.Column(db.LargeBinary, nullable=True)
    original_name = db.Column(db.String(500), nullable=True)
    content_type = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())


class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    name = db.Column(db.String(50), primary_key=True)
    body = db.Column(db.Text, nullable=False)
