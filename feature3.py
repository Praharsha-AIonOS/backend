# backend/feature3.py

import threading
import requests
from typing import List
from fastapi import APIRouter, UploadFile, Form, File, HTTPException, Depends

from services.template_renderer import render_template
from auth_router import get_current_user
from quota_utils import validate_and_increment_quota

router = APIRouter(prefix="/feature3", tags=["Feature3"])

FEATURE2_ENDPOINT = "http://127.0.0.1:8000/feature2/text-to-avatar"


def fire_feature2(video_bytes: bytes, video_name: str, payload: dict, user_id_int: int, feature_name: str):
    """
    Fire-and-forget call to Feature-2
    Note: Feature-2 now requires auth, but for internal calls we pass user_id
    """
    try:
        print("\n[Feature3] → Calling Feature-2")
        print("[Feature3] Payload:", payload)
        print("[Feature3] Video:", video_name)
        print("[Feature3] User ID:", user_id_int)
        print("[Feature3] Feature Name:", feature_name)

        files = {
            "video": (video_name, video_bytes, "video/mp4")
        }

        # Pass user_id and feature_name for internal call
        response = requests.post(
            FEATURE2_ENDPOINT,
            params={
                "user_id": str(user_id_int),
                "feature_name": feature_name  # Pass feature name to feature2
            },
            data=payload,
            files=files,
            timeout=5  # short timeout, async fire
        )

        print("[Feature3] Feature-2 status:", response.status_code)
        print("[Feature3] Feature-2 response:", response.text)

    except Exception as e:
        # Never crash Feature-3
        print("[Feature3] Feature-2 async error:", e)


@router.post("/personalized-wishes")
async def personalized_wishes(
    script: str = Form(...),
    names: List[str] = Form(...),
    video: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    # 🔒 Validate script
    if "{name}" not in script:
        raise HTTPException(status_code=400, detail="Script must contain {name}")

    # Get user_id from authenticated user
    user_id_int = current_user["user_id"]
    
    # Check quota (each submission counts as 1 attempt, regardless of number of names)
    feature_name = "Personalized Wishes Generator"
    validate_and_increment_quota(user_id_int, feature_name)

    # 1️⃣ Render personalized texts
    texts = render_template(script, names)
    print(f"[Feature3] Total jobs to queue: {len(texts)}")

    # 2️⃣ Read video ONCE
    video_bytes = await video.read()

    # 3️⃣ FORCE gender = female (IMPORTANT FIX)
    gender = "female"
    
    # 4️⃣ Fire Feature-2 asynchronously for each text
    # Pass user_id and feature name for internal service call
    for text in texts:
        payload = {
            "gender": gender,   # ✅ FIXED HERE
            "text": text
        }

        threading.Thread(
            target=fire_feature2,
            args=(video_bytes, video.filename, payload, user_id_int, feature_name),
            daemon=True
        ).start()

    # 5️⃣ Immediate response
    return {
        "status": "QUEUED",
        "jobs_created": len(texts),
        "message": "All personalized jobs queued successfully"
    }
