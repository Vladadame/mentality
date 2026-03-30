let selectedSlotId = null;

async function loadSlots() {
    const response = await fetch("/slots");
    const slots = await response.json();

    const container = document.getElementById("slots");
    container.innerHTML = "";

    if (!slots.length) {
        container.innerHTML = "<div>Нет доступных слотов</div>";
        return;
    }

    slots.forEach((slot) => {
        const btn = document.createElement("button");
        btn.className = "slot-btn";
        btn.type = "button";
        btn.textContent = `${slot.start_at} — ${slot.end_at}`;
        btn.onclick = () => selectSlot(slot.id, btn);
        container.appendChild(btn);
    });
}

function selectSlot(slotId, buttonElement) {
    selectedSlotId = slotId;

    document.querySelectorAll(".slot-btn").forEach((btn) => {
        btn.classList.remove("active");
    });

    buttonElement.classList.add("active");
}

async function createBooking() {
    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const message = document.getElementById("message");

    if (!selectedSlotId) {
        message.textContent = "Выберите слот";
        return null;
    }

    if (!name || !phone) {
        message.textContent = "Заполните имя и телефон";
        return null;
    }

    const response = await fetch("/bookings", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            slot_id: selectedSlotId,
            name,
            phone,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        message.textContent = data.detail || "Ошибка создания брони";
        return null;
    }

    return data.booking;
}

async function createPayment(bookingId) {
    const response = await fetch("/payments/wayforpay/create", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            booking_id: bookingId,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Ошибка создания оплаты");
    }

    return data.wayforpay;
}

function submitWayForPayForm(wayforpayData) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = wayforpayData.action;

    for (const [key, value] of Object.entries(wayforpayData.fields)) {
        if (Array.isArray(value)) {
            value.forEach((item) => {
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = key;
                input.value = String(item);
                form.appendChild(input);
            });
        } else {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = key;
            input.value = String(value);
            form.appendChild(input);
        }
    }

    document.body.appendChild(form);
    form.submit();
}

document.getElementById("bookBtn").addEventListener("click", async () => {
    const message = document.getElementById("message");
    message.textContent = "Создаём бронь...";

    try {
        const booking = await createBooking();
        if (!booking) {
            return;
        }

        message.textContent = "Создаём оплату...";

        const wayforpay = await createPayment(booking.id);

        message.textContent = "Переход к оплате...";
        submitWayForPayForm(wayforpay);
    } catch (error) {
        message.textContent = error.message || "Неизвестная ошибка";
    }
});

loadSlots();