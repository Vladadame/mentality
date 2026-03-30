import os
import psycopg
from psycopg.rows import dict_row


def db_conn():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "pg"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "booking"),
        user=os.getenv("DB_USER", "booking"),
        password=os.getenv("DB_PASSWORD", ""),
        row_factory=dict_row,
    )


def check_db():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            return cur.fetchone()