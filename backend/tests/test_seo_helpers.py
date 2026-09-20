import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


sys.path.append("/app/backend")
from seo_content import head_html, is_indexable, make_page, site_config  # noqa: E402
from seo_routes import create_seo_router  # noqa: E402


# SEO helper + router behavior in isolated env (no permanent .env changes)
class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, _limit):
        return self.rows


class FakeCollection:
    def __init__(self, rows):
        self.rows = rows

    async def find_one(self, query, _projection=None):
        if query == {"key": "store"}:
            return self.rows
        for row in self.rows:
            ok = True
            for key, value in query.items():
                if key == "deleted_at":
                    if "$exists" in value and value["$exists"] is False and "deleted_at" in row:
                        ok = False
                elif row.get(key) != value:
                    ok = False
            if ok:
                return row
        return None

    def find(self, query, _projection=None):
        out = []
        for row in self.rows:
            if query.get("status") and row.get("status") != query["status"]:
                continue
            if query.get("deleted_at", {}).get("$exists") is False and "deleted_at" in row:
                continue
            stock_rule = query.get("stock_quantity", {})
            if "$gt" in stock_rule and not (row.get("stock_quantity", 0) > stock_rule["$gt"]):
                continue
            out.append(row)
        return FakeCursor(out)


class FakeDB:
    def __init__(self):
        self.settings = FakeCollection(
            {
                "key": "store",
                "store_name": "Bhose Technology",
                "seo_city": "Kolkata",
                "seo_region": "West Bengal",
                "seo_title": "",
                "seo_description": "",
                "address": "",
                "phone": "",
            }
        )
        self.products = FakeCollection(
            [
                {
                    "product_id": "active-instock",
                    "title": "ThinkPad X1",
                    "sku": "LENO-ABC123",
                    "brand": "Lenovo",
                    "condition_description": "Used, tested",
                    "processor": "i7",
                    "ram_gb": 16,
                    "storage_gb": 512,
                    "storage_type": "SSD",
                    "price": 50000,
                    "stock_quantity": 2,
                    "status": "active",
                    "created_at": "2026-01-01T00:00:00Z",
                },
                {
                    "product_id": "active-outstock",
                    "title": "Latitude 7490",
                    "sku": "DELL-DEF456",
                    "brand": "Dell",
                    "condition_description": "Used, tested",
                    "processor": "i5",
                    "ram_gb": 8,
                    "storage_gb": 256,
                    "storage_type": "SSD",
                    "price": 30000,
                    "stock_quantity": 0,
                    "status": "active",
                    "created_at": "2026-01-02T00:00:00Z",
                },
                {
                    "product_id": "inactive",
                    "title": "Inactive",
                    "sku": "INAC-111111",
                    "brand": "HP",
                    "condition_description": "Inactive",
                    "processor": "i3",
                    "ram_gb": 4,
                    "storage_gb": 128,
                    "storage_type": "SSD",
                    "price": 10000,
                    "stock_quantity": 4,
                    "status": "inactive",
                    "created_at": "2026-01-03T00:00:00Z",
                },
                {
                    "product_id": "deleted",
                    "title": "Deleted",
                    "sku": "DELE-222222",
                    "brand": "Acer",
                    "condition_description": "Deleted",
                    "processor": "i3",
                    "ram_gb": 4,
                    "storage_gb": 128,
                    "storage_type": "SSD",
                    "price": 10000,
                    "stock_quantity": 4,
                    "status": "active",
                    "deleted_at": "2026-01-04T00:00:00Z",
                    "created_at": "2026-01-04T00:00:00Z",
                },
            ]
        )


def test_site_config_validation(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "")
    monkeypatch.setenv("SEO_INDEXING_ENABLED", "false")
    cfg = site_config()
    assert cfg == {"site_url": None, "indexing_enabled": False}

    monkeypatch.setenv("SEO_INDEXING_ENABLED", "true")
    with pytest.raises(ValueError):
        site_config()

    monkeypatch.setenv("PUBLIC_SITE_URL", "https://order-mail-system.preview.emergentagent.com")
    with pytest.raises(ValueError):
        site_config()

    monkeypatch.setenv("PUBLIC_SITE_URL", "https://bhose-technology.in")
    monkeypatch.setenv("SEO_INDEXING_ENABLED", "true")
    cfg = site_config()
    assert cfg["site_url"] == "https://bhose-technology.in"
    assert cfg["indexing_enabled"] is True


def test_is_indexable_hostname_gating():
    cfg = {"site_url": "https://bhose-technology.in", "indexing_enabled": True}
    assert is_indexable(cfg, "bhose-technology.in") is True
    assert is_indexable(cfg, "order-mail-system.preview.emergentagent.com") is False


def test_make_page_and_head_html_escape_and_schema():
    settings = {
        "store_name": "Bhose \"Tech\" <script>",
        "seo_city": "Kolkata",
        "seo_region": "West Bengal",
        "seo_title": "",
        "seo_description": "",
    }
    cfg = {"site_url": "https://bhose-technology.in", "indexing_enabled": True}
    product = {
        "product_id": "unsafe/id",
        "title": "ThinkPad <script>alert(1)</script>",
        "sku": "LENO-ABC123",
        "brand": "Lenovo",
        "condition_description": "Good \"quoted\" condition",
        "processor": "i5",
        "ram_gb": 8,
        "storage_gb": 256,
        "storage_type": "SSD",
        "price": 42000,
        "stock_quantity": 0,
        "image_url": "https://images.example.com/x.jpg",
    }

    page = make_page(settings, cfg, "/product/unsafe/id", "bhose-technology.in", product=product)
    assert page["canonical"] == "https://bhose-technology.in/product/unsafe%2Fid"
    assert page["robots"].startswith("index")
    assert page["schemas"][0]["offers"]["availability"] == "https://schema.org/OutOfStock"

    html = head_html(page)
    assert "<script>alert(1)</script>" not in html
    assert "\\u003cscript" in html


def test_router_robots_and_sitemap_indexable_only_active_nondeleted(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "https://bhose-technology.in")
    monkeypatch.setenv("SEO_INDEXING_ENABLED", "true")

    app = FastAPI()
    app.include_router(create_seo_router(FakeDB()))
    client = TestClient(app)

    robots_index = client.get("/api/seo/robots.txt", params={"hostname": "bhose-technology.in"})
    assert robots_index.status_code == 200
    assert "Sitemap: https://bhose-technology.in/sitemap.xml" in robots_index.text

    robots_preview = client.get("/api/seo/robots.txt", params={"hostname": "order-mail-system.preview.emergentagent.com"})
    assert robots_preview.status_code == 200
    assert "Preview: all HTML pages send noindex" in robots_preview.text

    sitemap = client.get("/api/seo/sitemap.xml", params={"hostname": "bhose-technology.in"})
    xml = sitemap.text
    assert sitemap.status_code == 200
    assert "https://bhose-technology.in/" in xml
    assert "product/active-instock" in xml
    assert "product/active-outstock" in xml
    assert "product/inactive" not in xml
    assert "product/deleted" not in xml
    assert "/admin" not in xml and "/cart" not in xml and "/checkout" not in xml


def test_router_page_home_and_404(monkeypatch):
    monkeypatch.setenv("PUBLIC_SITE_URL", "")
    monkeypatch.setenv("SEO_INDEXING_ENABLED", "false")

    app = FastAPI()
    app.include_router(create_seo_router(FakeDB()))
    client = TestClient(app)

    home = client.get("/api/seo/page", params={"path": "/", "hostname": "order-mail-system.preview.emergentagent.com"})
    assert home.status_code == 200
    assert home.json()["robots"] == "noindex, nofollow"
    assert "Second-hand laptops in Kolkata" in home.json()["body"]

    missing = client.get("/api/seo/page", params={"path": "/not-found", "hostname": "order-mail-system.preview.emergentagent.com"})
    assert missing.status_code == 200
    assert missing.json()["status_code"] == 404
    assert missing.json()["robots"] == "noindex, nofollow"
