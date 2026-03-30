# Psychologist Booking API

Небольшой backend-сервис для записи на консультацию с поддержкой онлайн-оплаты.

## Стек

* FastAPI
* PostgreSQL
* psycopg

## Основной функционал

* получение доступных слотов
* создание записи (booking)
* создание платежа
* обработка callback от платёжной системы

## Запуск

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Эндпоинты

```
GET  /slots
POST /bookings
POST /payments/wayforpay/create
POST /payments/wayforpay/callback
```

## Описание

Сервис реализует базовый процесс записи:

1. пользователь выбирает слот
2. создаётся запись
3. инициируется платёж
4. после оплаты запись подтверждается

---
