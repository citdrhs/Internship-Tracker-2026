import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

DB_NAME = os.environ["DB"]
DB_USER = os.environ["DB_UN"]
DB_PASSWORD = os.environ["DB_PW"]
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "5433"))

SMTP_HOST = os.environ.get("SMTP_HOST", "smtppro.zoho.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USERNAME = os.environ["SMTP_USERNAME"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "CIT Internship Program")
MAIL_FROM_ADDRESS = os.environ.get("MAIL_FROM_ADDRESS", "noreply@drhscit.org")

FOLLOWUP_SUBJECT = "REMINDER: Register for the CIT Internship App"


def send_email(recipient, subject, body):
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM_ADDRESS}>"
    message["To"] = recipient
    message.set_content(body)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


def main():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT body FROM email_templates WHERE name = 'followup'")
            row = cur.fetchone()
            body = row[0] if row else ""
            cur.execute(
                """
                SELECT id, email
                FROM organization_mentor_emails
                WHERE invited_at IS NOT NULL
                  AND invited_at <= NOW() - INTERVAL '7 days'
                  AND reminder_sent_at IS NULL
                  AND lower(email) NOT IN (SELECT lower(email) FROM mentors)
                """
            )
            due = cur.fetchall()

        sent = 0
        for email_id, email in due:
            try:
                send_email(email, FOLLOWUP_SUBJECT, body)
            except Exception as exc:
                print(f"Reminder to {email} failed: {exc}")
                continue
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE organization_mentor_emails SET reminder_sent_at = NOW() WHERE id = %s",
                    (email_id,),
                )
            sent += 1
        print(f"Follow-up reminders sent: {sent} of {len(due)} due")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
