from dotenv import load_dotenv
load_dotenv()

import logging
import os
import re
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Optional, Literal

import jwt
import hmac
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from starlette.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from email_service import notify_order, test_owner_email, EMAIL_FROM_NAME
from reports import STORE_TZ, day_bounds, workbook_bytes, pdf_bytes
from seo_routes import create_seo_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(__file__)
mongo = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = mongo[os.environ["DB_NAME"]]
JWT_SECRET = os.environ["JWT_SECRET"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"].lower()
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

app = FastAPI(title="Laptop Lab Store API")
origins = [x.strip() for x in os.environ.get("CORS_ORIGINS", "*").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(create_seo_router(db))

class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class ProductInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    brand: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    price: int = Field(gt=0)
    compare_at_price: Optional[int] = Field(default=None, gt=0)
    condition_grade: Literal["A", "B", "C"] = "A"
    condition_description: str = Field(default="Professionally checked and ready to use.", min_length=1, max_length=5000)
    processor: str = Field(min_length=1, max_length=200)
    ram_gb: int = Field(gt=0)
    storage_type: str = "SSD"
    storage_gb: int = Field(gt=0)
    display: str = "14-inch Full HD"
    gpu: str = "Integrated"
    battery_health: str = "Tested"
    operating_system: str = "Windows 11 Pro"
    warranty_months: int = Field(default=3, ge=0)
    stock_quantity: int = Field(ge=0)
    image_url: str
    status: Literal["active", "inactive"] = "active"

class ProductOutput(ProductInput):
    product_id: str
    sku: str
    created_at: str
    updated_at: Optional[str] = None

class StockInput(BaseModel):
    stock_quantity: int = Field(ge=0)
    expected_stock: int = Field(ge=0)

class ProductUpdate(ProductInput):
    expected_stock: int = Field(ge=0)

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
    model_config = ConfigDict(str_strip_whitespace=True)
    store_name: str = Field(min_length=1, max_length=80)
    owner_email: Optional[EmailStr] = None
    phone: str = ""
    address: str = ""
    shipping_policy: str = "Free delivery across India. Orders are dispatched in 2–4 working days."
    return_policy: str = "7-day return support for verified manufacturing issues."
    warranty_default: str = "3 months store warranty"
    hero_title: str = "Good tech. Better value."
    hero_subtitle: str = "Professionally checked laptops, honestly described, ready for their next chapter."
    seo_city: str = Field(default="Kolkata", min_length=1, max_length=60)
    seo_region: str = Field(default="West Bengal", min_length=1, max_length=60)
    seo_title: str = Field(default="", max_length=160)
    seo_description: str = Field(default="", max_length=320)

    @field_validator("owner_email", mode="before")
    @classmethod
    def empty_email(cls, value):
        return value.strip() or None if isinstance(value, str) else value

class SettingsOutput(SettingsInput):
    key: str = "store"

class OrderOutput(BaseModel):
    order_id: str
    order_number: str
    customer_name: str
    customer_email: str
    customer_phone: str
    address: str
    city: str
    pincode: str
    items: list[dict]
    total: int
    status: str
    created_at: str
    notifications: dict = Field(default_factory=dict)

class EmailResult(BaseModel):
    status: str
    recipient: Optional[str] = None
    email_id: Optional[str] = None
    error: Optional[str] = None
    updated_at: Optional[str] = None

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

@app.get("/api/products", response_model=list[ProductOutput])
async def products(search: str = "", brand: str = "", category: str = ""):
    query={"status":"active","stock_quantity":{"$gt":0}}
    if search: query["$or"]=[{field:{"$regex":re.escape(search),"$options":"i"}} for field in ("title", "brand", "sku")]
    if brand: query["brand"]=brand
    if category: query["category"]=category
    return await db.products.find(query,{"_id":0}).sort("created_at",-1).to_list(100)

@app.get("/api/products/{product_id}", response_model=ProductOutput)
async def product(product_id: str):
    item=await db.products.find_one({"product_id":product_id,"status":"active"},{"_id":0})
    if not item: raise HTTPException(404,"Laptop not found")
    return item

@app.post("/api/orders", response_model=OrderOutput, response_model_exclude={"notifications"})
async def create_order(data: OrderInput, background: BackgroundTasks):
    if not data.items: raise HTTPException(400,"Cart is empty")
    snapshots=[]; total=0
    for line in data.items:
        item=await db.products.find_one({"product_id":line.product_id,"status":"active","stock_quantity":{"$gte":line.quantity}},{"_id":0})
        if not item: raise HTTPException(409,"One of these laptops is no longer available")
        snapshots.append({"product_id":item["product_id"],"title":item["title"],"sku":item["sku"],"price":item["price"],"quantity":line.quantity})
        total += item["price"] * line.quantity
    order={"order_id":str(uuid.uuid4()),"order_number":f"LL-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:5].upper()}","customer_name":data.customer_name,"customer_email":str(data.customer_email).lower(),"customer_phone":data.customer_phone,"address":data.address,"city":data.city,"pincode":data.pincode,"items":snapshots,"total":total,"status":"PLACED","created_at":now()}
    order["notifications"]={target:{"status":"pending","updated_at":now()} for target in ("owner","customer")}
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
    background.add_task(notify_order, db, order["order_id"])
    return {k:v for k,v in order.items() if k != "_id"}

@app.get("/api/admin/products", response_model=list[ProductOutput])
async def admin_products(user=Depends(admin_required)):
    return await db.products.find({"deleted_at":{"$exists":False}}, {"_id":0}).sort("created_at",-1).to_list(None)

@app.post("/api/admin/products", response_model=ProductOutput)
async def add_product(data: ProductInput, user=Depends(admin_required)):
    doc=data.model_dump(); doc.update({"product_id":str(uuid.uuid4()),"sku":f"{data.brand[:4].upper()}-{uuid.uuid4().hex[:6].upper()}","created_at":now(),"updated_at":now()})
    await db.products.insert_one(doc); return await db.products.find_one({"product_id":doc["product_id"]},{"_id":0})

@app.put("/api/admin/products/{product_id}", response_model=ProductOutput)
async def edit_product(product_id: str, data: ProductUpdate, user=Depends(admin_required)):
    if not await db.products.find_one({"product_id":product_id,"deleted_at":{"$exists":False}}, {"_id":0,"product_id":1}):
        raise HTTPException(404,"Product not found")
    result=await db.products.update_one({"product_id":product_id,"deleted_at":{"$exists":False},"stock_quantity":data.expected_stock},{"$set":{**data.model_dump(exclude={"expected_stock"}),"updated_at":now()}})
    if not result.matched_count: raise HTTPException(409,"Stock changed after you opened this product. Reopen the editor to use the latest stock.")
    return await db.products.find_one({"product_id":product_id},{"_id":0})

@app.patch("/api/admin/products/{product_id}/stock", response_model=ProductOutput)
async def update_stock(product_id: str, data: StockInput, user=Depends(admin_required)):
    if not await db.products.find_one({"product_id":product_id,"deleted_at":{"$exists":False}}, {"_id":0,"product_id":1}):
        raise HTTPException(404,"Product not found")
    result=await db.products.update_one({"product_id":product_id,"deleted_at":{"$exists":False},"stock_quantity":data.expected_stock}, {"$set":{"stock_quantity":data.stock_quantity,"updated_at":now()}})
    if not result.matched_count: raise HTTPException(409,"Stock changed while editing. Inventory has been refreshed; enter the new count again.")
    return await db.products.find_one({"product_id":product_id},{"_id":0})

@app.delete("/api/admin/products/{product_id}")
async def delete_product(product_id: str, user=Depends(admin_required)):
    result=await db.products.update_one({"product_id":product_id,"deleted_at":{"$exists":False}},{"$set":{"status":"inactive","deleted_at":now(),"updated_at":now()}})
    if not result.matched_count: raise HTTPException(404,"Product not found")
    return {"status":"deleted"}

@app.get("/api/admin/orders", response_model=list[OrderOutput])
async def admin_orders(date: Optional[date] = None, user=Depends(admin_required)):
    query={}
    if date:
        start,end=day_bounds(date)
        query={"created_at":{"$gte":start,"$lt":end}}
    return await db.orders.find(query, {"_id":0}).sort("created_at",-1).to_list(None)

@app.get("/api/admin/orders/export")
async def export_orders(format: Literal["xlsx", "pdf"], date: Optional[date] = None, user=Depends(admin_required)):
    day=date or datetime.now(STORE_TZ).date()
    start,end=day_bounds(day)
    orders=await db.orders.find({"created_at":{"$gte":start,"$lt":end}}, {"_id":0}).sort("created_at",1).to_list(None)
    settings=await db.settings.find_one({"key":"store"}, {"_id":0}) or {}
    content=await run_in_threadpool(workbook_bytes if format == "xlsx" else pdf_bytes, orders, settings.get("store_name", EMAIL_FROM_NAME), day)
    media="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "application/pdf"
    return Response(content=content, media_type=media, headers={"Content-Disposition":f'attachment; filename="orders-{day.isoformat()}.{format}"',"Cache-Control":"no-store"})

@app.post("/api/admin/orders/{order_id}/retry-email", response_model=OrderOutput)
async def retry_email(order_id: str, recipient: Literal["owner","customer"], user=Depends(admin_required)):
    order=await db.orders.find_one({"order_id":order_id}, {"_id":0})
    if not order: raise HTTPException(404,"Order not found")
    last=order.get("notifications",{}).get(recipient,{})
    if last.get("status") == "accepted": return order
    if last.get("status") == "sending" and last.get("updated_at", "") > (datetime.now(timezone.utc)-timedelta(seconds=90)).isoformat():
        raise HTTPException(409,"This notification is still sending. Refresh shortly.")
    if last.get("updated_at", "") > (datetime.now(timezone.utc)-timedelta(seconds=60)).isoformat() and last.get("status") in {"failed","unknown"}:
        raise HTTPException(429,"Please wait a minute before retrying this email.")
    await notify_order(db, order_id, recipient)
    return await db.orders.find_one({"order_id":order_id}, {"_id":0})

@app.post("/api/admin/email/test", response_model=EmailResult)
async def send_test_email(user=Depends(admin_required)):
    return await test_owner_email(db)

@app.get("/api/admin/documentation")
async def documentation(user=Depends(admin_required)):
    return FileResponse(os.path.join(ROOT_DIR,"docs","TECH_STACK.md"), media_type="text/markdown", filename="Website-Tech-Stack.md")

@app.patch("/api/admin/orders/{order_id}")
async def update_order(order_id: str, status: str, user=Depends(admin_required)):
    if status not in {"PLACED","PROCESSING","PACKED","SHIPPED","DELIVERED","CANCELLED"}: raise HTTPException(400,"Invalid status")
    result=await db.orders.update_one({"order_id":order_id},{"$set":{"status":status}})
    if not result.matched_count: raise HTTPException(404,"Order not found")
    return {"status":status}

@app.get("/api/settings", response_model=SettingsOutput)
async def get_settings():
    item=await db.settings.find_one({"key":"store"},{"_id":0})
    return item or {"key":"store","store_name":"Laptop Lab","hero_title":"Good tech. Better value.","hero_subtitle":"Professionally checked laptops, honestly described, ready for their next chapter.","shipping_policy":"Free delivery across India. Orders are dispatched in 2–4 working days.","return_policy":"7-day return support for verified manufacturing issues.","warranty_default":"3 months store warranty"}

@app.put("/api/admin/settings", response_model=SettingsOutput)
async def save_settings(data: SettingsInput, user=Depends(admin_required)):
    await db.settings.update_one({"key":"store"},{"$set":data.model_dump()},upsert=True)
    return await db.settings.find_one({"key":"store"},{"_id":0})

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