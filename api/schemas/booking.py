class BookingCreate(BaseModel):
    slot_id: int
    name: str
    phone: str