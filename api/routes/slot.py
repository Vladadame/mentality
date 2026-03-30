from services.slot_service import list_available_slots

@app.get("/slots")
def get_slots():
    return list_available_slots()

@app.get("/slots")
def get_slots():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, start_at, end_at, status, hold_until
                FROM slots
                WHERE status = 'free'
                ORDER BY start_at ASC
                """
            )
            rows = cur.fetchall()

    return rows