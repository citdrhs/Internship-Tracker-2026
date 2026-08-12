import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS organizations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL
);

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS name VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_number VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_address VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_city VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_state VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_zip VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_web VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS screening VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS atmosphere BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS facilities BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS accommodation BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS pay BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS wage_requirements BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS equal_opportunity BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS va_verify BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS supervision BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS mentorship BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS virginia_5cs BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS hours BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS signature VARCHAR(200);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS excluded BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS organization_mentor_emails (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(200) NOT NULL,
    invited_at TIMESTAMPTZ,
    reminder_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_templates (
    name VARCHAR(50) PRIMARY KEY,
    body TEXT NOT NULL
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM organizations
        GROUP BY name
        HAVING COUNT(*) > 1
    ) THEN
        CREATE UNIQUE INDEX IF NOT EXISTS organizations_name_key ON organizations (name);
    END IF;
END $$;

DO $$
DECLARE
    legacy_column TEXT;
BEGIN
    FOR legacy_column IN
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'organizations'
          AND is_nullable = 'NO'
          AND column_name NOT IN ('id', 'name')
    LOOP
        EXECUTE format('ALTER TABLE organizations ALTER COLUMN %I DROP NOT NULL', legacy_column);
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    organization VARCHAR(200),
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE students ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE students ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE students ADD COLUMN IF NOT EXISTS last_name TEXT;
ALTER TABLE students ADD COLUMN IF NOT EXISTS password TEXT;
ALTER TABLE students ADD COLUMN IF NOT EXISTS organization VARCHAR(200);
ALTER TABLE students ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL;
ALTER TABLE students ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS mentors (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    organization VARCHAR(200),
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE mentors ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE mentors ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE mentors ADD COLUMN IF NOT EXISTS last_name TEXT;
ALTER TABLE mentors ADD COLUMN IF NOT EXISTS password TEXT;
ALTER TABLE mentors ADD COLUMN IF NOT EXISTS organization VARCHAR(200);
ALTER TABLE mentors ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL;
ALTER TABLE mentors ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS admins (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    organization VARCHAR(200),
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE admins ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE admins ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE admins ADD COLUMN IF NOT EXISTS last_name TEXT;
ALTER TABLE admins ADD COLUMN IF NOT EXISTS password TEXT;
ALTER TABLE admins ADD COLUMN IF NOT EXISTS organization VARCHAR(200);
ALTER TABLE admins ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL;
ALTER TABLE admins ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TABLE IF NOT EXISTS pending_users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    organization VARCHAR(200),
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    role TEXT NOT NULL DEFAULT 'student',
    requested_mentor_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE pending_users ADD COLUMN IF NOT EXISTS organization VARCHAR(200);
ALTER TABLE pending_users ADD COLUMN IF NOT EXISTS organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL;
ALTER TABLE pending_users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'student';
ALTER TABLE pending_users ADD COLUMN IF NOT EXISTS requested_mentor_id BIGINT;
ALTER TABLE pending_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
UPDATE pending_users SET role = 'student' WHERE role IS NULL;
ALTER TABLE pending_users ALTER COLUMN role SET DEFAULT 'student';
ALTER TABLE pending_users ALTER COLUMN role SET NOT NULL;

CREATE TABLE IF NOT EXISTS mentor_assignments (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL,
    mentor_id BIGINT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS progress_checks (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL,
    day_worked DATE NOT NULL,
    hours_worked NUMERIC(5,2) NOT NULL CHECK (hours_worked >= 0 AND hours_worked <= 24),
    what_they_did TEXT NOT NULL,
    mentor_questions TEXT,
    reflection TEXT,
    next_steps TEXT,
    self_questions TEXT,
    mentor_response TEXT,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    is_rejected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS feedback (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL,
    mentor_id BIGINT,
    week INTEGER NOT NULL CHECK (week BETWEEN 1 AND 52),
    description TEXT NOT NULL,
    action_items TEXT,
    focus_areas TEXT,
    quality SMALLINT NOT NULL CHECK (quality BETWEEN 1 AND 5),
    professionalism SMALLINT NOT NULL CHECK (professionalism BETWEEN 1 AND 5),
    timeliness SMALLINT NOT NULL CHECK (timeliness BETWEEN 1 AND 5),
    initiative SMALLINT NOT NULL CHECK (initiative BETWEEN 1 AND 5),
    softskills SMALLINT NOT NULL CHECK (softskills BETWEEN 1 AND 5),
    rating NUMERIC(4,2) NOT NULL CHECK (rating BETWEEN 1 AND 5),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_documents (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    url VARCHAR(1000),
    file_data BYTEA,
    original_name VARCHAR(500),
    content_type VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE student_documents ALTER COLUMN url DROP NOT NULL;
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS file_data BYTEA;
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS original_name VARCHAR(500);
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(200);

-- One final evaluation per student, filled out by that student's mentor.
CREATE TABLE IF NOT EXISTS final_evaluations (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    mentor_id BIGINT REFERENCES mentors(id) ON DELETE SET NULL,
    takes_on_tasks SMALLINT NOT NULL CHECK (takes_on_tasks BETWEEN 1 AND 5),
    seeks_opportunities SMALLINT NOT NULL CHECK (seeks_opportunities BETWEEN 1 AND 5),
    maintains_contact SMALLINT NOT NULL CHECK (maintains_contact BETWEEN 1 AND 5),
    accomplished_tasks SMALLINT NOT NULL CHECK (accomplished_tasks BETWEEN 1 AND 5),
    responsibilities_comments TEXT,
    team_member SMALLINT NOT NULL CHECK (team_member BETWEEN 1 AND 5),
    enthusiasm SMALLINT NOT NULL CHECK (enthusiasm BETWEEN 1 AND 5),
    communication SMALLINT NOT NULL CHECK (communication BETWEEN 1 AND 5),
    problem_solving SMALLINT NOT NULL CHECK (problem_solving BETWEEN 1 AND 5),
    work_ethic SMALLINT NOT NULL CHECK (work_ethic BETWEEN 1 AND 5),
    positive_attitude SMALLINT NOT NULL CHECK (positive_attitude BETWEEN 1 AND 5),
    initiative SMALLINT NOT NULL CHECK (initiative BETWEEN 1 AND 5),
    attendance SMALLINT NOT NULL CHECK (attendance BETWEEN 1 AND 5),
    characteristics_comments TEXT,
    overall_rating SMALLINT NOT NULL CHECK (overall_rating BETWEEN 1 AND 5),
    is_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE feedback ADD COLUMN IF NOT EXISTS mentor_id BIGINT;
ALTER TABLE feedback ALTER COLUMN mentor_id DROP NOT NULL;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS action_items TEXT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS focus_areas TEXT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS quality SMALLINT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS professionalism SMALLINT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS timeliness SMALLINT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS initiative SMALLINT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS softskills SMALLINT;
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS rating NUMERIC(4,2);
ALTER TABLE feedback ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE progress_checks ADD COLUMN IF NOT EXISTS is_approved BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE progress_checks ADD COLUMN IF NOT EXISTS is_rejected BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE progress_checks ADD COLUMN IF NOT EXISTS mentor_response TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS mentor_assignments_student_id_idx ON mentor_assignments (student_id);
CREATE UNIQUE INDEX IF NOT EXISTS progress_checks_student_day_idx ON progress_checks (student_id, day_worked);
CREATE UNIQUE INDEX IF NOT EXISTS students_email_idx ON students (email);
CREATE UNIQUE INDEX IF NOT EXISTS mentors_email_idx ON mentors (email);
CREATE UNIQUE INDEX IF NOT EXISTS admins_email_idx ON admins (email);
CREATE UNIQUE INDEX IF NOT EXISTS pending_users_email_idx ON pending_users (email);

DO $$
BEGIN
    IF to_regclass('public.users') IS NOT NULL THEN
        INSERT INTO students (id, email, first_name, last_name, password, organization, organization_id)
        SELECT id, email, first_name, last_name, password, organization, organization_id
        FROM users
        WHERE COALESCE(is_admin, FALSE) = FALSE
          AND COALESCE(is_teacher, FALSE) = FALSE
          AND COALESCE(is_mentor, FALSE) = FALSE
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            password = EXCLUDED.password,
            organization = EXCLUDED.organization,
            organization_id = EXCLUDED.organization_id;

        INSERT INTO mentors (id, email, first_name, last_name, password, organization, organization_id)
        SELECT id, email, first_name, last_name, password, organization, organization_id
        FROM users
        WHERE COALESCE(is_mentor, FALSE) = TRUE
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            password = EXCLUDED.password,
            organization = EXCLUDED.organization,
            organization_id = EXCLUDED.organization_id;

        INSERT INTO admins (id, email, first_name, last_name, password, organization, organization_id)
        SELECT id, email, first_name, last_name, password, organization, organization_id
        FROM users
        WHERE COALESCE(is_admin, FALSE) = TRUE
           OR COALESCE(is_teacher, FALSE) = TRUE
        ON CONFLICT (id) DO UPDATE SET
            email = EXCLUDED.email,
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            password = EXCLUDED.password,
            organization = EXCLUDED.organization,
            organization_id = EXCLUDED.organization_id;
    END IF;
END $$;

DROP TABLE IF EXISTS users CASCADE;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'mentor_assignments_student_fk'
          AND conrelid = 'mentor_assignments'::regclass
    ) THEN
        ALTER TABLE mentor_assignments
        ADD CONSTRAINT mentor_assignments_student_fk
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'mentor_assignments_mentor_fk'
          AND conrelid = 'mentor_assignments'::regclass
    ) THEN
        ALTER TABLE mentor_assignments
        ADD CONSTRAINT mentor_assignments_mentor_fk
        FOREIGN KEY (mentor_id) REFERENCES mentors(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'progress_checks_student_fk'
          AND conrelid = 'progress_checks'::regclass
    ) THEN
        ALTER TABLE progress_checks
        ADD CONSTRAINT progress_checks_student_fk
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'feedback_student_fk'
          AND conrelid = 'feedback'::regclass
    ) THEN
        ALTER TABLE feedback
        ADD CONSTRAINT feedback_student_fk
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'feedback_mentor_fk'
          AND conrelid = 'feedback'::regclass
    ) THEN
        ALTER TABLE feedback
        ADD CONSTRAINT feedback_mentor_fk
        FOREIGN KEY (mentor_id) REFERENCES mentors(id) ON DELETE CASCADE NOT VALID;
    END IF;
END $$;

DO $$
DECLARE
    table_name TEXT;
    sequence_name TEXT;
    max_id BIGINT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'organizations',
        'students',
        'mentors',
        'admins',
        'pending_users',
        'mentor_assignments',
        'progress_checks',
        'feedback'
    ]
    LOOP
        SELECT pg_get_serial_sequence(table_name, 'id') INTO sequence_name;
        IF sequence_name IS NOT NULL THEN
            EXECUTE format('SELECT COALESCE(MAX(id), 0) FROM %I', table_name) INTO max_id;
            EXECUTE 'SELECT setval($1, $2, $3)' USING sequence_name, GREATEST(max_id, 1), max_id > 0;
        END IF;
    END LOOP;
END $$;
"""


ONBOARDING_EMAIL_DEFAULT = """Dear CIT Student Internship Mentor,

This summer, the Center for Information Technology is using a custom-built site to manage student work logs, hour approvals, and feedback submissions as part of the CIT internship process.

To register, students must select a mentor profile to link their account to. Therefore, it would be great if you could create an account for the website as soon as possible.

The documentation linked below covers all mentor-related features on the Internship Tracker website, including account creation, bug reporting, submitting feedback, and approving hours. Please review it thoroughly.
Documentation: https://docs.google.com/document/d/1_ER0zeRv4XzvdkAsa-ip4l5V_5oEuR7km37FDV9K7J0/edit?usp=sharing
If you'd prefer to watch an explanatory video instead: https://drive.google.com/file/d/1oY3Zct0-IHeb13sQohE_FRHCt5ZcwoBL/view?usp=sharing

*** The mentor code for registration is: 2892

The internship tracker website can be found here: https://drhscit.org/internships/intr/

We appreciate the opportunity you will be providing for your student(s)!  If you have any questions, please reach out to kblogan@henrico.k12.va.us

Best,
Center for Information Technology
Deep Run High School, Glen Allen, VA, USA
"""

FOLLOWUP_EMAIL_DEFAULT = """Dear CIT Student Internship Mentor,

We would like to follow up on our previous email about registering for the Center for Information Technology Internship Tracker website. Your student intern(s) cannot register for their accounts until your mentor profile is set up, so we'd be grateful if you could create your account when you have a moment.

Register here: https://drhscit.org/internships/intr/
Mentor code for Registration: 2892
Documentation/Instructions: https://docs.google.com/document/d/1_ER0zeRv4XzvdkAsa-ip4l5V_5oEuR7km37FDV9K7J0/edit?usp=sharing
If you'd prefer to watch an explanatory video instead: https://drive.google.com/file/d/1oY3Zct0-IHeb13sQohE_FRHCt5ZcwoBL/view?usp=sharing

If you've already signed up, please disregard this.

If you have any questions, please reach out to kblogan@henrico.k12.va.us.

Thank you,
Center for Information Technology
Deep Run High School, Glen Allen, VA, USA
"""


def get_connection():
    load_dotenv(ENV_FILE)

    db_name = os.getenv("DB")
    db_user = os.getenv("DB_UN")
    db_password = os.getenv("DB_PW")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("DB_PORT", "5434"))
    if db_host == "drhscit.org" and db_port == 5432:
        db_port = 5434

    if db_name and db_user and db_password:
        return psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )

    database_uri = os.getenv("DATABASE_URI")
    if database_uri:
        database_uri = database_uri.replace("drhscit.org:5432", "drhscit.org:5434")
        return psycopg2.connect(database_uri)

    missing = [
        key
        for key, value in {
            "DB": db_name,
            "DB_UN": db_user,
            "DB_PW": db_password,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required env values: {', '.join(missing)}")


def initialize_database() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            cur.execute(
                "INSERT INTO email_templates (name, body) VALUES (%s, %s), (%s, %s) "
                "ON CONFLICT (name) DO NOTHING",
                ("onboarding", ONBOARDING_EMAIL_DEFAULT, "followup", FOLLOWUP_EMAIL_DEFAULT),
            )


def main() -> None:
    initialize_database()
    print("Initialized Internship Tracker schema.")


if __name__ == "__main__":
    main()
