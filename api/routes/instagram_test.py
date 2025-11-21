from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from api.services.content_distributor.connectors.instagram import upload_instagram_photo

router = APIRouter()


class InstagramPost(BaseModel):
    image_url: HttpUrl
    caption: str = ""


@router.post("/test", response_model=dict)
async def test_instagram_post(data: InstagramPost):
    try:
        response = await upload_instagram_photo(
            image_url=data.image_url,
            caption=data.caption
        )
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
