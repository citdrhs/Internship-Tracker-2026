# Mentor Onboarding Email Follow-up Reminder Email Service

A small standalone service/mini-app that emails a follow-up reminder to mentors who received
the initial onboarding email but still have not created an account 7 days later.

It is intentionally **separate from the web app** because the internship
app may be containerized via CITDEPLOY pipeline (https://drhscit.org/citdeploy/).
When an app is containerized, it cannot easily talk to scheduled services that
run on the system via systemd.

## How it works

Once a day the systemd timer runs `send_reminders.py`, which:

1. Reads the follow-up email body from the `email_templates` table
2. Finds every row in `organization_mentor_emails` that was invited at least 7
   days ago, has not been reminded yet, and whose email does **not** already
   have a registered mentor account
3. Emails each of them the follow-up, then records `reminder_sent_at` so nobody
   is emailed twice

## Deploying on the server (It likely ALREADY EXISTS and is ALREADY RUNNING!!)

This service should run under `/opt/internships-reminders` (not the /home directory) and 
should act pretty much as a standalone 'app'

One-time setup:

- Copy this 'internships-reminders' folder into /opt/internships-reminders
- Ensure the folder has a .env file with the following variables:
```bash
DB=internships
DB_UN=internships
DB_PW=
DB_HOST=127.0.0.1
DB_PORT=5433

SMTP_HOST=smtppro.zoho.com
SMTP_PORT=465
SMTP_USERNAME=noreply@drhscit.org
SMTP_PASSWORD=
MAIL_FROM_NAME=CIT Internship Program - NO REPLY
MAIL_FROM_ADDRESS=noreply@drhscit.org
```
- Then, run the following:
```bash

sudo python3 -m venv /opt/internships-reminders/venv
sudo /opt/internships-reminders/venv/bin/pip install -r /opt/internships-reminders/requirements.txt
sudo chown -R internships:internships /opt/internships-reminders
sudo chmod 600 /opt/internships-reminders/.env

# install the schedule
sudo cp internships-reminders.service internships-reminders.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now internships-reminders.timer
```

## Schedule

The timer uses `OnCalendar=*-*-* 06:00:00 America/New_York`, so it runs **daily
at 6 AM Eastern**. `Persistent=true` means a run missed while the server was down 
is caught up as soon as it's back.

## When the app is containerized

Nothing here changes. The job talks to the database directly and reads its own
config, so as long as the Postgres database stays reachable at the host/port in
`.env`, this keeps running from `/opt` exactly as-is.
