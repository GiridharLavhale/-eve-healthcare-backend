"""Payment provider webhook and idempotency tests."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import WebhookEvent


def test_webhook_success_flow(client: TestClient, auth_headers, seeded_data, db_session: Session):
    """Verifies that an incoming SUCCESS webhook updates booking status to CONFIRMED and records payment."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    webhook_payload = {
        "event_id": "evt_test_001",
        "event_type": "payment.updated",
        "payment_id": "pay_test_001",
        "booking_id": booking_id,
        "status": "SUCCESS",
        "amount": 500.00,
    }

    wh_res = client.post("/payments/webhook/", json=webhook_payload)
    assert wh_res.status_code == 200
    wh_data = wh_res.json()
    assert wh_data["status"] == "success"
    assert wh_data["booking_status"] == "CONFIRMED"

    # Verify database state
    booking = db_session.get(Booking, booking_id)
    assert booking.status == BookingStatus.CONFIRMED

    # Verify payment record
    stmt = select(Payment).where(Payment.provider_payment_id == "pay_test_001")
    payment = db_session.execute(stmt).scalar_one_or_none()
    assert payment is not None
    assert payment.status == PaymentStatus.SUCCESS
    assert float(payment.amount) == 500.00


def test_webhook_failed_flow(client: TestClient, auth_headers, seeded_data, db_session: Session):
    """Verifies that an incoming FAILED webhook updates a PENDING booking to FAILED."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    webhook_payload = {
        "event_id": "evt_test_002",
        "event_type": "payment.updated",
        "payment_id": "pay_test_002",
        "booking_id": booking_id,
        "status": "FAILED",
        "amount": 500.00,
    }

    wh_res = client.post("/payments/webhook/", json=webhook_payload)
    assert wh_res.status_code == 200
    assert wh_res.json()["status"] == "success"
    assert wh_res.json()["booking_status"] == "FAILED"

    booking = db_session.get(Booking, booking_id)
    assert booking.status == BookingStatus.FAILED


def test_webhook_idempotency_10_repeated_calls(client: TestClient, auth_headers, seeded_data, db_session: Session):
    """
    CRITICAL IDEMPOTENCY TEST:
    Verifies that sending the exact same webhook 10 times:
    - Only processes once (1st returns 'success', remaining 9 return 'duplicate')
    - Creates exactly ONE payment record
    - Keeps the booking count and status completely consistent
    - Never corrupts state
    """
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    webhook_payload = {
        "event_id": "evt_idempotent_999",
        "event_type": "payment.updated",
        "payment_id": "pay_idempotent_999",
        "booking_id": booking_id,
        "status": "SUCCESS",
        "amount": 500.00,
    }

    # 1st call -> success
    res1 = client.post("/payments/webhook/", json=webhook_payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"
    assert res1.json()["booking_status"] == "CONFIRMED"

    # Subsequent 9 calls -> duplicate
    for i in range(2, 11):
        res_i = client.post("/payments/webhook/", json=webhook_payload)
        assert res_i.status_code == 200, f"Call #{i} failed with status {res_i.status_code}"
        assert res_i.json()["status"] == "duplicate", f"Call #{i} did not return duplicate status"
        assert res_i.json()["booking_status"] == "CONFIRMED"

    # Verify payment record count in database
    stmt_payments = select(Payment).where(Payment.provider_payment_id == "pay_idempotent_999")
    payments = db_session.execute(stmt_payments).scalars().all()
    assert len(payments) == 1, f"Expected 1 payment record, found {len(payments)}"

    # Verify webhook event record count
    stmt_events = select(WebhookEvent).where(WebhookEvent.event_id == "evt_idempotent_999")
    events = db_session.execute(stmt_events).scalars().all()
    assert len(events) == 1, f"Expected 1 webhook event record, found {len(events)}"
    assert events[0].processed is True

    # Verify booking status remains CONFIRMED
    booking = db_session.get(Booking, booking_id)
    assert booking.status == BookingStatus.CONFIRMED


def test_webhook_stale_failed_after_confirmed_protection(
    client: TestClient,
    auth_headers,
    seeded_data,
    db_session: Session,
):
    """
    STATE SAFETY TEST:
    Verifies that if a booking is already CONFIRMED, a delayed/stale FAILED webhook
    does NOT downgrade or corrupt the booking status.
    """
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Step 1: Booking is successfully confirmed via webhook 1
    wh1 = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt_success_first",
            "event_type": "payment.updated",
            "payment_id": "pay_success_first",
            "booking_id": booking_id,
            "status": "SUCCESS",
            "amount": 500.00,
        },
    )
    assert wh1.status_code == 200
    assert wh1.json()["booking_status"] == "CONFIRMED"

    # Step 2: A stale FAILED webhook arrives with a different event ID
    wh2 = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt_stale_failed_second",
            "event_type": "payment.updated",
            "payment_id": "pay_stale_failed_second",
            "booking_id": booking_id,
            "status": "FAILED",
            "amount": 500.00,
        },
    )
    assert wh2.status_code == 200
    # Booking status MUST remain CONFIRMED
    assert wh2.json()["booking_status"] == "CONFIRMED"

    booking = db_session.get(Booking, booking_id)
    assert booking.status == BookingStatus.CONFIRMED


def test_webhook_nonexistent_booking(client: TestClient):
    """Verifies that a webhook targeting a non-existent booking returns 404."""
    response = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt_no_booking",
            "event_type": "payment.updated",
            "payment_id": "pay_no_booking",
            "booking_id": 9999,
            "status": "SUCCESS",
        },
    )
    assert response.status_code == 404


def test_webhook_cancelled_booking_protection(client: TestClient, auth_headers, seeded_data, db_session: Session):
    """Verifies that if a booking is CANCELLED, an incoming SUCCESS webhook does not revive it."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Cancel booking
    client.post(f"/bookings/{booking_id}/cancel", headers=auth_headers)

    # Ingest SUCCESS webhook
    wh_res = client.post(
        "/payments/webhook/",
        json={
            "event_id": "evt_cancelled_wh",
            "event_type": "payment.updated",
            "payment_id": "pay_cancelled_wh",
            "booking_id": booking_id,
            "status": "SUCCESS",
        },
    )
    assert wh_res.status_code == 200
    assert wh_res.json()["booking_status"] == "CANCELLED"

    booking = db_session.get(Booking, booking_id)
    assert booking.status == BookingStatus.CANCELLED
