import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / "env"

DEFAULT_SCHEMA = """
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS progress_checks CASCADE;
DROP TABLE IF EXISTS mentor_assignments CASCADE;
DROP TABLE IF EXISTS pending_users CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS mentors CASCADE;
DROP TABLE IF EXISTS admin CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

CREATE TABLE organizations (
    id BIGSERIAL PRIMARY KEY,
    organization_name VARCHAR(256) NOT NULL,
    email VARCHAR(128) NOT NULL,
    phone_number VARCHAR(64) NOT NULL,
    address VARCHAR(128) NOT NULL,
    city VARCHAR(128) NOT NULL,
    state VARCHAR(128) NOT NULL,
    zip_code VARCHAR(16) NOT NULL,
    website VARCHAR(512) NOT NULL,
    type_of_screening VARCHAR(128),
    WBL_checklist BYTEA NOT NULL,
    Training_agreement_form BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE students (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    organization VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE mentors (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    phone_number VARCHAR(16) NOT NULL,
    email VARCHAR(128) NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE admin (
    id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOt NULL,
    email VARCHAR(128) NOT NULL,
    phone_number VARCHAR(16) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE pending_users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    organization VARCHAR(200),
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_mentor BOOLEAN NOT NULL DEFAULT FALSE,
    is_teacher BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE mentor_assignments (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    mentor_id BIGINT NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (student_id, mentor_id)
);

CREATE TABLE progress_checks (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
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
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    mentor_id BIGINT NOT NULL REFERENCES mentors(id) ON DELETE CASCADE,
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

    print(f"Initialized Internship Tracker schema on {os.getenv("DB_HOST", "localhost")}:{int(os.getenv("DB_PORT", "5432"))}")


if __name__ == "__main__":
    main()