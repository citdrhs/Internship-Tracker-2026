import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / "env"

from init_db import get_connection

def add_file_to_column(file_name: str, column_name: str, record_id:int, conn, cur) -> None:
    with open(file_name, 'rb') as f:
        file = f.read()

    query = sql.SQL("UPDATE organizations SET {col} = %s WHERE id = %s").format(
    col=sql.Identifier(column_name)
    )
    
    cur.execute(query, (psycopg2.Binary(file), record_id,))
    conn.commit()
    print(f"Added {file_name} to database")

def main() -> None:
    conn = get_connection()
    cur = conn.cursor()
    
    add_file_to_column('cute.jpg', 'wbl_checklist', 0, conn, cur)

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
"SELECT * FROM users;"