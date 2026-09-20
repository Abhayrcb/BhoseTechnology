import json
import os
import re
import uuid

import pytest
import requests
from dotenv import dotenv_values


# SEO public endpoint checks against the external preview URL
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or dotenv_values("/app/frontend/.env").get("REACT_APP_BACKEND_URL", "")).rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL is required"


def _read_admin_credentials():
    text = open("/app/memory/test_credentials.md", "r", encoding="utf-8").read()
    email = re.search(r"-\s*Email:\s*`([^`]+)`", text)
    password = re.search(r"-\s*Password:\s*`([^`]+)`", text)
    if not email or not password:
        pytest.skip("Admin credentials missing from /app/memory/test_credentials.md")
    return email.group(1), password.group(1)


def _ld_json_blocks(html: str):
    blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    parsed = []
    for block in blocks:
        parsed.append(json.loads(block.strip()))
    return parsed


@pytest.fixture(scope="module")
def client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_headers(client):
    email, password = _read_admin_credentials()
    response = client.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=20)
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def restore_store_settings(client, auth_headers):
    original = client.get(f"{BASE_URL}/api/settings", timeout=20)
    assert original.status_code == 200, original.text
    original_data = original.json()
    yield
    restore_payload = {
        "store_name": original_data.get("store_name", "Bhose Technology"),
        "owner_email": original_data.get("owner_email"),
        "phone": original_data.get("phone", ""),
        "address": original_data.get("address", ""),
        "shipping_policy": original_data.get("shipping_policy", ""),
        "return_policy": original_data.get("return_policy", ""),
        "warranty_default": original_data.get("warranty_default", ""),
        "hero_title": original_data.get("hero_title", ""),
        "hero_subtitle": original_data.get("hero_subtitle", ""),
        "seo_city": original_data.get("seo_city", "Kolkata"),
        "seo_region": original_data.get("seo_region", "West Bengal"),
        "seo_title": original_data.get("seo_title", ""),
        "seo_description": original_data.get("seo_description", ""),
    }
    client.put(f"{BASE_URL}/api/admin/settings", headers=auth_headers, json=restore_payload, timeout=20)


def test_home_raw_html_seo_tags_and_fallback_links(client):
    response = client.get(f"{BASE_URL}/", timeout=20)
    assert response.status_code == 200
    assert response.headers.get("x-robots-tag") == "noindex, nofollow"
    html = response.text

    assert html.count("<title data-seo-owned=\"true\">") == 1
    assert "Bhose Technology" in html
    assert "Kolkata" in html
    assert html.count('name="description"') >= 1
    assert 'name="robots" content="noindex, nofollow"' in html

    assert 'property="og:title"' in html
    assert 'property="og:description"' in html
    assert 'name="twitter:title"' in html
    assert 'name="twitter:description"' in html

    schemas = _ld_json_blocks(html)
    org = next((x for x in schemas if x.get("@type") in {"Organization", "ComputerStore"}), None)
    assert org is not None
    assert "Kolkata" in json.dumps(org)
    assert "West Bengal" in json.dumps(org)
    assert "review" not in json.dumps(org).lower()
    assert "aggregaterating" not in json.dumps(org).lower()

    assert '<div id="root"><main>' in html
    assert "Second-hand laptops in Kolkata" in html
    assert re.search(r'href="/product/[^"]+"', html)
    assert "Emergent" not in re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.S | re.I).group(1)


def test_seo_config_and_discovery_routes_preview_mode(client):
    config = client.get(f"{BASE_URL}/api/seo/config", timeout=20)
    assert config.status_code == 200
    data = config.json()
    assert data["site_url"] is None
    assert data["indexing_enabled"] is False
    assert data["request_indexable"] is False

    robots = client.get(f"{BASE_URL}/robots.txt", timeout=20)
    assert robots.status_code == 200
    assert robots.headers["content-type"].startswith("text/plain")
    assert "Allow: /" in robots.text
    assert "Sitemap:" not in robots.text

    sitemap = client.get(f"{BASE_URL}/sitemap.xml", timeout=20)
    assert sitemap.status_code == 200
    assert sitemap.headers["content-type"].startswith("application/xml")
    assert "<urlset" in sitemap.text and "<url>" not in sitemap.text


def test_product_page_schema_in_preview_has_no_fake_canonical(client):
    products = client.get(f"{BASE_URL}/api/products", timeout=20)
    assert products.status_code == 200
    active = products.json()
    assert active
    product = active[0]

    page = client.get(f"{BASE_URL}/product/{product['product_id']}", timeout=20)
    assert page.status_code == 200
    html = page.text
    assert page.headers.get("x-robots-tag") == "noindex, nofollow"
    assert f"{product['title']} |" in html
    assert 'rel="canonical"' not in html
    assert 'property="og:url"' not in html

    schema = next(x for x in _ld_json_blocks(html) if x.get("@type") == "Product")
    assert schema["offers"]["priceCurrency"] == "INR"
    assert schema["offers"]["itemCondition"] == "https://schema.org/UsedCondition"
    assert schema["offers"]["availability"] == "https://schema.org/InStock"
    assert schema["sku"] == product["sku"]


def test_active_zero_stock_still_has_valid_page_and_outofstock_schema(client, auth_headers):
    pid = None
    payload = {
        "title": f"TEST_SEO_OOS_{uuid.uuid4().hex[:6]}",
        "brand": "Lenovo",
        "category": "Business",
        "price": 25000,
        "compare_at_price": 28000,
        "condition_grade": "B",
        "condition_description": "TEST seo out-of-stock",
        "processor": "Intel Core i5",
        "ram_gb": 8,
        "storage_type": "SSD",
        "storage_gb": 256,
        "display": "14 inch",
        "gpu": "Integrated",
        "battery_health": "Good",
        "operating_system": "Windows 11",
        "warranty_months": 3,
        "stock_quantity": 0,
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=85",
        "status": "active",
    }
    try:
        created = client.post(f"{BASE_URL}/api/admin/products", headers=auth_headers, json=payload, timeout=20)
        assert created.status_code == 200, created.text
        pid = created.json()["product_id"]
        page = client.get(f"{BASE_URL}/product/{pid}", timeout=20)
        assert page.status_code == 200
        schema = next(x for x in _ld_json_blocks(page.text) if x.get("@type") == "Product")
        assert schema["offers"]["availability"] == "https://schema.org/OutOfStock"
    finally:
        if pid:
            client.delete(f"{BASE_URL}/api/admin/products/{pid}", headers=auth_headers, timeout=20)


def test_inactive_missing_unknown_routes_return_404_and_noindex(client, auth_headers):
    pid = None
    payload = {
        "title": f"TEST_SEO_INACTIVE_{uuid.uuid4().hex[:6]}",
        "brand": "HP",
        "category": "Business",
        "price": 22000,
        "compare_at_price": 26000,
        "condition_grade": "B",
        "condition_description": "TEST inactive product",
        "processor": "Intel Core i5",
        "ram_gb": 8,
        "storage_type": "SSD",
        "storage_gb": 256,
        "display": "14 inch",
        "gpu": "Integrated",
        "battery_health": "Good",
        "operating_system": "Windows 11",
        "warranty_months": 3,
        "stock_quantity": 1,
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=85",
        "status": "inactive",
    }
    try:
        created = client.post(f"{BASE_URL}/api/admin/products", headers=auth_headers, json=payload, timeout=20)
        assert created.status_code == 200, created.text
        pid = created.json()["product_id"]

        inactive = client.get(f"{BASE_URL}/product/{pid}", timeout=20)
        assert inactive.status_code == 404
        assert inactive.headers.get("x-robots-tag") == "noindex, nofollow"

        missing = client.get(f"{BASE_URL}/product/not-a-real-product-id", timeout=20)
        assert missing.status_code == 404
        assert missing.headers.get("x-robots-tag") == "noindex, nofollow"

        unknown = client.get(f"{BASE_URL}/unknown-page-for-seo-test", timeout=20)
        assert unknown.status_code == 404
        assert unknown.headers.get("x-robots-tag") == "noindex, nofollow"
    finally:
        if pid:
            client.delete(f"{BASE_URL}/api/admin/products/{pid}", headers=auth_headers, timeout=20)


def test_admin_cart_checkout_pages_noindex(client):
    for path in ["/admin", "/cart", "/checkout"]:
        response = client.get(f"{BASE_URL}{path}", timeout=20)
        assert response.status_code == 200
        assert response.headers.get("x-robots-tag") == "noindex, nofollow"
        assert 'name="robots" content="noindex, nofollow"' in response.text


def test_search_appearance_settings_persist_and_validation(client, auth_headers, restore_store_settings):
    current = client.get(f"{BASE_URL}/api/settings", timeout=20).json()
    updated_name = f"{current['store_name']} SEO TEST"
    save_payload = {
        "store_name": updated_name,
        "owner_email": current.get("owner_email"),
        "phone": current.get("phone", ""),
        "address": current.get("address", ""),
        "shipping_policy": current.get("shipping_policy", ""),
        "return_policy": current.get("return_policy", ""),
        "warranty_default": current.get("warranty_default", ""),
        "hero_title": current.get("hero_title", ""),
        "hero_subtitle": current.get("hero_subtitle", ""),
        "seo_city": "Kolkata",
        "seo_region": "West Bengal",
        "seo_title": "Bhose Technology Kolkata Refurbished Laptops",
        "seo_description": "Used and refurbished laptops in Kolkata with clear specs and stock status.",
    }
    saved = client.put(f"{BASE_URL}/api/admin/settings", headers=auth_headers, json=save_payload, timeout=20)
    assert saved.status_code == 200, saved.text
    assert saved.json()["seo_title"] == save_payload["seo_title"]

    page = client.get(f"{BASE_URL}/", timeout=20)
    assert save_payload["seo_title"] in page.text
    assert save_payload["seo_description"] in page.text

    cleared = {**save_payload, "seo_title": "", "seo_description": ""}
    cleared_resp = client.put(f"{BASE_URL}/api/admin/settings", headers=auth_headers, json=cleared, timeout=20)
    assert cleared_resp.status_code == 200
    fallback_page = client.get(f"{BASE_URL}/", timeout=20)
    assert f"{updated_name} | Refurbished Laptops in Kolkata" in fallback_page.text

    invalid_city = {**cleared, "seo_city": ""}
    invalid_resp = client.put(f"{BASE_URL}/api/admin/settings", headers=auth_headers, json=invalid_city, timeout=20)
    assert invalid_resp.status_code == 422
