"""Diagnostic centres and tests API tests."""

from fastapi.testclient import TestClient


def test_list_centres(client: TestClient, seeded_data):
    """Verifies retrieval of diagnostic centres with test offerings and pricing."""
    response = client.get("/centres/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [c["name"] for c in data]
    assert "Apollo Diagnostic Centre" in names
    assert "Metropolis Healthcare" in names


def test_get_centre_by_id(client: TestClient, seeded_data):
    """Verifies retrieval of a single diagnostic centre by ID."""
    c1 = seeded_data["centre_1"]
    response = client.get(f"/centres/{c1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == c1.name
    assert data["location"] == c1.location
    assert len(data["centre_tests"]) == 2


def test_get_centre_invalid_id(client: TestClient):
    """Verifies that non-existent centre ID returns 404."""
    response = client.get("/centres/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_tests(client: TestClient, seeded_data):
    """Verifies retrieval of global diagnostic tests catalogue."""
    response = client.get("/tests/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    test_names = [t["name"] for t in data]
    assert "Complete Blood Count (CBC)" in test_names
    assert "Lipid Profile" in test_names


def test_get_test_by_id(client: TestClient, seeded_data):
    """Verifies retrieval of a single diagnostic test by ID."""
    t_cbc = seeded_data["test_cbc"]
    response = client.get(f"/tests/{t_cbc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == t_cbc.name
    assert data["description"] == t_cbc.description


def test_get_test_invalid_id(client: TestClient):
    """Verifies that non-existent test ID returns 404."""
    response = client.get("/tests/9999")
    assert response.status_code == 404


def test_get_centre_tests(client: TestClient, seeded_data):
    """Verifies retrieval of specific tests and pricing for a diagnostic centre."""
    c1 = seeded_data["centre_1"]
    response = client.get(f"/centres/{c1.id}/tests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Verify pricing
    prices = {item["test"]["name"]: float(item["price"]) for item in data if item["test"]}
    assert prices["Complete Blood Count (CBC)"] == 500.00
    assert prices["Lipid Profile"] == 900.00


def test_create_centre_and_add_test(client: TestClient):
    """Verifies creation of new centre and mapping test with price."""
    # Create centre
    c_res = client.post("/centres/", json={"name": "New Diagnostics", "location": "Pune"})
    assert c_res.status_code == 201
    centre_id = c_res.json()["id"]

    # Create test
    t_res = client.post(
        "/tests/",
        json={"name": "Urine Routine", "description": "Kidney and metabolic assessment"},
    )
    assert t_res.status_code == 201
    test_id = t_res.json()["id"]

    # Map test to centre
    map_res = client.post(f"/centres/{centre_id}/tests", json={"test_id": test_id, "price": 350.00})
    assert map_res.status_code == 201
    assert float(map_res.json()["price"]) == 350.00
