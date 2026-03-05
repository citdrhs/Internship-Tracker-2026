import os
import psycopg2

conn = psycopg2.connect(
host='drhscit.org',
database=os.environ['DB'],
user=os.environ['DB_UN'],
password=os.environ['DB_PW']
)

cur = conn.cursor()

# Create students table

cur.execute('''
CREATE TABLE IF NOT EXISTS students (
id   SERIAL PRIMARY KEY,
name TEXT NOT NULL
)
''')

# Create feedback table

cur.execute('''
CREATE TABLE IF NOT EXISTS feedback (
id          SERIAL PRIMARY KEY,
student_id  INTEGER NOT NULL REFERENCES students(id),
description TEXT    NOT NULL,
rating      INTEGER NOT NULL
)
''')

conn.commit()
cur.close()
conn.close()
print('Database initialized.')
