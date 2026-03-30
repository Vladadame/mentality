@app.get("/health")
def health():
    return {"ok": True}

@app.get("/booking", response_class=HTMLResponse)
def booking_page(request: Request):
    return templates.TemplateResponse(
        "booking.html",
        {"request": request},
    )