"""Simulated payment API tests."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def test_payment_success(client: TestClient, auth_headers, seeded_data):
    """Verifies that simulating a successful payment marks payment as SUCCESS and updates booking to CONFIRMED."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Process payment
    pay_res = client.post(
        "/payments/",
        json={"booking_id": booking_id, "simulate_result": "SUCCESS"},
        headers=auth_headers,
    )
    assert pay_res.status_code == 201
    pay_data = pay_res.json()
    assert pay_data["status"] == "SUCCESS"
    assert pay_data["booking_id"] == booking_id
    assert float(pay_data["amount"]) == 500.00

    # Verify booking status changed to CONFIRMED
    booking_res = client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert booking_res.json()["status"] == "CONFIRMED"


def test_payment_failed(client: TestClient, auth_headers, seeded_data):
    """Verifies that simulating a failed payment marks payment as FAILED and updates booking to FAILED."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Process payment with FAILED outcome
    pay_res = client.post(
        "/payments/",
        json={"booking_id": booking_id, "simulate_result": "FAILED"},
        headers=auth_headers,
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["status"] == "FAILED"

    # Verify booking status changed to FAILED
    booking_res = client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert booking_res.json()["status"] == "FAILED"


def test_payment_unauthenticated(client: TestClient):
    """Verifies that unauthenticated payment requests are rejected with 401."""
    response = client.post("/payments/", json={"booking_id": 1})
    assert response.status_code == 401


def test_payment_nonexistent_booking(client: TestClient, auth_headers):
    """Verifies that paying for a non-existent booking returns 404."""
    response = client.post(
        "/payments/",
        json={"booking_id": 9999, "simulate_result": "SUCCESS"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_payment_another_users_booking(client: TestClient, auth_headers, second_auth_headers, seeded_data):
    """Verifies that a user cannot pay for another user's booking (403 Forbidden)."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    # User 1 creates booking
    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # User 2 attempts to pay for User 1's booking -> 403
    pay_res = client.post(
        "/payments/",
        json={"booking_id": booking_id, "simulate_result": "SUCCESS"},
        headers=second_auth_headers,
    )
    assert pay_res.status_code == 403


def test_payment_already_confirmed_booking(client: TestClient, auth_headers, seeded_data):
    """Verifies that attempting payment on an already confirmed booking returns 400."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Pay once (SUCCESS)
    client.post(
        "/payments/",
        json={"booking_id": booking_id, "simulate_result": "SUCCESS"},
        headers=auth_headers,
    )

    # Attempt to pay second time -> 400
    pay_res2 = client.post(
        "/payments/",
        json={"booking_id": booking_id, "simulate_result": "SUCCESS"},
        headers=auth_headers,
    )
    assert pay_res2.status_code == 400
    assert "already paid" in pay_res2.json()["detail"].lower()


def test_payment_cancelled_booking(client: TestClient, auth_headers, seeded_data):
    """Verifies that paying for a cancelled booking returns 400."""
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

    # Attempt payment -> 400
    pay_res = client.post(
        "/payments/",
        json={"booking_id": booking_id, "simulate_result": "SUCCESS"},
        headers=auth_headers,
    )
    assert pay_res.status_code == 400
    assert "cancelled" in pay_res.json()["detail"].lower()
