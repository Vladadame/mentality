import os
import hmac
import hashlib
import json
import time
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.post("/bookings")
def create_booking(payload: BookingCreate):
    return booking_service.create_booking(payload)


@app.post("/payments/wayforpay/create")
def create_wayforpay_payment(payload: PaymentCreate):
    return payment_service.create_wayforpay_payment(payload)


@app.post("/payments/wayforpay/callback")
async def wayforpay_callback(payload: dict[str, Any] = Body(...)):
    return payment_service.handle_wayforpay_callback(payload)















@app.get("/db-check")
def db_check():
    return {"db": check_db()}








from services.booking_service import create_booking_service

@app.post("/bookings")
def create_booking(payload: BookingCreate):
    return create_booking_service(payload)


@app.post("/payments/wayforpay/create")
def create_wayforpay_payment(payload: PaymentCreate):
    merchant_account = get_env("WFP_MERCHANT_ACCOUNT")
    secret_key = get_env("WFP_SECRET_KEY")
    domain = get_env("WFP_DOMAIN")
    base_url = get_env("BASE_URL")

    amount = Decimal("500.00")
    currency = "UAH"
    product_name = "Psychologist consultation"

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT b.id, b.slot_id, b.name, b.phone, b.status,
                       s.start_at, s.end_at, s.status AS slot_status
                FROM bookings b
                JOIN slots s ON s.id = b.slot_id
                WHERE b.id = %s
                """,
                (payload.booking_id,),
            )
            booking = cur.fetchone()

            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            if booking["status"] != "pending":
                raise HTTPException(status_code=409, detail="Booking is not pending")

            if booking["slot_status"] != "hold":
                raise HTTPException(status_code=409, detail="Slot is not on hold")

            order_reference = f"booking-{booking['id']}-{int(time.time())}"
            order_date = int(time.time())

            provider_payload = {
                "booking_id": booking["id"],
                "amount": str(amount),
                "currency": currency,
                "productName": [product_name],
                "productCount": [1],
                "productPrice": [str(amount)],
            }

            cur.execute(
                """
                INSERT INTO payments (
                    booking_id, provider, order_reference, amount, currency, status, provider_payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, booking_id, provider, order_reference, amount, currency, status, created_at
                """,
                (
                    booking["id"],
                    "wayforpay",
                    order_reference,
                    amount,
                    currency,
                    "initiated",
                    json.dumps(provider_payload),
                ),
            )
            payment = cur.fetchone()

            conn.commit()

    product_names = [product_name]
    product_counts = [1]
    product_prices = [str(amount)]

    sign_parts = [
        merchant_account,
        domain,
        order_reference,
        str(order_date),
        str(amount),
        currency,
        *[str(x) for x in product_names],
        *[str(x) for x in product_counts],
        *[str(x) for x in product_prices],
    ]
    merchant_signature = hmac_md5_hex(";".join(sign_parts), secret_key)

    return {
        "message": "Payment created",
        "payment": payment,
        "wayforpay": {
            "action": "https://secure.wayforpay.com/pay",
            "fields": {
                "merchantAccount": merchant_account,
                "merchantAuthType": "SimpleSignature",
                "merchantDomainName": domain,
                "merchantSignature": merchant_signature,
                "orderReference": order_reference,
                "orderDate": order_date,
                "amount": str(amount),
                "currency": currency,
                "productName[]": product_names,
                "productCount[]": product_counts,
                "productPrice[]": product_prices,
                "returnUrl": f"{base_url}/booking/paid?orderReference={order_reference}",
                "serviceUrl": f"{base_url}/payments/wayforpay/callback",
            },
        },
    }


@app.post("/payments/wayforpay/callback")
async def wayforpay_callback(payload: dict[str, Any] = Body(...)):
    secret_key = get_env("WFP_SECRET_KEY")
    data = payload

    order_reference = str(data.get("orderReference", ""))

    sign_fields = [
        str(data.get("merchantAccount", "")),
        order_reference,
        str(data.get("amount", "")),
        str(data.get("currency", "")),
        str(data.get("authCode", "")),
        str(data.get("cardPan", "")),
        str(data.get("transactionStatus", "")),
        str(data.get("reasonCode", "")),
    ]

    expected_signature = hmac_md5_hex(";".join(sign_fields), secret_key)
    received_signature = str(data.get("merchantSignature", ""))

    # Временно можно не проверять подпись локально:
    # if expected_signature != received_signature:
    #     raise HTTPException(status_code=400, detail="Invalid signature")

    tx_status = str(data.get("transactionStatus", "")).lower()

    if tx_status not in ("approved", "success"):
        new_status = tx_status or "failed"

        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE payments
                    SET status = %s,
                        provider_payload = %s
                    WHERE order_reference = %s
                    """,
                    (new_status, json.dumps(data), order_reference),
                )
                conn.commit()

        return {"status": "ignored"}

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, booking_id
                FROM payments
                WHERE order_reference = %s
                """,
                (order_reference,),
            )
            payment = cur.fetchone()

            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")

            booking_id = payment["booking_id"]

            cur.execute(
                """
                UPDATE payments
                SET status = 'approved',
                    provider_payload = %s
                WHERE id = %s
                """,
                (json.dumps(data), payment["id"]),
            )

            cur.execute(
                """
                UPDATE bookings
                SET status = 'confirmed'
                WHERE id = %s
                """,
                (booking_id,),
            )

            cur.execute(
                """
                UPDATE slots
                SET status = 'booked'
                WHERE id = (
                    SELECT slot_id FROM bookings WHERE id = %s
                )
                """,
                (booking_id,),
            )

            conn.commit()

    now = int(time.time())
    status = "accept"

    response_signature = hmac_md5_hex(
        f"{order_reference};{status};{now}",
        secret_key,
    )

    return JSONResponse({
        "orderReference": order_reference,
        "status": status,
        "time": now,
        "signature": response_signature,
    })