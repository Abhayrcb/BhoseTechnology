import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from html import escape

import httpx
from fastapi import HTTPException
from email_guardrails import _assert_safe_email

logger = logging.getLogger(__name__)
EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ["EMERGENT_EMAIL_KEY"]
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

def timestamp():
    return datetime.now(timezone.utc).isoformat()

async def send_email(*, to, subject, html, reply_to=None):
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if reply_to or EMAIL_REPLY_TO:
        payload["contact_email"] = reply_to or EMAIL_REPLY_TO
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{EMAIL_BASE_URL}/api/v1/email/send", headers={"X-Email-Key": EMAIL_KEY}, json=payload)
        response.raise_for_status()
        email_id = response.json().get("id")
        if not email_id:
            raise ValueError("Email provider did not return a message ID")
        return {"status": "accepted", "email_id": str(email_id), "error": None}
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        logger.error("Email provider rejected notification: HTTP %s", code)
        reasons = {401: "Email key is invalid. Check server email configuration.", 403: "Email provider access denied.",
                   422: "Email provider rejected the recipient or message.", 429: "Email provider rate limit reached. Retry later."}
        return {"status": "failed", "error": reasons.get(code, f"Email provider error (HTTP {code}). Retry later.")}
    except (httpx.RequestError, ValueError):
        logger.warning("Email send outcome could not be confirmed")
        return {"status": "unknown", "error": "Provider acceptance is unconfirmed. Check the inbox before retrying to avoid duplicates."}

def email_html(order, owner=False, store_name=None):
    brand = escape(store_name or EMAIL_FROM_NAME)
    items = "".join(
        f"<tr><td style='padding:10px 4px'>{escape(i['title'])}<br/><small>{escape(i['sku'])}</small></td>"
        f"<td>{i['quantity']}</td><td>INR {i['price']:,}</td><td>INR {i['price'] * i['quantity']:,}</td></tr>"
        for i in order["items"])
    intro = "A new order is ready for your attention." if owner else f"Hi {escape(order['customer_name'])}, your order has been placed."
    return f"""<table role='presentation' width='100%' style='max-width:700px;margin:auto;font-family:Arial,sans-serif;color:#142a2a'>
    <tr><td style='padding:28px'><h2>{brand}</h2><h1>Order {escape(order['order_number'])}</h1><p>{intro}</p>
    <p>Placed: {escape(order['created_at'])} · Status: {escape(order['status'])}</p>
    <table width='100%' style='border-collapse:collapse;text-align:left'><tr><th>Product / SKU</th><th>Qty</th><th>Unit price</th><th>Subtotal</th></tr>{items}</table>
    <p><strong>Order total: INR {order['total']:,}</strong></p><h3>Customer &amp; delivery</h3>
    <p>{escape(order['customer_name'])}<br/>{escape(order['customer_email'])}<br/>{escape(order['customer_phone'])}</p>
    <p>{escape(order['address'])}<br/>{escape(order['city'])} - {escape(order['pincode'])}</p>
    <p>No online payment was collected. The store will contact the customer before dispatch.</p>
    <p style='font-size:12px;color:#657575'>Sent by {escape(EMAIL_FROM_NAME)} for {brand}. We never ask for your password or card details by email.</p>
    </td></tr></table>"""

async def notify_recipient(db, order, settings, recipient):
    field = f"notifications.{recipient}"
    address = settings.get("owner_email") if recipient == "owner" else order["customer_email"]
    current = timestamp()
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=90)).isoformat()
    # Atomic lease prevents concurrent checkout/retry sends for the same recipient.
    acquired = await db.orders.update_one({"order_id": order["order_id"], f"{field}.status": {"$ne": "accepted"},
        "$or": [{f"{field}.status": {"$ne": "sending"}}, {f"{field}.updated_at": {"$lt": cutoff}}]},
        {"$set": {f"{field}.status": "sending", f"{field}.updated_at": current}})
    if not acquired.modified_count:
        return
    if not address:
        result = {"status": "not_configured", "error": "Store owner email is missing. Save it in Settings, then retry."}
    else:
        try:
            result = await send_email(to=address,
                subject=f"{'New order' if recipient == 'owner' else 'Order placed'} {order['order_number']}",
                html=email_html(order, recipient == "owner", settings.get("store_name")), reply_to=settings.get("owner_email"))
        except ValueError:
            result = {"status": "failed", "error": "Email content failed safety validation. Review store/order details."}
    result.update({"recipient": address, "updated_at": timestamp()})
    await db.orders.update_one({"order_id": order["order_id"]}, {"$set": {field: result}})

async def notify_order(db, order_id, recipient=None):
    order = await db.orders.find_one({"order_id": order_id}, {"_id": 0})
    if not order:
        return
    settings = await db.settings.find_one({"key": "store"}, {"_id": 0}) or {}
    await asyncio.gather(*(notify_recipient(db, order, settings, target) for target in ([recipient] if recipient else ["customer", "owner"])))

async def test_owner_email(db):
    settings = await db.settings.find_one({"key": "store"}, {"_id": 0}) or {}
    if not settings.get("owner_email"):
        raise HTTPException(400, "Save a store owner email in Settings first.")
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    lock = await db.settings.update_one({"key": "store", "$or": [{"email_test_at": {"$exists": False}}, {"email_test_at": {"$lt": cutoff}}]}, {"$set": {"email_test_at": timestamp()}})
    if not lock.modified_count:
        raise HTTPException(429, "Please wait a minute before sending another test email.")
    brand = escape(settings.get("store_name") or EMAIL_FROM_NAME)
    result = await send_email(to=settings["owner_email"], subject="Store order notification test",
        html=f"<h2>{brand}</h2><p>Your store owner notification address has been configured.</p><p>This is a test, not an order.</p><p>Sent by {escape(EMAIL_FROM_NAME)}.</p>", reply_to=settings["owner_email"])
    result.update({"recipient": settings["owner_email"], "updated_at": timestamp()})
    await db.settings.update_one({"key": "store"}, {"$set": {"email_test_result": result}})
    return result