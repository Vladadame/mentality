def get_free_slots():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, start_at, end_at, status, hold_until
                FROM slots
                WHERE status = 'free'
                ORDER BY start_at ASC
            """)
            return cur.fetchall()