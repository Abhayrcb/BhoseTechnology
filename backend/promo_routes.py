import uuid
from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator


def now():
    return datetime.now(timezone.utc).isoformat()


class PromoVideoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    platform: Literal["YouTube", "Instagram", "Facebook", "WhatsApp", "Other"] = "YouTube"
    video_url: str = Field(min_length=1, max_length=2000)
    description: str = Field(default="", max_length=1000)
    status: Literal["active", "inactive"] = "active"

    @field_validator("video_url")
    @classmethod
    def valid_url(cls, value):
        if not value.startswith(("http://", "https://")):
            raise ValueError("Video link must start with http:// or https://")
        return value


class PromoVideoOutput(PromoVideoInput):
    video_id: str
    created_at: str
    updated_at: Optional[str] = None


def create_promo_router(db, admin_required):
    """Public + admin CRUD routes for social media promotional video links.
    Mirrors the product CRUD pattern already used in server.py."""
    router = APIRouter(prefix="/api", tags=["Promo Videos"])

    @router.get("/promo-videos", response_model=list[PromoVideoOutput])
    async def public_promo_videos():
        return await db.promo_videos.find({"status": "active"}, {"_id": 0}).sort("created_at", -1).to_list(100)

    @router.get("/admin/promo-videos", response_model=list[PromoVideoOutput])
    async def admin_promo_videos(user=Depends(admin_required)):
        return await db.promo_videos.find({}, {"_id": 0}).sort("created_at", -1).to_list(None)

    @router.post("/admin/promo-videos", response_model=PromoVideoOutput)
    async def add_promo_video(data: PromoVideoInput, user=Depends(admin_required)):
        doc = data.model_dump()
        doc.update({"video_id": str(uuid.uuid4()), "created_at": now(), "updated_at": now()})
        await db.promo_videos.insert_one(doc)
        return await db.promo_videos.find_one({"video_id": doc["video_id"]}, {"_id": 0})

    @router.put("/admin/promo-videos/{video_id}", response_model=PromoVideoOutput)
    async def edit_promo_video(video_id: str, data: PromoVideoInput, user=Depends(admin_required)):
        result = await db.promo_videos.update_one({"video_id": video_id}, {"$set": {**data.model_dump(), "updated_at": now()}})
        if not result.matched_count:
            raise HTTPException(404, "Video not found")
        return await db.promo_videos.find_one({"video_id": video_id}, {"_id": 0})

    @router.delete("/admin/promo-videos/{video_id}")
    async def delete_promo_video(video_id: str, user=Depends(admin_required)):
        result = await db.promo_videos.delete_one({"video_id": video_id})
        if not result.deleted_count:
            raise HTTPException(404, "Video not found")
        return {"status": "deleted"}

    return router
