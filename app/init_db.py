import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

DEFAULT_SCHEMA = """
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS progress_checks CASCADE;
DROP TABLE IF EXISTS mentor_assignments CASCADE;
DROP TABLE IF EXISTS pending_users CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

CREATE TABLE organizations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    organization_number VARCHAR(200),
    organization_address VARCHAR(200),
    organization_city VARCHAR(200),
    organization_state VARCHAR(200),
    organization_zip VARCHAR(200),
    organization_web VARCHAR(200),
    screening VARCHAR(200),
    atmosphere BOOLEAN NOT NULL DEFAULT FALSE,
    facilities BOOLEAN NOT NULL DEFAULT FALSE,
    accommodation BOOLEAN NOT NULL DEFAULT FALSE,
    pay BOOLEAN NOT NULL DEFAULT FALSE,
    wage_requirements BOOLEAN NOT NULL DEFAULT FALSE,
    equal_opportunity BOOLEAN NOT NULL DEFAULT FALSE,
    va_verify BOOLEAN NOT NULL DEFAULT FALSE,
    supervision BOOLEAN NOT NULL DEFAULT FALSE,
    mentorship BOOLEAN NOT NULL DEFAULT FALSE,
    virginia_5cs BOOLEAN NOT NULL DEFAULT FALSE,
    hours BOOLEAN NOT NULL DEFAULT FALSE,
    signature VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    grade VARCHAR(2),
    organization VARCHAR(200),
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_mentor BOOLEAN NOT NULL DEFAULT FALSE,
    is_teacher BOOLEAN NOT NULL DEFAULT FALSE,
    is_present_view BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pending_users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    grade VARCHAR(2),
    organization VARCHAR(200),
    organization_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    role TEXT NOT NULL DEFAULT 'student',
    requested_mentor_id BIGINT,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_mentor BOOLEAN NOT NULL DEFAULT FALSE,
    is_teacher BOOLEAN NOT NULL DEFAULT FALSE,
    is_present_view BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE TABLE mentor_assignments (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentor_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id)
);

CREATE TABLE progress_checks (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    day_worked DATE NOT NULL,
    hours_worked NUMERIC(5,2) NOT NULL CHECK (hours_worked >= 0 AND hours_worked <= 24),
    what_they_did TEXT NOT NULL,
    mentor_questions TEXT,
    reflection TEXT,
    next_steps TEXT,
    self_questions TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, day_worked)
);

CREATE TABLE feedback (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentor_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
"""


def get_connection():
    load_dotenv(ENV_FILE)

    database_uri = os.getenv("DATABASE_URI")
    if database_uri:
        return psycopg2.connect(database_uri)

    db_name = os.getenv("DB")
    db_user = os.getenv("DB_UN")
    db_password = os.getenv("DB_PW")
    db_host = os.getenv("DB_HOST", "drhscit.org")
    db_port = int(os.getenv("DB_PORT", "5434"))

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

    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )


def main() -> None:
    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(DEFAULT_SCHEMA)
    finally:
        connection.close()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))

    print(f"Initialized Internship Tracker schema on {db_host}:{db_port}")


if __name__ == "__main__":
    main()
