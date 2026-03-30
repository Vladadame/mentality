from repositories.slot_repository import get_free_slots

def list_available_slots():
    slots = get_free_slots()

    # тут можно потом добавить:
    # фильтрацию, преобразования, логику

    return slots

from fastapi import HTTPException

from repositories.slot_repository import find_slot_by_id, hold_slot
from repositories.booking_repository import create_booking


def create_booking_service(payload):
    slot = find_slot_by_id(payload.slot_id)

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot["status"] != "free":
        raise HTTPException(status_code=409, detail="Slot is not available")

    updated_slot = hold_slot(payload.slot_id)
    booking = create_booking(payload.slot_id, payload.name, payload.phone)

    return {
        "message": "Booking created",
        "booking": booking,
        "slot": updated_slot,
    }