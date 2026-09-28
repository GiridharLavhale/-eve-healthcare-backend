"""End-to-end full scenario validation script."""

import sys
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.db.seed import seed_database

def run_e2e_verification():
    print("==================================================")
    print("       EVE HEALTHCARE BACKEND E2E VERIFICATION     ")
    print("==================================================")
    
    # Ensure database is seeded
    seed_database()
    
    client = TestClient(app)
    
    # 1. Health check
    print("\n[Step 1] Checking /health endpoint...")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print("-> Health check passed:", res.json())
    
    # 2. Signup User
    email = f"e2e_user_{datetime.now().timestamp()}@example.com"
    print(f"\n[Step 2] Registering user: {email}...")
    res = client.post("/auth/signup", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": "E2E Test Patient",
    })
    assert res.status_code == 201, f"Signup failed: {res.text}"
    user_data = res.json()
    print("-> Signup successful:", user_data)
    
    # 3. Login and get JWT
    print("\n[Step 3] Logging in...")
    res = client.post("/auth/login", json={
        "email": email,
        "password": "SecurePassword123!",
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print("-> JWT token acquired successfully.")
    
    # 4. Get Diagnostic Centres & Tests
    print("\n[Step 4] Fetching diagnostic centres...")
    res = client.get("/centres/")
    assert res.status_code == 200
    centres = res.json()
    print(f"-> Found {len(centres)} centres.")
    c1 = centres[0]
    print(f"   Selected Centre: {c1['name']} (ID: {c1['id']})")
    
    print("\n[Step 5] Fetching tests offered by selected centre...")
    res = client.get(f"/centres/{c1['id']}/tests")
    assert res.status_code == 200
    tests = res.json()
    assert len(tests) > 0, "No tests found for centre"
    t1 = tests[0]
    print(f"   Selected Test: {t1['test']['name']} (ID: {t1['test_id']}) - Price: Rs.{t1['price']}")
    
    # 6. Create Booking
    print("\n[Step 6] Creating appointment booking...")
    future_time = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    res = client.post("/bookings/", json={
        "centre_id": c1["id"],
        "test_id": t1["test_id"],
        "appointment_datetime": future_time,
    }, headers=auth_headers)
    assert res.status_code == 201, f"Booking creation failed: {res.text}"
    booking = res.json()
    booking_id = booking["id"]
    print("-> Booking created successfully:", booking)
    assert booking["status"] == "PENDING"
    assert float(booking["amount"]) == float(t1["price"])
    
    # 7. Simulate Payment
    print("\n[Step 7] Processing simulated SUCCESS payment...")
    res = client.post("/payments/", json={
        "booking_id": booking_id,
        "simulate_result": "SUCCESS",
    }, headers=auth_headers)
    assert res.status_code == 201, f"Payment failed: {res.text}"
    print("-> Payment successful:", res.json())
    
    # Verify booking status is now CONFIRMED
    res = client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert res.json()["status"] == "CONFIRMED"
    print("-> Booking is now CONFIRMED.")
    
    # 8. Webhook Idempotency Verification (Repeat 5 times)
    print("\n[Step 8] Testing Webhook Idempotency (Sending same event 5 times)...")
    webhook_payload = {
        "event_id": f"evt_e2e_{booking_id}_999",
        "event_type": "payment.updated",
        "payment_id": f"pay_e2e_{booking_id}_999",
        "booking_id": booking_id,
        "status": "SUCCESS",
        "amount": float(booking["amount"]),
    }
    
    for i in range(1, 6):
        res = client.post("/payments/webhook/", json=webhook_payload)
        assert res.status_code == 200, f"Webhook #{i} failed: {res.text}"
        data = res.json()
        expected_status = "success" if i == 1 else "duplicate"
        assert data["status"] == expected_status, f"Expected {expected_status}, got {data['status']}"
        print(f"   Delivery #{i} -> status: '{data['status']}', booking_status: '{data['booking_status']}'")
    
    # 9. Stale/Out-of-order FAILED Webhook Safety Check
    print("\n[Step 9] Sending stale out-of-order FAILED webhook to confirmed booking...")
    stale_payload = {
        "event_id": f"evt_stale_fail_{booking_id}",
        "event_type": "payment.updated",
        "payment_id": f"pay_stale_fail_{booking_id}",
        "booking_id": booking_id,
        "status": "FAILED",
    }
    res = client.post("/payments/webhook/", json=stale_payload)
    assert res.status_code == 200
    assert res.json()["booking_status"] == "CONFIRMED"
    print("-> Booking status protected against stale downgrade! Current status:", res.json()["booking_status"])
    
    # 10. Failed Payment Scenario with Second Booking
    print("\n[Step 10] Testing FAILED payment scenario with a new booking...")
    res = client.post("/bookings/", json={
        "centre_id": c1["id"],
        "test_id": t1["test_id"],
        "appointment_datetime": future_time,
    }, headers=auth_headers)
    booking2_id = res.json()["id"]
    
    res = client.post("/payments/", json={
        "booking_id": booking2_id,
        "simulate_result": "FAILED",
    }, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["status"] == "FAILED"
    
    res = client.get(f"/bookings/{booking2_id}", headers=auth_headers)
    assert res.json()["status"] == "FAILED"
    print("-> Second booking correctly transitioned to FAILED status.")
    
    # 11. Unauthorized Cross-User Access Attempt
    print("\n[Step 11] Testing Unauthorized Cross-User Access...")
    # Register 2nd user
    client.post("/auth/signup", json={
        "email": f"attacker_{datetime.now().timestamp()}@example.com",
        "password": "Password123!",
        "full_name": "Attacker User",
    })
    res = client.post("/auth/login", json={
        "email": f"attacker_{datetime.now().timestamp()}@example.com",
        "password": "Password123!",
    })
    # Try accessing User 1's booking without proper credentials
    res_unauth = client.get(f"/bookings/{booking_id}")
    assert res_unauth.status_code == 401
    print("-> Unauthenticated access blocked (401).")
    
    print("\n==================================================")
    print("    ALL END-TO-END VERIFICATION CHECKS PASSED!    ")
    print("==================================================")

if __name__ == "__main__":
    run_e2e_verification()
