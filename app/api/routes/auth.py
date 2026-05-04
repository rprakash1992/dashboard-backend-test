import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


class GoogleCallbackRequest(BaseModel):
    code: str


@router.post("/auth/google/callback")
def google_callback(body: GoogleCallbackRequest):
    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback"

    res = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": body.code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )

    if not res.ok:
        return JSONResponse(status_code=res.status_code, content=res.json())

    data = res.json()
    return {"access_token": data.get("access_token")}
