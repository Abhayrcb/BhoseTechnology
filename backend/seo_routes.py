from urllib.parse import quote
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel
from seo_content import site_config, is_indexable, make_page, head_html


class SeoConfigOutput(BaseModel):
    site_url: str | None
    indexing_enabled: bool
    request_indexable: bool


class SeoPageOutput(BaseModel):
    title: str
    description: str
    canonical: str | None
    image: str | None
    robots: str
    site_name: str
    og_type: str
    schemas: list[dict]
    status_code: int
    body: str
    head: str


def create_seo_router(db):
    router = APIRouter(prefix="/api/seo", tags=["SEO"])
    site_config()  # Missing/invalid configuration fails early, never defaults to the preview domain.

    @router.get("/config", response_model=SeoConfigOutput)
    async def config(request: Request, hostname: str = Query(default="", max_length=253)):
        value = site_config()
        return {**value, "request_indexable": is_indexable(value, hostname or request.url.hostname or "")}

    @router.get("/page", response_model=SeoPageOutput)
    async def page(request: Request, path: str = Query(default="/", max_length=1024), hostname: str = Query(default="", max_length=253)):
        settings = await db.settings.find_one({"key": "store"}, {"_id": 0})
        path = path.rstrip("/") or "/"
        product, products = None, []
        if path.startswith("/product/") and path.count("/") == 2:
            product = await db.products.find_one({"product_id": path.split("/")[-1], "status": "active", "deleted_at": {"$exists": False}}, {"_id": 0})
        elif path == "/":
            products = await db.products.find({"status": "active", "stock_quantity": {"$gt": 0}, "deleted_at": {"$exists": False}}, {"_id": 0, "product_id": 1, "title": 1, "price": 1}).sort("created_at", -1).to_list(100)
        content = make_page(settings, site_config(), path, hostname or request.url.hostname or "", product, products)
        return {**content, "head": head_html(content)}

    @router.get("/robots.txt")
    async def robots(request: Request, hostname: str = Query(default="", max_length=253)):
        config = site_config()
        enabled = is_indexable(config, hostname or request.url.hostname or "")
        if enabled:
            text = f"User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /admin\nDisallow: /cart\nDisallow: /checkout\nSitemap: {config['site_url']}/sitemap.xml\n"
        else:
            # Allow reading the explicit noindex header/tags instead of risking URL-only indexing from a robots block.
            text = "User-agent: *\nAllow: /\n# Preview: all HTML pages send noindex. No sitemap URLs are published.\n"
        return Response(text, media_type="text/plain", headers={"X-Robots-Tag": "noindex", "Cache-Control": "no-store"})

    @router.get("/sitemap.xml")
    async def sitemap(request: Request, hostname: str = Query(default="", max_length=253)):
        config = site_config()
        ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
        register_namespace("", ns)
        root = Element(f"{{{ns}}}urlset")
        if is_indexable(config, hostname or request.url.hostname or ""):
            home = SubElement(root, f"{{{ns}}}url")
            SubElement(home, f"{{{ns}}}loc").text = f"{config['site_url']}/"
            products = await db.products.find({"status": "active", "deleted_at": {"$exists": False}}, {"_id": 0, "product_id": 1, "updated_at": 1, "created_at": 1}).to_list(49999)
            for product in products:
                node = SubElement(root, f"{{{ns}}}url")
                SubElement(node, f"{{{ns}}}loc").text = f"{config['site_url']}/product/{quote(product['product_id'], safe='')}"
                updated = product.get("updated_at") or product.get("created_at")
                if updated:
                    SubElement(node, f"{{{ns}}}lastmod").text = updated
        return Response(tostring(root, encoding="utf-8", xml_declaration=True), media_type="application/xml", headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})

    return router