"""SEO metadata and truthful structured data built from stored business records."""
import ipaddress
import json
import os
from html import escape
from urllib.parse import urlsplit, quote


def site_config():
    raw = os.environ["PUBLIC_SITE_URL"].strip().rstrip("/")
    enabled = os.environ["SEO_INDEXING_ENABLED"] == "true"
    if raw:
        parsed = urlsplit(raw)
        if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.port:
            raise ValueError("PUBLIC_SITE_URL must be a bare HTTPS origin without a path, credentials or port")
        host = parsed.hostname.lower()
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError("PUBLIC_SITE_URL must be a real domain, not an IP address")
        if "." not in host or host.endswith((".localhost", ".local", ".test", ".invalid", ".preview.emergentagent.com")):
            raise ValueError("PUBLIC_SITE_URL must not be a local/test/preview domain")
        raw = f"https://{host}"
    if enabled and not raw:
        raise ValueError("Set PUBLIC_SITE_URL before enabling SEO indexing")
    return {"site_url": raw or None, "indexing_enabled": bool(enabled and raw)}


def is_indexable(config, hostname):
    return bool(config["indexing_enabled"] and hostname.lower() == urlsplit(config["site_url"]).hostname)


def homepage_copy(settings):
    name = settings["store_name"]
    city = settings.get("seo_city", "Kolkata")
    region = settings.get("seo_region", "West Bengal")
    title = settings.get("seo_title") or f"{name} | Refurbished Laptops in {city}"
    description = settings.get("seo_description") or f"Shop second-hand and refurbished laptops at {name} in {city}, {region}. Compare specifications, condition and prices, then order online."
    return title, description


def business_schema(settings, site_url):
    city, region = settings.get("seo_city", "Kolkata"), settings.get("seo_region", "West Bengal")
    business = {"@context": "https://schema.org", "@type": "Organization", "name": settings["store_name"],
                "areaServed": {"@type": "City", "name": city, "containedInPlace": {"@type": "AdministrativeArea", "name": region}}}
    if site_url:
        business.update({"@id": f"{site_url}/#business", "url": f"{site_url}/"})
    # A service area is not a street address. Do not invent local-business address, hours or ratings.
    if settings.get("address"):
        business["@type"] = "ComputerStore"
        business["address"] = {"@type": "PostalAddress", "streetAddress": settings["address"], "addressLocality": city, "addressRegion": region, "addressCountry": "IN"}
    if settings.get("phone"):
        business["telephone"] = settings["phone"]
    return business


def product_schema(product, settings, canonical):
    schema = {"@context": "https://schema.org", "@type": "Product", "name": product["title"], "sku": product["sku"],
        "description": product["condition_description"], "brand": {"@type": "Brand", "name": product["brand"]},
        "offers": {"@type": "Offer", "priceCurrency": "INR", "price": product["price"], "itemCondition": "https://schema.org/UsedCondition",
            "availability": "https://schema.org/InStock" if product["stock_quantity"] > 0 else "https://schema.org/OutOfStock",
            "seller": {"@type": "Organization", "name": settings["store_name"]}}}
    if product.get("image_url", "").startswith(("https://", "http://")):
        schema["image"] = [product["image_url"]]
    if canonical:
        schema["url"] = canonical
        schema["offers"]["url"] = canonical
    return schema


def make_page(settings, config, path, hostname, product=None, products=None):
    path = path.rstrip("/") or "/"
    title, description = homepage_copy(settings)
    canonical = None
    image = None
    schemas = []
    status = 200
    public_page = path == "/" or product is not None
    if path == "/":
        canonical = f"{config['site_url']}/" if config["site_url"] else None
        schemas = [business_schema(settings, config["site_url"])]
        if config["site_url"]:
            schemas.append({"@context": "https://schema.org", "@type": "WebSite", "@id": f"{config['site_url']}/#website", "name": settings["store_name"], "url": canonical})
    elif product:
        title = f"{product['title']} | {settings['store_name']}"
        description = f"{product['title']} at {settings['store_name']}, {settings.get('seo_city', 'Kolkata')}. {product['processor']}, {product['ram_gb']}GB RAM, {product['storage_gb']}GB {product['storage_type']}. {product['condition_description']}"[:300]
        canonical = f"{config['site_url']}/product/{quote(product['product_id'], safe='')}" if config["site_url"] else None
        image = product.get("image_url") if product.get("image_url", "").startswith(("https://", "http://")) else None
        schemas = [product_schema(product, settings, canonical)]
        if canonical:
            schemas.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": settings["store_name"], "item": f"{config['site_url']}/"},
                {"@type": "ListItem", "position": 2, "name": product["title"], "item": canonical}]})
    elif path in ("/admin", "/cart", "/checkout"):
        title = f"{ {'/admin':'Admin', '/cart':'Your bag', '/checkout':'Checkout'}[path]} | {settings['store_name']}"
        description = "Private store workspace." if path == "/admin" else f"Your order at {settings['store_name']}."
    else:
        title, description, status = f"Page not found | {settings['store_name']}", "This page or laptop is no longer available.", 404
    indexable = public_page and is_indexable(config, hostname)
    return {"title": title, "description": description, "canonical": canonical, "image": image,
        "robots": "index, follow, max-image-preview:large" if indexable else "noindex, nofollow",
        "site_name": settings["store_name"], "og_type": "product" if product else "website", "schemas": schemas,
        "status_code": status, "body": fallback_body(settings, path, product, products or [], status)}


def fallback_body(settings, path, product, products, status):
    brand = escape(settings["store_name"])
    if status == 404:
        return f'<main><h1>Page not found</h1><p>This page or laptop is no longer available.</p><a href="/">Back to {brand}</a></main>'
    if path not in ("/",) and not product:
        return f'<main><h1>{brand}</h1><p>Open this page with JavaScript enabled.</p></main>'
    if product:
        return f'<main><a href="/">{brand}</a><h1>{escape(product["title"])}</h1><p>{escape(product["condition_description"])}</p><p>{escape(product["processor"])} · {product["ram_gb"]}GB RAM · {product["storage_gb"]}GB {escape(product["storage_type"])}</p><p>INR {product["price"]:,} · {product["stock_quantity"]} in stock</p></main>'
    city, region = escape(settings.get("seo_city", "Kolkata")), escape(settings.get("seo_region", "West Bengal"))
    links = "".join(f'<li><a href="/product/{quote(p["product_id"], safe="")}">{escape(p["title"])}</a> · INR {p["price"]:,}</li>' for p in products)
    return f'<main><h1>{brand}</h1><h2>Second-hand laptops in {city}</h2><p>Shop second-hand and refurbished laptops at {brand} in {city}, {region}. Compare specifications, condition and prices, then order online.</p><ul>{links}</ul></main>'


def head_html(page):
    def meta(attribute, key, value):
        return f'<meta data-seo-owned="true" {attribute}="{key}" content="{escape(str(value), quote=True)}">'
    tags = [f'<title data-seo-owned="true">{escape(page["title"])}</title>', meta("name", "description", page["description"]), meta("name", "robots", page["robots"])]
    for key, value in {"og:title": page["title"], "og:description": page["description"], "og:type": page["og_type"], "og:site_name": page["site_name"], "og:locale": "en_IN"}.items():
        tags.append(meta("property", key, value))
    for key, value in {"twitter:card": "summary_large_image" if page["image"] else "summary", "twitter:title": page["title"], "twitter:description": page["description"]}.items():
        tags.append(meta("name", key, value))
    if page["canonical"]:
        tags += [f'<link data-seo-owned="true" rel="canonical" href="{escape(page["canonical"], quote=True)}">', meta("property", "og:url", page["canonical"])]
    if page["image"]:
        tags += [meta("property", "og:image", page["image"]), meta("name", "twitter:image", page["image"])]
    for schema in page["schemas"]:
        safe_json = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
        tags.append(f'<script data-seo-owned="true" type="application/ld+json">{safe_json}</script>')
    return "\n".join(tags)