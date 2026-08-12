# Internship-Tracker-2026

## Mentor follow-up reminders

A week after a mentor is invited to register, they get an automatic follow-up
email if they still haven't signed up. This is handled by a small standalone
service/mini-app that runs on a daily schedule, **separate from this web app** 
(it exists in `/opt/internships-reminders` on the server).

It is intentionally **separate from the web app** because the internship
app may be containerized via CITDEPLOY pipeline (https://drhscit.org/citdeploy/).
When an app is containerized, it cannot easily talk to scheduled services that
run on the system via systemd (like this one).

Everything this service needs and full setup instructions is in the [`internships-reminders/`](internships-reminders/)
folder. See [`internships-reminders/README.md`](reminders/README.md) for more details.

### NOTE: IT IS LIKELY ALREADY SET UP AND RUNNING!