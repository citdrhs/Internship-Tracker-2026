import os
from pathlib import Path

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / "env"

from init_db import get_connection

def write_to_bin_file(output_file_name: str, column_name: str, record_id: int, conn, cur) -> None:
    query = sql.SQL("SELECT {col} FROM organizations WHERE id = %s;").format(
        col = sql.Identifier(column_name)
    )
    cur.execute(query, (record_id,))

    row = cur.fetchone()

    if row:
        binary_data = row[0]

        with open(output_file_name, 'wb') as f:
            f.write(binary_data)
        print("File saved")
    else:
        print("record_id not found")


def main():
    conn = get_connection()
    cur = conn.cursor()

    write_to_bin_file("testreading.jpg", 'wbl_checklist', 0, conn, cur)

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()