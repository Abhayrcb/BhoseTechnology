from dotenv import load_dotenv
load_dotenv()

import ipaddress
import logging
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from html import escape
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urlparse

import bcrypt
import httpx
import jwt
import hmac
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(__file__)
mongo = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = mongo[os.environ["DB_NAME"]]
JWT_SECRET = os.environ["JWT_SECRET"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"].lower()
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Laptop Lab")
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO")

app = FastAPI(title="Laptop Lab Store API")
origins = [x.strip() for x in os.environ.get("CORS_ORIGINS", "*").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class ProductInput(BaseModel):
    title: str
    brand: str
    category: str
    price: int = Field(gt=0)
    compare_at_price: Optional[int] = None
    condition_grade: str = "A"
    condition_description: str = "Professionally checked and ready to use."
    processor: str
    ram_gb: int = Field(gt=0)
    storage_type: str = "SSD"
    storage_gb: int = Field(gt=0)
    display: str = "14-inch Full HD"
    gpu: str = "Integrated"
    battery_health: str = "Tested"
    operating_system: str = "Windows 11 Pro"
    warranty_months: int = 3
    stock_quantity: int = Field(ge=0)
    image_url: str
    status: str = "active"

class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)

class OrderInput(BaseModel):
    customer_name: str = Field(min_length=2)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=7)
    address: str = Field(min_length=8)
    city: str = Field(min_length=2)
    pincode: str = Field(min_length=4)
    items: list[OrderItem]

class SettingsInput(BaseModel):
    store_name: str
    owner_email: Optional[EmailStr] = None
    phone: str = ""
    address: str = ""
    shipping_policy: str = "Free delivery across India. Orders are dispatched in 2–4 working days."
    return_policy: str = "7-day return support for verified manufacturing issues."
    warranty_default: str = "3 months store warranty"
    hero_title: str = "Good tech. Better value."
    hero_subtitle: str = "Professionally checked laptops, honestly described, ready for their next chapter."

def now():
    return datetime.now(timezone.utc).isoformat()

def token_for(email: str):
    return jwt.encode({"sub": email, "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=12)}, JWT_SECRET, algorithm="HS256")

async def admin_required(request: Request):
    header = request.headers.get("Authorization", "")
    token = header.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Admin login required")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "admin" or payload.get("sub") != ADMIN_EMAIL:
            raise HTTPException(403, "Admin access required")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired")

_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "send your password", "cvv", "seed phrase", "recovery phrase", "confirm your card number")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)
class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__(); self.tags=set(); self.urls=[]; self.anchors=[]; self.href=None; self.text=[]
    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower()); self.urls += [v for k,v in attrs if k.lower() in ("href","src") and v]
        if tag.lower() == "a": self.href=dict(attrs).get("href"); self.text=[]
    def handle_data(self, data):
        if self.href is not None: self.text.append(data)
    def handle_endtag(self, tag):
        if tag.lower()=="a" and self.href is not None: self.anchors.append((self.href,"".join(self.text))); self.href=None
def _host_ok(host):
    if not host or "xn--" in host: return False
    try: ipaddress.ip_address(host); return False
    except ValueError: pass
    return not any(host == s or host.endswith("."+s) for s in _SHORTENERS)
def _assert_safe_email(subject, html):
    scan=_EmailScan(); scan.feed(html)
    if scan.tags & {"form","input","textarea","select"}: raise ValueError("Unsafe email form")
    body=f"{subject}\n{html}".lower()
    if any(p in body for p in _CRED_ASK): raise ValueError("Unsafe credential request")
    for url in scan.urls:
        low=url.strip().lower()
        if low.startswith(("mailto:","tel:","cid:","#")): continue
        parsed=urlparse(low)
        if not low.startswith("https://") or not _host_ok(parsed.hostname or "") or parsed.username:
            raise ValueError("Unsafe email link")

async def send_email(*, to: str, subject: str, html: str):
    _assert_safe_email(subject, html)
    if not EMAIL_KEY: return None
    payload={"to":[to],"subject":subject,"html":html,"from_name":EMAIL_FROM_NAME}
    if EMAIL_REPLY_TO: payload["contact_email"] = EMAIL_REPLY_TO
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response=await client.post(f"{EMAIL_BASE_URL}/api/v1/email/send", headers={"X-Email-Key":EMAIL_KEY}, json=payload)
            response.raise_for_status(); return response.json().get("id")
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return None

def email_html(order, recipient_label):
    items="".join(f"<tr><td style='padding:8px 0'>{escape(i['title'])}</td><td style='padding:8px 0;text-align:right'>₹{i['price']:,}</td></tr>" for i in order["items"])
    return f"<table role='presentation' width='100%' style='max-width:620px;margin:0 auto;font-family:Arial,sans-serif;color:#0f172a'><tr><td style='padding:32px 20px'><p style='font-size:12px;letter-spacing:2px;color:#0d9488'>{escape(EMAIL_FROM_NAME.upper())}</p><h1 style='font-size:26px'>Order {escape(order['order_number'])}</h1><p>Hi {escape(recipient_label)}, your order has been placed successfully.</p><table width='100%'>{items}<tr><td style='padding:16px 0;border-top:1px solid #ddd'><strong>Total</strong></td><td style='padding:16px 0;border-top:1px solid #ddd;text-align:right'><strong>₹{order['total']:,}</strong></td></tr></table><p style='color:#64748b'>We’ll contact you at {escape(order['customer_phone'])} before dispatch.</p><p style='font-size:12px;color:#64748b'>Sent by {escape(EMAIL_FROM_NAME)}. We never ask for your password or card details by email.</p></td></tr></table>"

async def notify_order(order):
    await send_email(to=order["customer_email"], subject=f"Order {order['order_number']} placed", html=email_html(order, order["customer_name"]))
    settings=await db.settings.find_one({"key":"store"},{"_id":0})
    owner=(settings or {}).get("owner_email")
    if owner: await send_email(to=owner, subject=f"New order {order['order_number']}", html=email_html(order, "Store owner"))

@app.get("/api/")
async def root(): return {"message":"Laptop Lab API"}

@app.post("/api/auth/login")
async def login(data: LoginInput, request: Request):
    identifier=data.email.lower()
    attempt=await db.login_attempts.find_one({"identifier":identifier},{"_id":0})
    if attempt and attempt.get("locked_until","") > now():
        raise HTTPException(429,"Too many attempts. Try again in a few minutes.")
    if data.email.lower() != ADMIN_EMAIL or not hmac.compare_digest(data.password, ADMIN_PASSWORD):
        failed=(attempt or {}).get("failed",0)+1
        update={"identifier":identifier,"failed":failed,"locked_until":(datetime.now(timezone.utc)+timedelta(minutes=15)).isoformat() if failed >= 5 else ""}
        await db.login_attempts.replace_one({"identifier":identifier},update,upsert=True)
        raise HTTPException(401, "Invalid admin email or password")
    await db.login_attempts.delete_one({"identifier":identifier})
    return {"token": token_for(ADMIN_EMAIL), "email": ADMIN_EMAIL, "role":"admin"}

@app.get("/api/auth/me")
async def me(user=Depends(admin_required)): return {"email":user["sub"],"role":"admin"}

@app.get("/api/products")
async def products(search: str = "", brand: str = "", category: str = ""):
    query={"status":"active","stock_quantity":{"$gt":0}}
    if search: query["$or"]=[{"title":{"$regex":search,"$options":"i"}},{"brand":{"$regex":search,"$options":"i"}},{"sku":{"$regex":search,"$options":"i"}}]
    if brand: query["brand"]=brand
    if category: query["category"]=category
    return await db.products.find(query,{"_id":0}).sort("created_at",-1).to_list(100)

@app.get("/api/products/{product_id}")
async def product(product_id: str):
    item=await db.products.find_one({"product_id":product_id},{"_id":0})
    if not item: raise HTTPException(404,"Laptop not found")
    return item

@app.post("/api/orders")
async def create_order(data: OrderInput, background: BackgroundTasks):
    if not data.items: raise HTTPException(400,"Cart is empty")
    snapshots=[]; total=0
    for line in data.items:
        item=await db.products.find_one({"product_id":line.product_id,"status":"active","stock_quantity":{"$gte":line.quantity}},{"_id":0})
        if not item: raise HTTPException(409,"One of these laptops is no longer available")
        snapshots.append({"product_id":item["product_id"],"title":item["title"],"sku":item["sku"],"price":item["price"],"quantity":line.quantity})
        total += item["price"] * line.quantity
    order={"order_id":str(uuid.uuid4()),"order_number":f"LL-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:5].upper()}","customer_name":data.customer_name,"customer_email":str(data.customer_email).lower(),"customer_phone":data.customer_phone,"address":data.address,"city":data.city,"pincode":data.pincode,"items":snapshots,"total":total,"status":"PLACED","created_at":now()}
    reserved=[]
    try:
        for line in data.items:
            updated=await db.products.update_one({"product_id":line.product_id,"status":"active","stock_quantity":{"$gte":line.quantity}}, {"$inc":{"stock_quantity":-line.quantity}})
            if updated.modified_count != 1: raise HTTPException(409,"Stock changed, please try again")
            reserved.append(line)
        await db.orders.insert_one(order)
    except Exception:
        for line in reserved:
            await db.products.update_one({"product_id":line.product_id},{"$inc":{"stock_quantity":line.quantity}})
        raise
    background.add_task(notify_order, order)
    return {k:v for k,v in order.items() if k != "_id"}

@app.get("/api/admin/products")
async def admin_products(user=Depends(admin_required)):
    return await db.products.find({}, {"_id":0}).sort("created_at",-1).to_list(200)

@app.post("/api/admin/products")
async def add_product(data: ProductInput, user=Depends(admin_required)):
    doc=data.model_dump(); doc.update({"product_id":str(uuid.uuid4()),"sku":f"{data.brand[:4].upper()}-{uuid.uuid4().hex[:6].upper()}","created_at":now(),"updated_at":now()})
    await db.products.insert_one(doc); return await db.products.find_one({"product_id":doc["product_id"]},{"_id":0})

@app.put("/api/admin/products/{product_id}")
async def edit_product(product_id: str, data: ProductInput, user=Depends(admin_required)):
    result=await db.products.update_one({"product_id":product_id},{"$set":{**data.model_dump(),"updated_at":now()}})
    if not result.matched_count: raise HTTPException(404,"Product not found")
    return await db.products.find_one({"product_id":product_id},{"_id":0})

@app.delete("/api/admin/products/{product_id}")
async def delete_product(product_id: str, user=Depends(admin_required)):
    await db.products.update_one({"product_id":product_id},{"$set":{"status":"inactive","updated_at":now()}}); return {"status":"archived"}

@app.get("/api/admin/orders")
async def admin_orders(user=Depends(admin_required)):
    return await db.orders.find({}, {"_id":0}).sort("created_at",-1).to_list(200)

@app.patch("/api/admin/orders/{order_id}")
async def update_order(order_id: str, status: str, user=Depends(admin_required)):
    if status not in {"PLACED","PROCESSING","PACKED","SHIPPED","DELIVERED","CANCELLED"}: raise HTTPException(400,"Invalid status")
    result=await db.orders.update_one({"order_id":order_id},{"$set":{"status":status}})
    if not result.matched_count: raise HTTPException(404,"Order not found")
    return {"status":status}

@app.get("/api/settings")
async def get_settings():
    item=await db.settings.find_one({"key":"store"},{"_id":0})
    return item or {"key":"store","store_name":"Laptop Lab","hero_title":"Good tech. Better value.","hero_subtitle":"Professionally checked laptops, honestly described, ready for their next chapter.","shipping_policy":"Free delivery across India. Orders are dispatched in 2–4 working days.","return_policy":"7-day return support for verified manufacturing issues.","warranty_default":"3 months store warranty"}

@app.put("/api/admin/settings")
async def save_settings(data: SettingsInput, user=Depends(admin_required)):
    doc={"key":"store",**data.model_dump()}; await db.settings.replace_one({"key":"store"},doc,upsert=True); return doc

@app.on_event("startup")
async def seed():
    await db.products.create_index("product_id",unique=True)
    await db.login_attempts.create_index("identifier",unique=True)
    if await db.products.count_documents({}) == 0:
        samples=[
            {"title":"ThinkPad T14 Gen 2","brand":"Lenovo","category":"Business","price":34990,"compare_at_price":49990,"condition_grade":"A","condition_description":"Clean body, crisp keyboard, tested ports and excellent battery health.","processor":"Intel Core i5-1135G7","ram_gb":16,"storage_type":"NVMe SSD","storage_gb":512,"display":"14-inch Full HD IPS","gpu":"Intel Iris Xe","battery_health":"88% tested","operating_system":"Windows 11 Pro","warranty_months":3,"stock_quantity":1,"image_url":"https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=1200&q=85","status":"active"},
            {"title":"MacBook Air M1","brand":"Apple","category":"Student","price":52990,"compare_at_price":69990,"condition_grade":"A","condition_description":"Minimal signs of use with a bright display and smooth all-day performance.","processor":"Apple M1","ram_gb":8,"storage_type":"SSD","storage_gb":256,"display":"13.3-inch Retina","gpu":"8-core integrated","battery_health":"91% tested","operating_system":"macOS","warranty_months":3,"stock_quantity":1,"image_url":"https://images.unsplash.com/photo-1517336714739-489689fd1ca8?auto=format&fit=crop&w=1200&q=85","status":"active"},
            {"title":"EliteBook 840 G7","brand":"HP","category":"Business","price":29990,"compare_at_price":41990,"condition_grade":"B","condition_description":"A few honest marks on the lid, fully tested and dependable for daily work.","processor":"Intel Core i5-10210U","ram_gb":16,"storage_type":"SSD","storage_gb":512,"display":"14-inch Full HD","gpu":"Intel UHD","battery_health":"82% tested","operating_system":"Windows 11 Pro","warranty_months":3,"stock_quantity":1,"image_url":"https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=1200&q=85","status":"active"}
        ]
        for item in samples: item.update({"product_id":str(uuid.uuid4()),"sku":f"{item['brand'][:4].upper()}-{uuid.uuid4().hex[:6].upper()}","created_at":now(),"updated_at":now()})
        await db.products.insert_many(samples)
    if not await db.settings.find_one({"key":"store"}): await db.settings.insert_one({"key":"store","store_name":"Laptop Lab","hero_title":"Good tech. Better value.","hero_subtitle":"Professionally checked laptops, honestly described, ready for their next chapter.","shipping_policy":"Free delivery across India. Orders are dispatched in 2–4 working days.","return_policy":"7-day return support for verified manufacturing issues.","warranty_default":"3 months store warranty"})

@app.on_event("shutdown")
async def close(): mongo.close()