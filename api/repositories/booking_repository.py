from core.db import db_conn


def find_slot_by_id(slot_id: int):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status, hold_until
                FROM slots
                WHERE id = %s
                """,
                (slot_id,),
            )
            return cur.fetchone()


def hold_slot(slot_id: int):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE slots
                SET status = 'hold',
                    hold_until = NOW() + INTERVAL '15 minutes'
                WHERE id = %s
                RETURNING id, start_at, end_at, status, hold_until
                """,
                (slot_id,),
            )
            row = cur.fetchone()
            conn.commit()
            return row
        
from core.db import db_conn


def create_booking(slot_id: int, name: str, phone: str):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bookings (slot_id, name, phone, status)
                VALUES (%s, %s, %s, 'pending')
                RETURNING id, slot_id, name, phone, telegram_id, status, created_at
                """,
                (slot_id, name, phone),
            )
            row = cur.fetchone()
            conn.commit()
            return row