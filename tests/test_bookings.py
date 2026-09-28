"""Booking management API tests."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def test_create_booking_success(client: TestClient, auth_headers, seeded_data, test_user):
    """Verifies that an authenticated user can create a booking with correct price snapshot and PENDING status."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]  # Price at c1 is 500.00
    future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    payload = {
        "centre_id": c1.id,
        "test_id": t_cbc.id,
        "appointment_datetime": future_time,
    }

    response = client.post("/bookings/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == test_user.id
    assert data["centre_id"] == c1.id
    assert data["test_id"] == t_cbc.id
    assert float(data["amount"]) == 500.00  # Snapshotted price
    assert data["status"] == "PENDING"


def test_create_booking_unauthenticated(client: TestClient, seeded_data):
    """Verifies that unauthenticated booking requests are rejected with 401."""
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "centre_id": seeded_data["centre_1"].id,
        "test_id": seeded_data["test_cbc"].id,
        "appointment_datetime": future_time,
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 401


def test_create_booking_invalid_centre(client: TestClient, auth_headers, seeded_data):
    """Verifies that non-existent centre ID returns 404."""
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "centre_id": 9999,
        "test_id": seeded_data["test_cbc"].id,
        "appointment_datetime": future_time,
    }
    response = client.post("/bookings/", json=payload, headers=auth_headers)
    assert response.status_code == 404


def test_create_booking_test_not_offered_by_centre(client: TestClient, auth_headers, seeded_data):
    """Verifies that selecting a test not offered by the chosen centre returns 400."""
    c1 = seeded_data["centre_1"]
    t_thyroid = seeded_data["test_thyroid"]  # Centre 1 only offers CBC and Lipid, not Thyroid
    future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    payload = {
        "centre_id": c1.id,
        "test_id": t_thyroid.id,
        "appointment_datetime": future_time,
    }
    response = client.post("/bookings/", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "not offered" in response.json()["detail"].lower()


def test_create_booking_past_datetime_rejected(client: TestClient, auth_headers, seeded_data):
    """Verifies that appointments scheduled in the past are rejected by validation."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    past_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    payload = {
        "centre_id": c1.id,
        "test_id": t_cbc.id,
        "appointment_datetime": past_time,
    }
    response = client.post("/bookings/", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_list_user_bookings(client: TestClient, auth_headers, second_auth_headers, seeded_data):
    """Verifies that users can only see their own bookings."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # Create 2 bookings for User 1
    client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )

    # Create 1 booking for User 2
    client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=second_auth_headers,
    )

    # User 1 lists bookings
    res1 = client.get("/bookings/", headers=auth_headers)
    assert res1.status_code == 200
    assert len(res1.json()) == 2

    # User 2 lists bookings
    res2 = client.get("/bookings/", headers=second_auth_headers)
    assert res2.status_code == 200
    assert len(res2.json()) == 1


def test_get_booking_ownership_protection(client: TestClient, auth_headers, second_auth_headers, seeded_data):
    """Verifies that User 2 cannot access User 1's booking (returns 403 Forbidden)."""
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

    # User 1 can view own booking
    owner_res = client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert owner_res.status_code == 200

    # User 2 attempts to view User 1's booking -> 403
    unauth_res = client.get(f"/bookings/{booking_id}", headers=second_auth_headers)
    assert unauth_res.status_code == 403
    assert "permission" in unauth_res.json()["detail"].lower()


def test_cancel_booking_success(client: TestClient, auth_headers, seeded_data):
    """Verifies that the booking owner can cancel an active booking."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Cancel booking
    cancel_res = client.post(f"/bookings/{booking_id}/cancel", headers=auth_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Verify status in database
    get_res = client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert get_res.json()["status"] == "CANCELLED"


def test_cancel_already_cancelled_booking(client: TestClient, auth_headers, seeded_data):
    """Verifies that cancelling an already cancelled booking returns 400."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # Cancel once
    client.post(f"/bookings/{booking_id}/cancel", headers=auth_headers)

    # Cancel second time -> 400
    cancel_res2 = client.post(f"/bookings/{booking_id}/cancel", headers=auth_headers)
    assert cancel_res2.status_code == 400
    assert "already cancelled" in cancel_res2.json()["detail"].lower()


def test_cancel_another_users_booking(client: TestClient, auth_headers, second_auth_headers, seeded_data):
    """Verifies that a user cannot cancel another user's booking (403 Forbidden)."""
    c1 = seeded_data["centre_1"]
    t_cbc = seeded_data["test_cbc"]
    future_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    create_res = client.post(
        "/bookings/",
        json={"centre_id": c1.id, "test_id": t_cbc.id, "appointment_datetime": future_time},
        headers=auth_headers,
    )
    booking_id = create_res.json()["id"]

    # User 2 attempts to cancel User 1's booking
    res = client.post(f"/bookings/{booking_id}/cancel", headers=second_auth_headers)
    assert res.status_code == 403
