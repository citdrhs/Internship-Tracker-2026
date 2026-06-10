import json
import os
from pathlib import Path
from urllib.parse import quote_plus

import psycopg2
from better_profanity import profanity
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from app.forms import LoginForm, RegisterForm
from itsdangerous import URLSafeTimedSerializer
from app.models import Admin, Mentor, PendingUser, Student, MentorAssignment, db

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

load_dotenv()
profanity.load_censor_words()

DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", "10"))
DB_POOL_RECYCLE_SECONDS = int(os.environ.get("DB_POOL_RECYCLE_SECONDS", "300"))
DB_POOL_TIMEOUT_SECONDS = int(os.environ.get("DB_POOL_TIMEOUT_SECONDS", "30"))

ORGANIZATION_TEXT_FIELDS = [
    {
        "name": "organization_number",
        "label": "Organization Phone Number",
        "type": "number",
        "placeholder": "Enter organization number",
    },
    {
        "name": "organization_address",
        "label": "Organization Address",
        "type": "text",
        "placeholder": "Enter organization address",
    },
    {
        "name": "organization_city",
        "label": "Organization City",
        "type": "text",
        "placeholder": "Enter organization city",
    },
    {
        "name": "organization_state",
        "label": "Organization State",
        "type": "text",
        "placeholder": "Enter organization state",
    },
    {
        "name": "organization_zip",
        "label": "Organization ZIP Code",
        "type": "number",
        "placeholder": "Enter organization zip code",
    },
    {
        "name": "organization_web",
        "label": "Organization Website",
        "type": "url",
        "placeholder": "Enter organization website",
    },
    {
        "name": "screening",
        "label": "What type of screening is required?",
        "type": "text",
        "placeholder": "Enter here",
    },
]

ORGANIZATION_CHECKBOX_FIELDS = [
    {
        "name": "atmosphere",
        "label": "Is the atmosphere of the workplace conducive to the Work-based Learning experience?",
    },
    {
        "name": "facilities",
        "label": "Are the facilities and equipment conducive to student safety in the area in which students will be completing the WBL experience?",
    },
    {
        "name": "accommodation",
        "label": "Will the workplace provide accommodation(s) for students with disabilities?",
    },
    {
        "name": "pay",
        "label": "Is the workplace offering paid student experiences?",
    },
    {
        "name": "wage_requirements",
        "label": "For paid experiences, are all federal and state wage requirements met?",
    },
    {
        "name": "equal_opportunity",
        "label": "Does the workplace provide equal opportunities for students without discrimination based on race, sex, color, national origin, religion, sexual orientation, gender identity, age, political affiliation or against otherwise qualified persons with disabilities?",
    },
    {
        "name": "va_verify",
        "label": "Has the employer verified students will not be working in direct contact with anyone on the Virginia State Police Sex Offender Registry pursuant to Section 22.1-296.1 of the Code of Virginia?",
    },
    {
        "name": "supervision",
        "label": "Will the employer ensure students will always be working under the supervision of an industry professional at the workplace?",
    },
    {
        "name": "mentorship",
        "label": "Will the employer provide structured mentorship with an industry professional at the workplace?",
    },
    {
        "name": "virginia_5cs",
        "label": "Will the employer provide opportunities for students to build Virginia's 5 Cs (critical thinking, collaboration, communication, creative thinking, and citizenship) on a daily basis?",
    },
    {
        "name": "hours",
        "label": "Will the employer provide students with at least 160 hours of WBL experience?",
    },
]

ORGANIZATION_DETAIL_COLUMN_TYPES = {
    **{field["name"]: "TEXT" for field in ORGANIZATION_TEXT_FIELDS},
    **{field["name"]: "BOOLEAN NOT NULL DEFAULT FALSE" for field in ORGANIZATION_CHECKBOX_FIELDS},
    "signature": "TEXT",
}


def get_database_settings():
    db_name = os.environ.get("DB")
    db_user = os.environ.get("DB_UN")
    db_password = os.environ.get("DB_PW")
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = int(os.environ.get("DB_PORT", "5434"))

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


def build_sqlalchemy_uri():
    settings = get_database_settings()
    if "database_uri" in settings:
        return settings["database_uri"]

    return (
        "postgresql://"
        f"{quote_plus(settings['user'])}:{quote_plus(settings['password'])}"
        f"@{settings['host']}:{settings['port']}/{settings['dbname']}"
    )


def get_db_connection():
    settings = get_database_settings()
    connect_options = {
        "connect_timeout": DB_CONNECT_TIMEOUT,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }

    if "database_uri" in settings:
        return psycopg2.connect(settings["database_uri"], **connect_options)

    return psycopg2.connect(
        dbname=settings["dbname"],
        user=settings["user"],
        password=settings["password"],
        host=settings["host"],
        port=settings["port"],
        **connect_options,
    )

def fetch_all_mentors():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.id,
                    CONCAT(m.first_name, ' ', m.last_name) AS mentor_name,
                    COALESCE(o.name, m.organization) AS organization_name
                FROM mentors m
                LEFT JOIN organizations o ON m.organization_id = o.id
                ORDER BY COALESCE(o.name, m.organization), m.first_name, m.last_name
                """
            )
            return cur.fetchall()
    finally:
        conn.close()

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "Internship 2026-OD")
app.config["SQLALCHEMY_DATABASE_URI"] = build_sqlalchemy_uri()
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": DB_POOL_RECYCLE_SECONDS,
    "pool_timeout": DB_POOL_TIMEOUT_SECONDS,
    "connect_args": {
        "connect_timeout": DB_CONNECT_TIMEOUT,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("EMAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("EMAIL_PASSWORD")

db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

def require_login():
    if "email" not in session:
        return redirect(url_for("login"))
    return None

def is_student_session():
    return not any(
        [
            session.get("is_admin"),
            session.get("is_teacher"),
            session.get("is_mentor"),
        ]
    )

def require_student():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    if not is_student_session():
        flash("That page is only available to students.", "warning")
        return redirect(url_for("home"))
    return None

def fetch_students(mentor_id=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if mentor_id is not None:
                cur.execute(
                    """
                    SELECT s.id, CONCAT(s.first_name, ' ', s.last_name) AS full_name
                    FROM students s
                    JOIN mentor_assignments ma ON ma.student_id = s.id
                    WHERE ma.mentor_id = %s
                    ORDER BY s.first_name, s.last_name
                    """,
                    (mentor_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, CONCAT(first_name, ' ', last_name) AS full_name
                    FROM students
                    ORDER BY first_name, last_name
                    """
                )
            return cur.fetchall()
    finally:
        conn.close()

def fetch_feedback_students():
    if session.get("is_admin"):
        return fetch_students()

    if session.get("is_mentor"):
        mentor_id = get_current_user_id()
        if mentor_id is None:
            return []
        return fetch_students(mentor_id=mentor_id)

    return []

def can_access_student(student_id):
    if session.get("is_admin"):
        return True

    if not session.get("is_mentor"):
        return False

    mentor_id = get_current_user_id()
    if mentor_id is None:
        return False

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM mentor_assignments
                WHERE mentor_id = %s
                  AND student_id = %s
                """,
                (mentor_id, student_id),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()

def fetch_feedback(mentor_id=None):
    conn = get_db_connection()
    try:
        with conn:
            ensure_feedback_schema(conn)
        with conn.cursor() as cur:
            if mentor_id is not None:
                cur.execute(
                    """
                    SELECT
                        f.id,
                        CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                        f.week,
                        f.description,
                        f.action_items,
                        f.focus_areas,
                        f.rating,
                        f.quality,
                        f.professionalism,
                        f.timeliness,
                        f.initiative,
                        f.softskills
                    FROM feedback f
                    JOIN students u ON f.student_id = u.id
                    JOIN mentor_assignments ma ON ma.student_id = u.id
                    WHERE ma.mentor_id = %s
                    ORDER BY f.week DESC, f.id DESC
                    """,
                    (mentor_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        f.id,
                        CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                        f.week,
                        f.description,
                        f.action_items,
                        f.focus_areas,
                        f.rating,
                        f.quality,
                        f.professionalism,
                        f.timeliness,
                        f.initiative,
                        f.softskills
                    FROM feedback f
                    JOIN students u ON f.student_id = u.id
                    ORDER BY f.week DESC, f.id DESC
                    """
                )
            return cur.fetchall()
    finally:
        conn.close()

def fetch_feedback_entry(feedback_id):
    conn = get_db_connection()
    try:
        with conn:
            ensure_feedback_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    student_id,
                    week,
                    description,
                    action_items,
                    focus_areas,
                    quality,
                    professionalism,
                    timeliness,
                    initiative,
                    softskills,
                    rating
                FROM feedback
                WHERE id = %s
                """,
                (feedback_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()

def fetch_student_hours_summary(student_id):
    conn = get_db_connection()
    try:
        with conn:
            ensure_progress_schema(conn)
            ensure_feedback_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH progress_totals AS (
                    SELECT
                        student_id,
                        COALESCE(SUM(CASE WHEN is_approved THEN hours_worked ELSE 0 END), 0) AS approved_hours,
                        COALESCE(SUM(CASE WHEN NOT is_approved AND NOT is_rejected THEN hours_worked ELSE 0 END), 0) AS pending_hours,
                        COUNT(id) AS days_logged
                    FROM progress_checks
                    GROUP BY student_id
                ),
                feedback_averages AS (
                    SELECT
                        student_id,
                        ROUND(AVG(quality)::numeric, 2) AS avg_quality,
                        ROUND(AVG(professionalism)::numeric, 2) AS avg_professionalism,
                        ROUND(AVG(timeliness)::numeric, 2) AS avg_timeliness,
                        ROUND(AVG(initiative)::numeric, 2) AS avg_initiative,
                        ROUND(AVG(softskills)::numeric, 2) AS avg_softskills,
                        ROUND(AVG(rating)::numeric, 2) AS total_average_rating
                    FROM feedback
                    GROUP BY student_id
                ),
                mentor_info AS (
                    SELECT
                        ma.student_id,
                        STRING_AGG(DISTINCT CONCAT(m.first_name, ' ', m.last_name), ', ') AS mentor_name,
                        STRING_AGG(DISTINCT COALESCE(o.name, m.organization), ', ') AS mentor_organization
                    FROM mentor_assignments ma
                    JOIN mentors m ON ma.mentor_id = m.id
                    LEFT JOIN organizations o ON m.organization_id = o.id
                    GROUP BY ma.student_id
                )
                SELECT
                    u.id,
                    CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                    u.email,
                    COALESCE(u.organization, '') AS organization,
                    COALESCE(pt.approved_hours, 0) AS total_hours,
                    COALESCE(pt.pending_hours, 0) AS pending_hours,
                    COALESCE(pt.days_logged, 0) AS days_logged,
                    COALESCE(mi.mentor_name, 'No mentor assigned') AS mentor_name,
                    COALESCE(mi.mentor_organization, '') AS mentor_organization,
                    fa.avg_quality,
                    fa.avg_professionalism,
                    fa.avg_timeliness,
                    fa.avg_initiative,
                    fa.avg_softskills,
                    fa.total_average_rating
                FROM students u
                LEFT JOIN progress_totals pt ON pt.student_id = u.id
                LEFT JOIN feedback_averages fa ON fa.student_id = u.id
                LEFT JOIN mentor_info mi ON mi.student_id = u.id
                WHERE u.id = %s
                """,
                (student_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()

def fetch_feedback_for_student(student_id):
    conn = get_db_connection()
    try:
        with conn:
            ensure_feedback_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    f.id,
                    CONCAT(u.first_name, ' ', u.last_name) AS student_name,
                    f.week,
                    f.description,
                    f.action_items,
                    f.focus_areas,
                    f.rating,
                    f.quality,
                    f.professionalism,
                    f.timeliness,
                    f.initiative,
                    f.softskills
                FROM feedback f
                JOIN students u ON f.student_id = u.id
                WHERE f.student_id = %s
                ORDER BY f.week DESC, f.id DESC
                """,
                (student_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()

def fetch_progress_checks(student_id):
    conn = get_db_connection()
    try:
        with conn:
            ensure_progress_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    day_worked,
                    hours_worked,
                    what_they_did,
                    mentor_questions,
                    reflection,
                    next_steps,
                    self_questions,
                    is_approved,
                    created_at,
                    is_rejected,
                    mentor_response
                FROM progress_checks
                WHERE student_id = %s
                ORDER BY day_worked DESC, created_at DESC
                """,
                (student_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()

def summarize_progress_data(progress_checks):
    daily_hours = {}
    for entry in progress_checks:
        id_val, day_worked, hours_worked, what_they_did, mentor_questions, reflection, next_steps, self_questions, is_approved, created_at, is_rejected, mentor_response = entry
        if not day_worked or not is_approved:
            continue
        daily_hours[day_worked] = daily_hours.get(day_worked, 0) + float(hours_worked)

    events = []
    weekly = {}
    monthly = {}

    for day_worked, hours in daily_hours.items():
        events.append(
            {
                "title": f"{round(hours, 1)}h",
                "start": day_worked.isoformat(),
                "allDay": True,
            }
        )
        year, week_number, _ = day_worked.isocalendar()
        weekly[(year, week_number)] = weekly.get((year, week_number), 0) + hours
        monthly[(day_worked.year, day_worked.month)] = monthly.get((day_worked.year, day_worked.month), 0) + hours

    weekly_totals = [
        {
            "label": f"{year}-W{week_number:02d}",
            "hours": round(total, 1),
        }
        for (year, week_number), total in sorted(weekly.items())
    ]
    monthly_totals = [
        {
            "label": f"{year}-{datetime(year, month, 1).strftime('%B')}",
            "hours": round(total, 1),
        }
        for (year, month), total in sorted(monthly.items())
    ]

    return events, weekly_totals, monthly_totals
def parse_organization_details():
    details = {}

    for field in ORGANIZATION_TEXT_FIELDS:
        details[field["name"]] = request.form.get(field["name"], "").strip()

    for field in ORGANIZATION_CHECKBOX_FIELDS:
        details[field["name"]] = request.form.get(field["name"]) == "on"

    details["signature"] = request.form.get("signature", "").strip()
    return details

def ensure_organization_detail_columns(conn):
    with conn.cursor() as cur:
        for column_name, column_type in ORGANIZATION_DETAIL_COLUMN_TYPES.items():
            cur.execute(f"ALTER TABLE organizations ADD COLUMN IF NOT EXISTS {column_name} {column_type}")

def ensure_progress_schema(conn):
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE progress_checks ADD COLUMN IF NOT EXISTS is_approved BOOLEAN NOT NULL DEFAULT FALSE")
        cur.execute("ALTER TABLE progress_checks ADD COLUMN IF NOT EXISTS is_rejected BOOLEAN NOT NULL DEFAULT FALSE")
        cur.execute("ALTER TABLE progress_checks ADD COLUMN IF NOT EXISTS mentor_response TEXT")

def ensure_feedback_schema(conn):
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS mentor_id BIGINT")
        cur.execute("ALTER TABLE feedback ALTER COLUMN mentor_id DROP NOT NULL")
        cur.execute("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS action_items TEXT")
        cur.execute("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS focus_areas TEXT")
        cur.execute("ALTER TABLE feedback ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")

def organization_details_from_row(row):
    return {
        column_name: row[index + 2]
        for index, column_name in enumerate(ORGANIZATION_DETAIL_COLUMN_TYPES)
    }

def fetch_organizations():
    conn = get_db_connection()
    try:
        with conn:
            ensure_organization_detail_columns(conn)
        with conn.cursor() as cur:
            detail_columns = ", ".join(ORGANIZATION_DETAIL_COLUMN_TYPES)
            cur.execute(
                f"""
                SELECT id, name, {detail_columns}
                FROM organizations
                ORDER BY name
                """
            )
            return [
                (organization[0], organization[1], organization_details_from_row(organization))
                for organization in cur.fetchall()
            ]
    finally:
        conn.close()


def fetch_mentors():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, CONCAT(first_name, ' ', last_name) AS full_name
                FROM mentors
                ORDER BY first_name, last_name
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def fetch_student_entry(student_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.id,
                    s.email,
                    s.first_name,
                    s.last_name,
                    s.organization,
                    ma.mentor_id
                FROM students s
                LEFT JOIN mentor_assignments ma ON ma.student_id = s.id
                WHERE s.id = %s
                """,
                (student_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "email": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "organization": row[4],
                "mentor_id": row[5],
            }
    finally:
        conn.close()


def fetch_mentor_entry(mentor_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, first_name, last_name, organization, organization_id
                FROM mentors
                WHERE id = %s
                """,
                (mentor_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "email": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "organization": row[4],
                "organization_id": row[5],
            }
    finally:
        conn.close()


def fetch_students_for_mentor(mentor_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.id, CONCAT(s.first_name, ' ', s.last_name) AS full_name
                FROM students s
                JOIN mentor_assignments ma ON ma.student_id = s.id
                WHERE ma.mentor_id = %s
                ORDER BY s.first_name, s.last_name
                """,
                (mentor_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def is_email_available(email, current_role=None, current_id=None):
    account, role = find_account_by_email(email)
    if account is None:
        return True
    if role == current_role and account.id == current_id:
        return True
    return False


def fetch_organization_entry(organization_id):
    conn = get_db_connection()
    try:
        with conn:
            ensure_organization_detail_columns(conn)
        with conn.cursor() as cur:
            detail_columns = ", ".join(ORGANIZATION_DETAIL_COLUMN_TYPES)
            cur.execute(
                f"SELECT id, name, {detail_columns} FROM organizations WHERE id = %s",
                (organization_id,),
            )
            organization = cur.fetchone()
            if organization is None:
                return None
            return organization[0], organization[1], organization_details_from_row(organization)
    finally:
        conn.close()

def fetch_organization_name(organization_id):
    if organization_id is None:
        return None

    organization = fetch_organization_entry(organization_id)
    return organization[1] if organization else None

def fetch_mentors_by_organization(organization_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, CONCAT(first_name, ' ', last_name) AS full_name
                FROM mentors
                WHERE organization_id = %s
                ORDER BY first_name, last_name
                """,
                (organization_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()

def find_account_by_email(email):
    student = Student.query.filter_by(email=email).first()
    if student:
        return student, "student"

    mentor = Mentor.query.filter_by(email=email).first()
    if mentor:
        return mentor, "mentor"

    admin = Admin.query.filter_by(email=email).first()
    if admin:
        return admin, "admin"

    return None, None

def account_exists(email):
    account, _ = find_account_by_email(email)
    return account is not None

def get_current_user_id():
    email = session.get("email")
    if not email:
        return None
    user, _ = find_account_by_email(email)
    return user.id if user else None

def validate_progress_check_form():
    day_worked = request.form.get("day_worked", "").strip()
    hours_worked = request.form.get("hours_worked", "").strip()
    minutes_worked = request.form.get("minutes_worked", "").strip()
    what_they_did = request.form.get("what_they_did", "").strip()
    mentor_questions = request.form.get("mentor_questions", "").strip()
    reflection = request.form.get("reflection", "").strip()
    next_steps = request.form.get("next_steps", "").strip()
    self_questions = request.form.get("self_questions", "").strip()

    if not day_worked:
        raise ValueError("Day worked is required.")
    if not hours_worked:
        raise ValueError("Hours worked is required.")
    if minutes_worked is None or minutes_worked == "":
        raise ValueError("Minutes worked is required.")
    if not what_they_did:
        raise ValueError("Please describe what you did.")

    try:
        hours_value = int(hours_worked)
        minutes_value = int(minutes_worked)
    except ValueError as exc:
        raise ValueError("Hours and minutes must be valid numbers.") from exc

    total_hours = hours_value + (minutes_value / 60)

    if total_hours < 0 or total_hours > 24:
        raise ValueError("Total hours worked must be between 0 and 24.")

    return {
        "day_worked": day_worked,
        "hours_worked": round(total_hours, 2),
        "what_they_did": what_they_did,
        "mentor_questions": mentor_questions,
        "reflection": reflection,
        "next_steps": next_steps,
        "self_questions": self_questions,
    }

def parse_score(field_name):
    raw_value = request.form.get(field_name, "").strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        label = field_name.replace("_", " ")
        raise ValueError(f"{label} must be a whole number.") from exc

    if value < 1 or value > 5:
        label = field_name.replace("_", " ")
        raise ValueError(f"{label} must be between 1 and 5.")
    return value

def validate_feedback_form():
    student_id = request.form.get("student", "").strip()
    week = request.form.get("week", "").strip()
    description = request.form.get("description", "").strip()
    action_items = request.form.get("action_items", "").strip()
    focus_areas = request.form.get("focus_areas", "").strip()

    if not student_id:
        raise ValueError("Student is required.")
    if not week:
        raise ValueError("Week is required.")
    if not description:
        raise ValueError("Feedback description is required.")

    try:
        student_id_value = int(student_id)
        week_value = int(week)
    except ValueError as exc:
        raise ValueError("Student and week must be valid numbers.") from exc

    if week_value < 1 or week_value > 52:
        raise ValueError("Week must be between 1 and 52.")

    quality = parse_score("Quality_of_Work")
    professionalism = parse_score("Professionalism")
    timeliness = parse_score("Timeliness_of_Work")
    initiative = parse_score("Initiative")
    softskills = parse_score("Soft_Skills")
    rating = round((quality + professionalism + timeliness + initiative + softskills) / 5)

    return {
        "student_id": student_id_value,
        "week": week_value,
        "description": description,
        "action_items": action_items or None,
        "focus_areas": focus_areas or None,
        "quality": quality,
        "professionalism": professionalism,
        "timeliness": timeliness,
        "initiative": initiative,
        "softskills": softskills,
        "rating": rating,
    }

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="email-confirm-salt")

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt="email-confirm-salt", max_age=expiration)
    except Exception:
        return False

def send_confirmation_email(user_email):
    token = generate_confirmation_token(user_email)
    confirm_url = url_for("confirm_email", token=token, _external=True)
    html = render_template("confirm_email.html", confirm_url=confirm_url)
    msg = Message(
        "Confirm Your Registration",
        sender=app.config["MAIL_USERNAME"],
        recipients=[user_email],
    )
    msg.html = html
    mail.send(msg)

def notify_mentor_of_question(student_id, day_worked, question):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.email, CONCAT(s.first_name, ' ', s.last_name)
                FROM students s
                JOIN mentor_assignments ma ON ma.student_id = s.id
                JOIN mentors m ON m.id = ma.mentor_id
                WHERE s.id = %s
                """,
                (student_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or not row[0]:
        return

    mentor_email, student_name = row
    try:
        msg = Message(
            "A student left you a question",
            sender=app.config["MAIL_USERNAME"],
            recipients=[mentor_email],
        )
        msg.html = render_template(
            "question_email.html",
            student_name=student_name,
            day_worked=day_worked,
            question=question,
        )
        mail.send(msg)
    except Exception:
        pass

def notify_student_of_response(student_email, student_name, day_worked, response):
    if not student_email:
        return
    try:
        msg = Message(
            "Your mentor responded to your worklog",
            sender=app.config["MAIL_USERNAME"],
            recipients=[student_email],
        )
        msg.html = render_template(
            "response_email.html",
            student_name=student_name,
            day_worked=day_worked,
            response=response,
        )
        mail.send(msg)
    except Exception:
        pass

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/intr/", methods=["GET", "POST"])
def login():
    if session.get("email"):
        return redirect(url_for("home"))

    form = LoginForm()

    if request.method == "POST" and form.validate_on_submit():
        user, role = find_account_by_email(form.email.data)

        if not user:
            flash("Email does not exist.", "danger")
            return redirect(url_for("login"))

        if not bcrypt.check_password_hash(user.password, form.password.data):
            flash("Incorrect password.", "danger")
            return redirect(url_for("login"))

        session["email"] = user.email
        session["organization"] = fetch_organization_name(user.organization_id) or user.organization
        session["is_admin"] = role == "admin"
        session["is_teacher"] = False
        session["is_mentor"] = role == "mentor"

        return redirect(url_for("home"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/intr/home")
def home():
    student_hours = None
    if session.get("is_student"):
        student_id = get_current_user_id()
        if student_id:
            student_summary = fetch_student_hours_summary(student_id)
            if student_summary:
                student_hours = {
                    "approved_hours": student_summary[4],
                    "pending_hours": student_summary[5],
                }
    
    return render_template("home.html", student_hours=student_hours, session = session)

@app.route("/intr/about")
def about():
    return render_template("about.html")

@app.route("/intr/mentor/hours", methods=["GET"])
def mentor_hours():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor"):
        flash("This page is only available to mentors.", "warning")
        return redirect(url_for("home"))

    mentor_id = get_current_user_id()
    if mentor_id is None:
        flash("Unable to identify current mentor.", "danger")
        return redirect(url_for("home"))

    # Fetch students assigned to this mentor
    students = fetch_students_for_mentor(mentor_id)
    
    selected_student_id = request.args.get("student_id", "").strip()
    selected_student = None
    selected_progress_checks = []
    selected_progress_events = []
    weekly_totals = []
    monthly_totals = []

    if selected_student_id:
        try:
            student_id_value = int(selected_student_id)
        except ValueError:
            flash("Please select a valid student.", "danger")
        else:
            # Verify that this student is assigned to this mentor
            student_assigned = False
            for student in students:
                if student[0] == student_id_value:
                    student_assigned = True
                    break
            
            if not student_assigned:
                flash("You don't have access to this student's hours.", "danger")
            else:
                selected_progress_checks = fetch_progress_checks(student_id_value)
                selected_student = fetch_student_entry(student_id_value)
                selected_progress_events, weekly_totals, monthly_totals = summarize_progress_data(
                    selected_progress_checks
                )

    return render_template(
        "mentor_hours.html",
        students=students,
        selected_student_id=selected_student_id,
        selected_student=selected_student,
        selected_progress_checks=selected_progress_checks,
        selected_progress_events=selected_progress_events,
        selected_progress_events_json=json.dumps(selected_progress_events),
        weekly_totals=weekly_totals,
        monthly_totals=monthly_totals,
    )

@app.route("/intr/mentor/hours/<int:progress_id>/approve", methods=["POST"])
def approve_hours(progress_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor"):
        flash("Only mentors can approve hours.", "warning")
        return redirect(url_for("home"))

    mentor_id = get_current_user_id()
    
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Check if this progress check exists and belongs to a student assigned to this mentor
                cur.execute(
                    """
                    SELECT pc.id, pc.student_id 
                    FROM progress_checks pc
                    JOIN mentor_assignments ma ON pc.student_id = ma.student_id
                    WHERE pc.id = %s AND ma.mentor_id = %s
                    """,
                    (progress_id, mentor_id),
                )
                result = cur.fetchone()
                
                if result is None:
                    flash("You don't have permission to approve this entry.", "danger")
                else:
                    student_id = result[1]
                    cur.execute(
                        "UPDATE progress_checks SET is_approved = TRUE, is_rejected = FALSE WHERE id = %s",
                        (progress_id,),
                    )
                    flash("Hours approved.", "success")
        return redirect(url_for("mentor_hours", student_id=student_id))
    finally:
        conn.close()

@app.route("/intr/mentor/hours/<int:progress_id>/reject", methods=["POST"])
def reject_hours(progress_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor"):
        flash("Only mentors can reject hours.", "warning")
        return redirect(url_for("home"))

    mentor_id = get_current_user_id()
    
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Check if this progress check exists and belongs to a student assigned to this mentor
                cur.execute(
                    """
                    SELECT pc.id, pc.student_id 
                    FROM progress_checks pc
                    JOIN mentor_assignments ma ON pc.student_id = ma.student_id
                    WHERE pc.id = %s AND ma.mentor_id = %s
                    """,
                    (progress_id, mentor_id),
                )
                result = cur.fetchone()
                
                if result is None:
                    flash("You don't have permission to reject this entry.", "danger")
                else:
                    student_id = result[1]
                    cur.execute(
                        "UPDATE progress_checks SET is_approved = FALSE, is_rejected = TRUE WHERE id = %s",
                        (progress_id,),
                    )
                    flash("Hours rejected.", "success")
        return redirect(url_for("mentor_hours", student_id=student_id))
    finally:
        conn.close()

@app.route("/intr/mentor/hours/<int:progress_id>/respond", methods=["POST"])
def respond_hours(progress_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor"):
        flash("Only mentors can respond to worklogs.", "warning")
        return redirect(url_for("home"))

    mentor_id = get_current_user_id()
    response = request.form.get("mentor_response", "").strip()

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pc.student_id, s.email, CONCAT(s.first_name, ' ', s.last_name),
                           pc.day_worked, pc.mentor_response
                    FROM progress_checks pc
                    JOIN mentor_assignments ma ON pc.student_id = ma.student_id
                    JOIN students s ON s.id = pc.student_id
                    WHERE pc.id = %s AND ma.mentor_id = %s
                    """,
                    (progress_id, mentor_id),
                )
                result = cur.fetchone()
                if result is None:
                    flash("You don't have permission to respond to this entry.", "danger")
                    return redirect(url_for("mentor_hours"))
                student_id, student_email, student_name, day_worked, previous_response = result
                cur.execute(
                    "UPDATE progress_checks SET mentor_response = %s WHERE id = %s",
                    (response or None, progress_id),
                )
                flash("Response saved.", "success")
        if response and response != (previous_response or ""):
            notify_student_of_response(student_email, student_name, day_worked, response)
        return redirect(url_for("mentor_hours", student_id=student_id))
    finally:
        conn.close()

@app.route("/intr/admin", methods=["GET", "POST"])
def admin():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    if request.method == "POST":
        organization_name = request.form.get("organization_name", "").strip()
        organization_details = parse_organization_details()

        if not organization_name:
            flash("Organization name is required.", "danger")
            return redirect(url_for("admin"))

        conn = get_db_connection()
        try:
            with conn:
                ensure_organization_detail_columns(conn)
                with conn.cursor() as cur:
                    detail_columns = list(ORGANIZATION_DETAIL_COLUMN_TYPES)
                    columns = ", ".join(["name", *detail_columns])
                    placeholders = ", ".join(["%s"] * (len(detail_columns) + 1))
                    cur.execute("SELECT 1 FROM organizations WHERE name = %s", (organization_name,))
                    inserted = cur.fetchone() is None
                    if inserted:
                        cur.execute(
                            f"INSERT INTO organizations ({columns}) VALUES ({placeholders})",
                            (organization_name, *[organization_details[column] for column in detail_columns]),
                        )
            if inserted:
                flash("Organization added.", "success")
            else:
                flash("Organization already exists.", "warning")
        finally:
            conn.close()

        return redirect(url_for("admin"))

    students = fetch_students()
    organizations = fetch_organizations()
    mentors = fetch_mentors()
    admins = [
        (admin.id, f"{admin.first_name} {admin.last_name}")
        for admin in Admin.query.order_by(Admin.first_name, Admin.last_name).all()
    ]
    selected_student_id = request.args.get("student_id", "").strip()
    selected_mentor_id = request.args.get("mentor_id", "").strip()
    selected_admin_id = request.args.get("admin_id", "").strip()
    selected_student = None
    selected_feedback = []
    selected_progress_events = []
    weekly_totals = []
    monthly_totals = []
    selected_mentor = None
    selected_mentor_students = []
    selected_admin = None

    if selected_student_id:
        try:
            student_id_value = int(selected_student_id)
        except ValueError:
            flash("Please select a valid student.", "danger")
        else:
            selected_student = fetch_student_hours_summary(student_id_value)
            selected_feedback = fetch_feedback_for_student(student_id_value)
            selected_progress_events = []
            weekly_totals = []
            monthly_totals = []

            if selected_student is not None:
                progress_checks = fetch_progress_checks(student_id_value)
                selected_progress_events, weekly_totals, monthly_totals = summarize_progress_data(
                    progress_checks
                )

            if selected_student is None:
                flash("Student not found.", "warning")

    if selected_mentor_id:
        try:
            mentor_id_value = int(selected_mentor_id)
        except ValueError:
            flash("Please select a valid mentor.", "danger")
        else:
            selected_mentor = fetch_mentor_entry(mentor_id_value)
            if selected_mentor is None:
                flash("Mentor not found.", "warning")
            else:
                selected_mentor_students = fetch_students_for_mentor(mentor_id_value)

    if selected_admin_id:
        try:
            admin_id_value = int(selected_admin_id)
        except ValueError:
            flash("Please select a valid admin.", "danger")
        else:
            selected_admin = Admin.query.get(admin_id_value)
            if selected_admin is None:
                flash("Admin not found.", "warning")

    return render_template(
        "admin.html",
        students=students,
        mentors=mentors,
        admins=admins,
        selected_student_id=selected_student_id,
        selected_student=selected_student,
        selected_feedback=selected_feedback,
        selected_progress_events=selected_progress_events,
        selected_progress_events_json=json.dumps(selected_progress_events),
        weekly_totals=weekly_totals,
        monthly_totals=monthly_totals,
        selected_mentor_id=selected_mentor_id,
        selected_mentor=selected_mentor,
        selected_mentor_students=selected_mentor_students,
        selected_admin_id=selected_admin_id,
        selected_admin=selected_admin,
        organizations=organizations,
        organization_text_fields=ORGANIZATION_TEXT_FIELDS,
        organization_checkbox_fields=ORGANIZATION_CHECKBOX_FIELDS,
    )

@app.route("/intr/admin/admins/<int:id>/edit", methods=["GET", "POST"])
def editAdmin(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("admin"))

    admin_user = Admin.query.get(id)
    if admin_user is None:
        flash("Admin account not found.", "warning")
        return redirect(url_for("admin"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()

        if not email or not first_name or not last_name:
            flash("Email, first name, and last name are required.", "danger")
            return render_template("editadmin.html", admin=admin_user)

        if not is_email_available(email, current_role="admin", current_id=admin_user.id):
            flash("That email is already in use.", "danger")
            return render_template("editadmin.html", admin=admin_user)

        admin_user.email = email
        admin_user.first_name = first_name
        admin_user.last_name = last_name
        db.session.commit()
        if get_current_user_id() == admin_user.id:
            session["email"] = email
        flash("Admin profile updated.", "success")
        return redirect(url_for("admin", admin_id=admin_user.id))

    return render_template("editadmin.html", admin=admin_user)

@app.route("/intr/admin/admins/<int:id>/delete", methods=["POST"])
def deleteAdmin(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    admin_user = Admin.query.get(id)
    if admin_user is None:
        flash("Admin account not found.", "warning")
        return redirect(url_for("admin"))

    db.session.delete(admin_user)
    db.session.commit()
    flash("Admin account deleted.", "success")
    return redirect(url_for("admin"))

@app.route("/intr/admin/organizations/<int:id>/edit", methods=["GET", "POST"])
def editOrganization(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    organization = fetch_organization_entry(id)
    if organization is None:
        flash("Organization not found.", "warning")
        return redirect(url_for("admin"))

    if request.method == "POST":
        organization_name = request.form.get("organization_name", "").strip()
        organization_details = parse_organization_details()

        if not organization_name:
            flash("Organization name is required.", "danger")
            return render_template(
                "editorganization.html",
                organization=organization,
                organization_details=organization_details,
                organization_text_fields=ORGANIZATION_TEXT_FIELDS,
                organization_checkbox_fields=ORGANIZATION_CHECKBOX_FIELDS,
            )

        conn = get_db_connection()
        try:
            with conn:
                ensure_organization_detail_columns(conn)
                with conn.cursor() as cur:
                    detail_columns = list(ORGANIZATION_DETAIL_COLUMN_TYPES)
                    detail_updates = ", ".join(f"{column} = %s" for column in detail_columns)
                    cur.execute(
                        f"UPDATE organizations SET name = %s, {detail_updates} WHERE id = %s",
                        (
                            organization_name,
                            *[organization_details[column] for column in detail_columns],
                            id,
                        ),
                    )
                    cur.execute(
                        "UPDATE students SET organization = %s WHERE organization = %s",
                        (organization_name, organization[1]),
                    )
                    cur.execute(
                        "UPDATE mentors SET organization = %s WHERE organization = %s",
                        (organization_name, organization[1]),
                    )
                    cur.execute(
                        "UPDATE admins SET organization = %s WHERE organization = %s",
                        (organization_name, organization[1]),
                    )
                    cur.execute(
                        "UPDATE pending_users SET organization = %s WHERE organization = %s",
                        (organization_name, organization[1]),
                    )
        except psycopg2.IntegrityError:
            flash("Organization already exists.", "danger")
            return render_template(
                "editorganization.html",
                organization=organization,
                organization_details=organization_details,
                organization_text_fields=ORGANIZATION_TEXT_FIELDS,
                organization_checkbox_fields=ORGANIZATION_CHECKBOX_FIELDS,
            )
        finally:
            conn.close()

        flash("Organization updated.", "success")
        return redirect(url_for("admin"))

    return render_template(
        "editorganization.html",
        organization=organization,
        organization_details=organization[2] or {},
        organization_text_fields=ORGANIZATION_TEXT_FIELDS,
        organization_checkbox_fields=ORGANIZATION_CHECKBOX_FIELDS,
    )

@app.route("/intr/admin/students/<int:id>/edit", methods=["GET", "POST"])
def editStudent(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    student = fetch_student_entry(id)
    if student is None:
        flash("Student not found.", "warning")
        return redirect(url_for("admin"))

    mentors = fetch_mentors()
    selected_mentor_id = student["mentor_id"]

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        mentor_id_raw = request.form.get("mentor_id", "").strip()

        if not email or not first_name or not last_name:
            flash("Email, first name, and last name are required.", "danger")
            return render_template(
                "editstudent.html",
                student=student,
                mentors=mentors,
                selected_mentor_id=selected_mentor_id,
            )

        if not is_email_available(email, current_role="student", current_id=id):
            flash("That email is already in use.", "danger")
            return render_template(
                "editstudent.html",
                student=student,
                mentors=mentors,
                selected_mentor_id=selected_mentor_id,
            )

        mentor_id = None
        if mentor_id_raw:
            try:
                mentor_id = int(mentor_id_raw)
            except ValueError:
                flash("Please select a valid mentor.", "danger")
                return render_template(
                    "editstudent.html",
                    student=student,
                    mentors=mentors,
                    selected_mentor_id=selected_mentor_id,
                )

        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE students SET email = %s, first_name = %s, last_name = %s WHERE id = %s",
                        (email, first_name, last_name, id),
                    )
                    if mentor_id is None:
                        cur.execute("DELETE FROM mentor_assignments WHERE student_id = %s", (id,))
                    else:
                        cur.execute(
                            "INSERT INTO mentor_assignments (student_id, mentor_id) VALUES (%s, %s) ON CONFLICT (student_id) DO UPDATE SET mentor_id = EXCLUDED.mentor_id",
                            (id, mentor_id),
                        )
            flash("Student updated.", "success")
            return redirect(url_for("admin", student_id=id))
        finally:
            conn.close()

    return render_template(
        "editstudent.html",
        student=student,
        mentors=mentors,
        selected_mentor_id=selected_mentor_id,
    )


@app.route("/intr/admin/students/<int:id>/delete", methods=["POST"])
def deleteStudent(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM students WHERE id = %s", (id,))
                deleted = cur.rowcount
    finally:
        conn.close()

    flash("Student deleted." if deleted else "Student not found.", "success" if deleted else "warning")
    return redirect(url_for("admin"))


@app.route("/intr/admin/mentors/<int:id>/edit", methods=["GET", "POST"])
def editMentor(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    mentor = fetch_mentor_entry(id)
    if mentor is None:
        flash("Mentor not found.", "warning")
        return redirect(url_for("admin"))

    assigned_students = fetch_students_for_mentor(id)
    organizations = fetch_organizations()

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        organization_id_raw = request.form.get("organization_id", "").strip()

        if not email or not first_name or not last_name:
            flash("Email, first name, and last name are required.", "danger")
            return render_template(
                "editmentor.html",
                mentor=mentor,
                assigned_students=assigned_students,
                organizations=organizations,
            )

        if not is_email_available(email, current_role="mentor", current_id=id):
            flash("That email is already in use.", "danger")
            return render_template(
                "editmentor.html",
                mentor=mentor,
                assigned_students=assigned_students,
                organizations=organizations,
            )

        organization_id = None
        organization_name = None
        if organization_id_raw:
            try:
                organization_id = int(organization_id_raw)
            except ValueError:
                flash("Please select a valid organization.", "danger")
                return render_template(
                    "editmentor.html",
                    mentor=mentor,
                    assigned_students=assigned_students,
                    organizations=organizations,
                )
            organization = fetch_organization_entry(organization_id)
            if organization is None:
                flash("Please select a valid organization.", "danger")
                return render_template(
                    "editmentor.html",
                    mentor=mentor,
                    assigned_students=assigned_students,
                    organizations=organizations,
                )
            organization_name = organization[1]

        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE mentors SET email = %s, first_name = %s, last_name = %s, organization = %s, organization_id = %s WHERE id = %s",
                        (email, first_name, last_name, organization_name, organization_id, id),
                    )
            flash("Mentor updated.", "success")
            return redirect(url_for("admin", mentor_id=id))
        finally:
            conn.close()

    return render_template(
        "editmentor.html",
        mentor=mentor,
        assigned_students=assigned_students,
        organizations=organizations,
    )

@app.route("/intr/admin/mentors/<int:id>/delete", methods=["POST"])
def deleteMentor(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE feedback SET mentor_id = NULL WHERE mentor_id = %s", (id,))
                cur.execute("DELETE FROM mentors WHERE id = %s", (id,))
                deleted = cur.rowcount
    finally:
        conn.close()

    flash("Mentor deleted." if deleted else "Mentor not found.", "success" if deleted else "warning")
    return redirect(url_for("admin"))

@app.route("/intr/admin/mentors/<int:mentor_id>/assign-student", methods=["POST"])
def assignStudentToMentor(mentor_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    student_id_raw = request.form.get("student_id", "").strip()
    if not student_id_raw:
        flash("Please select a student to assign.", "warning")
        return redirect(url_for("admin", mentor_id=mentor_id))

    try:
        student_id = int(student_id_raw)
    except ValueError:
        flash("Please select a valid student.", "danger")
        return redirect(url_for("admin", mentor_id=mentor_id))

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO mentor_assignments (student_id, mentor_id) VALUES (%s, %s) ON CONFLICT (student_id) DO UPDATE SET mentor_id = EXCLUDED.mentor_id",
                    (student_id, mentor_id),
                )
        flash("Mentor assignment updated.", "success")
    finally:
        conn.close()

    return redirect(url_for("admin", mentor_id=mentor_id))

@app.route("/intr/admin/organizations/<int:id>/delete", methods=["POST"])
def deleteOrganization(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_admin"):
        return redirect(url_for("home"))

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                organization = fetch_organization_entry(id)
                if organization is not None:
                    cur.execute(
                        "UPDATE students SET organization = NULL, organization_id = NULL WHERE organization_id = %s OR organization = %s",
                        (id, organization[1]),
                    )
                    cur.execute(
                        "UPDATE mentors SET organization = NULL, organization_id = NULL WHERE organization_id = %s OR organization = %s",
                        (id, organization[1]),
                    )
                    cur.execute(
                        "UPDATE admins SET organization = NULL, organization_id = NULL WHERE organization_id = %s OR organization = %s",
                        (id, organization[1]),
                    )
                    cur.execute(
                        "UPDATE pending_users SET organization = NULL, organization_id = NULL WHERE organization_id = %s OR organization = %s",
                        (id, organization[1]),
                    )
                cur.execute("DELETE FROM organizations WHERE id = %s", (id,))
                deleted = cur.rowcount
    finally:
        conn.close()

    if deleted:
        flash("Organization deleted.", "success")
    else:
        flash("Organization not found.", "warning")
    return redirect(url_for("admin"))


@app.route("/intr/registration-pending")
def registration_pending():
    return render_template("registration_pending.html")




@app.route("/intr/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    organizations = fetch_organizations()
    mentors = fetch_all_mentors()

    if request.method == "POST" and form.validate_on_submit():
        selected_role = request.form.get("role", "").strip()
        selected_organization_id = request.form.get("organization", "").strip()
        selected_mentor_id = request.form.get("mentor_id", "").strip()
        security_code = form.security_code.data.strip() if form.security_code.data else ""

        if selected_role not in ["student", "mentor", "admin"]:
            flash("Please select Student, Mentor, or Admin.", "danger")
            return render_template("register.html", form=form, organizations=organizations, mentors=mentors)

        organization_id_value = None
        selected_organization = None

        if selected_role == "student":
            if not selected_mentor_id:
                flash("Students must select a mentor.", "danger")
                return render_template("register.html", form=form, organizations=organizations, mentors=mentors)

        elif selected_role == "mentor":
            if not selected_organization_id:
                flash("Mentors must select an organization.", "danger")
                return render_template("register.html", form=form, organizations=organizations, mentors=mentors)

            try:
                organization_id_value = int(selected_organization_id)
            except ValueError:
                flash("Please select a valid organization.", "danger")
                return render_template("register.html", form=form, organizations=organizations, mentors=mentors)

            selected_organization = fetch_organization_entry(organization_id_value)
            if selected_organization is None:
                flash("Please select a valid organization.", "danger")
                return render_template("register.html", form=form, organizations=organizations, mentors=mentors)

            if security_code != os.environ.get("MENTOR_CODE"):
                flash("Invalid mentor security code.", "danger")
                return render_template("register.html", form=form, organizations=organizations, mentors=mentors)

        elif selected_role == "admin":
            if security_code != os.environ.get("ADMIN_CODE"):
                flash("Invalid admin security code.", "danger")
                return render_template("register.html", form=form, organizations=organizations, mentors=mentors)

        if account_exists(form.email.data):
            flash("Email already in use.", "danger")
            return redirect(url_for("register"))

        existing_pending = PendingUser.query.filter_by(email=form.email.data).first()
        if existing_pending:
            db.session.delete(existing_pending)
            db.session.commit()

        if profanity.contains_profanity(form.first_name.data) or profanity.contains_profanity(form.last_name.data):
            flash("No profanity allowed.", "danger")
            return redirect(url_for("register"))

        if len(form.password.data) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("register"))

        if form.password.data != form.confirmPassword.data:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        pending_user = PendingUser(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            password=bcrypt.generate_password_hash(form.password.data).decode("utf-8"),
            organization=selected_organization[1] if selected_organization else None,
            organization_id=organization_id_value,
            role=selected_role,
            requested_mentor_id=int(selected_mentor_id) if selected_role == "student" else None,
        )

        db.session.add(pending_user)
        db.session.commit()

        send_confirmation_email(form.email.data)
        flash("A confirmation email has been sent.", "info")
        return redirect(url_for("registration_pending"))

    return render_template(
        "register.html",
        form=form,
        organizations=organizations,
        mentors=mentors,
    )

def compute_student_averages(feedback):
    groups = {}
    for row in feedback:
        groups.setdefault(row[1], []).append(row)

    def average(rows, index):
        return round(sum(float(r[index]) for r in rows) / len(rows), 2)

    return {
        name: {
            "quality": average(rows, 7),
            "professionalism": average(rows, 8),
            "timeliness": average(rows, 9),
            "initiative": average(rows, 10),
            "softskills": average(rows, 11),
            "overall": average(rows, 6),
        }
        for name, rows in groups.items()
    }

@app.route("/intr/feedback")
def feedbackPage():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor") and not session.get("is_admin"):
        flash("That page is only available to mentors, admins, or presenter view.", "warning")
        return redirect(url_for("home"))

    if session.get("is_admin"):
        return redirect(url_for("admin"))

    try:
        mentor_id = get_current_user_id() if session.get("is_mentor") else None
        feedback = fetch_feedback(mentor_id=mentor_id)
    except psycopg2.Error:
        flash("Feedback data could not be loaded. Run initdb.py to create the tables.", "danger")
        feedback = []

    return render_template(
        "feedbackpage.html",
        feedback=feedback,
        students_to_filter=sorted({f[1] for f in feedback}),
        weeks_to_filter=sorted({f[2] for f in feedback}),
        student_averages=compute_student_averages(feedback),
    )

@app.route("/intr/student-feedback")
def studentFeedback():
    login_redirect = require_student()
    if login_redirect:
        return login_redirect

    user_id = get_current_user_id()
    if user_id is None:
        flash("Unable to locate your account.", "danger")
        return redirect(url_for("home"))

    feedback = fetch_feedback_for_student(user_id)
    return render_template("student_feedback.html", feedback=feedback)

@app.route("/intr/feedback/submit", methods=["GET", "POST"])
def submitFeedback():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor") and not session.get("is_admin"):
        flash("That page is only available to mentors, admins, or presenter view.", "warning")
        return redirect(url_for("home"))

    try:
        students = fetch_feedback_students()
    except psycopg2.Error:
        flash("Student list could not be loaded. Run initdb.py to create the tables.", "danger")
        return redirect(url_for("feedbackPage"))

    if request.method == "POST":
        try:
            payload = validate_feedback_form()
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("feedbackform.html", students=students)

        if not can_access_student(payload["student_id"]):
            flash("You can only submit feedback for assigned students.", "danger")
            return render_template("feedbackform.html", students=students)

        current_user_id = get_current_user_id()
        if current_user_id is None:
            flash("You must be logged in as a valid user to submit feedback.", "danger")
            return redirect(url_for("login"))

        mentor_id = current_user_id if session.get("is_mentor") else None
        conn = get_db_connection()
        try:
            with conn:
                ensure_feedback_schema(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO feedback
                        (
                            student_id,
                            mentor_id,
                            week,
                            description,
                            action_items,
                            focus_areas,
                            quality,
                            professionalism,
                            timeliness,
                            initiative,
                            softskills,
                            rating
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            payload["student_id"],
                            mentor_id,
                            payload["week"],
                            payload["description"],
                            payload["action_items"],
                            payload["focus_areas"],
                            payload["quality"],
                            payload["professionalism"],
                            payload["timeliness"],
                            payload["initiative"],
                            payload["softskills"],
                            payload["rating"],
                        ),
                    )
        finally:
            conn.close()

        flash("Feedback submitted.", "success")
        return redirect(url_for("feedbackPage"))

    return render_template("feedbackform.html", students=students)

@app.route("/intr/progress-check", methods=["GET", "POST"])
def progressCheck():
    student_redirect = require_student()
    if student_redirect:
        return student_redirect

    student_id = get_current_user_id()
    if student_id is None:
        flash("You must be logged in as a student to use the worklog.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            payload = validate_progress_check_form()
        except ValueError as exc:
            flash(str(exc), "danger")
            entries = fetch_progress_checks(student_id)
            return render_template("progresscheck.html", entries=entries)

        previous_question = None
        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT is_approved, mentor_questions FROM progress_checks WHERE student_id = %s AND day_worked = %s",
                        (student_id, payload["day_worked"]),
                    )
                    existing = cur.fetchone()
                    if existing and existing[0]:
                        flash("Worklogs cannot be edited following mentor approval", "warning")
                        return redirect(url_for("progressCheck"))
                    previous_question = existing[1] if existing else None
                    cur.execute(
                        """
                        INSERT INTO progress_checks
                        (
                            student_id,
                            day_worked,
                            hours_worked,
                            what_they_did,
                            mentor_questions,
                            reflection,
                            next_steps,
                            self_questions
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id, day_worked)
                        DO UPDATE SET
                            hours_worked = EXCLUDED.hours_worked,
                            what_they_did = EXCLUDED.what_they_did,
                            mentor_questions = EXCLUDED.mentor_questions,
                            reflection = EXCLUDED.reflection,
                            next_steps = EXCLUDED.next_steps,
                            self_questions = EXCLUDED.self_questions,
                            created_at = NOW(),
                            is_approved = FALSE,
                            is_rejected = FALSE
                        """,
                        (
                            student_id,
                            payload["day_worked"],
                            payload["hours_worked"],
                            payload["what_they_did"],
                            payload["mentor_questions"] or None,
                            payload["reflection"] or None,
                            payload["next_steps"] or None,
                            payload["self_questions"] or None,
                        ),
                    )
        finally:
            conn.close()

        new_question = payload["mentor_questions"]
        if new_question and new_question != (previous_question or ""):
            notify_mentor_of_question(student_id, payload["day_worked"], new_question)

        flash("Daily worklog saved.", "success")
        return redirect(url_for("progressCheck"))

    entries = fetch_progress_checks(student_id)
    return render_template("progresscheck.html", entries=entries)

@app.route("/intr/feedback/<int:id>/edit", methods=["GET", "POST"])
def editFeedback(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor") and not session.get("is_admin"):
        flash("That page is only available to mentors, admins, or presenter view.", "warning")
        return redirect(url_for("home"))

    try:
        students = fetch_feedback_students()
        feedback = fetch_feedback_entry(id)
    except psycopg2.Error:
        flash("Feedback entry could not be loaded.", "danger")
        return redirect(url_for("feedbackPage"))

    if feedback is None:
        flash("Feedback entry not found.", "warning")
        return redirect(url_for("feedbackPage"))

    if not can_access_student(feedback[1]):
        flash("You can only edit feedback for assigned students.", "danger")
        return redirect(url_for("feedbackPage"))

    if request.method == "POST":
        try:
            payload = validate_feedback_form()
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("editform.html", students=students, feedback=feedback)

        if not can_access_student(payload["student_id"]):
            flash("You can only move feedback to assigned students.", "danger")
            return render_template("editform.html", students=students, feedback=feedback)

        conn = get_db_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE feedback
                        SET
                            student_id = %s,
                            week = %s,
                            description = %s,
                            action_items = %s,
                            focus_areas = %s,
                            quality = %s,
                            professionalism = %s,
                            timeliness = %s,
                            initiative = %s,
                            softskills = %s,
                            rating = %s
                        WHERE id = %s
                        """,
                        (
                            payload["student_id"],
                            payload["week"],
                            payload["description"],
                            payload["action_items"],
                            payload["focus_areas"],
                            payload["quality"],
                            payload["professionalism"],
                            payload["timeliness"],
                            payload["initiative"],
                            payload["softskills"],
                            payload["rating"],
                            id,
                        ),
                    )
        finally:
            conn.close()

        flash("Feedback updated.", "success")
        return redirect(url_for("feedbackPage"))

    return render_template("editform.html", students=students, feedback=feedback)

@app.route("/intr/feedback/<int:id>/delete", methods=["POST"])
def deleteFeedback(id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    if not session.get("is_mentor") and not session.get("is_admin"):
        flash("That page is only available to mentors, admins, or presenter view.", "warning")
        return redirect(url_for("home"))

    feedback = fetch_feedback_entry(id)
    if feedback is None:
        flash("Feedback entry not found.", "warning")
        return redirect(url_for("feedbackPage"))

    if not can_access_student(feedback[1]):
        flash("You can only delete feedback for assigned students.", "danger")
        return redirect(url_for("feedbackPage"))

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM feedback WHERE id = %s", (id,))
                deleted = cur.rowcount
    finally:
        conn.close()

    if deleted:
        flash("Feedback deleted.", "success")
    else:
        flash("Feedback entry not found.", "warning")
    return redirect(url_for("feedbackPage"))

@app.route("/intr/confirm/<token>/")
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash("Invalid or expired confirmation link.", "danger")
        return redirect(url_for("register"))

    pending = PendingUser.query.filter_by(email=email).first()
    if not pending:
        flash("No matching pending registration.", "danger")
        return redirect(url_for("register"))

    if account_exists(email):
        db.session.delete(pending)
        db.session.commit()
        flash("Account already confirmed. Please log in.", "info")
        return redirect(url_for("login"))

    account_data = {
        "email": pending.email,
        "first_name": pending.first_name,
        "last_name": pending.last_name,
        "password": pending.password,
        "organization": pending.organization,
        "organization_id": pending.organization_id,
    }

    if pending.role == "student":
        new_user = Student(**account_data)
    elif pending.role == "mentor":
        new_user = Mentor(**account_data)
    elif pending.role == "admin":
        new_user = Admin(
            **account_data,
        )
    else:
        flash("Invalid pending registration role.", "danger")
        return redirect(url_for("register"))

    db.session.add(new_user)
    db.session.flush()

    if pending.role == "student" and pending.requested_mentor_id:
        assignment = MentorAssignment(
            student_id=new_user.id,
            mentor_id=pending.requested_mentor_id,
        )
        db.session.add(assignment)

    db.session.delete(pending)
    db.session.commit()

    flash("Registration confirmed!", "success")
    return redirect(url_for("login"))



if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, port=5044)
