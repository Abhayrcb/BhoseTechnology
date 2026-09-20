import os
import uuid

import pytest
import requests


BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_EMAIL = "admin@laptoplab.com"
ADMIN_PASSWORD = "ChangeMe123!"


@pytest.fixture(scope="module")
def client():
    return requests.Session()


@pytest.fixture(scope="module")
def token(client):
    response = client.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["role"] == "admin" and data["email"] == ADMIN_EMAIL
    return data["token"]


def test_public_products_and_filters(client):
    response = client.get(f"{BASE_URL}/api/products")
    assert response.status_code == 200
    products = response.json()
    assert products and all("product_id" in item and "_id" not in item for item in products)
    brand = products[0]["brand"]
    filtered = client.get(f"{BASE_URL}/api/products", params={"brand": brand})
    assert filtered.status_code == 200
    assert all(item["brand"] == brand for item in filtered.json())


def test_auth_protection_and_me(client, token):
    assert client.get(f"{BASE_URL}/api/admin/products").status_code == 401
    response = client.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"email": ADMIN_EMAIL, "role": "admin"}


def test_admin_product_create_get_and_archive(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": f"TEST Laptop {uuid.uuid4().hex[:6]}", "brand": "Lenovo", "category": "Business", "price": 12345,
               "processor": "TEST CPU", "ram_gb": 8, "storage_type": "SSD", "storage_gb": 256,
               "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853", "stock_quantity": 1}
    created = client.post(f"{BASE_URL}/api/admin/products", json=payload, headers=headers)
    assert created.status_code == 200, created.text
    item = created.json()
    assert item["title"] == payload["title"] and "_id" not in item
    archived = client.delete(f"{BASE_URL}/api/admin/products/{item['product_id']}", headers=headers)
    assert archived.status_code == 200 and archived.json()["status"] == "archived"


def test_order_requires_customer_email(client):
    products = client.get(f"{BASE_URL}/api/products").json()
    if not products:
        pytest.skip("No available seeded product")
    payload = {"customer_name": "Test Buyer", "customer_phone": "9876543210", "address": "Test street 123",
               "city": "Pune", "pincode": "411001", "items": [{"product_id": products[0]["product_id"], "quantity": 1}]}
    response = client.post(f"{BASE_URL}/api/orders", json=payload)
    assert response.status_code == 422
