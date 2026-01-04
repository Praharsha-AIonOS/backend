# backend/feature2.py

import os
import uuid
import threading
import requests
from fastapi import APIRouter, UploadFile, Form, File, HTTPException, Depends, Query

from config.tts_config import get_voice
from services.tts_client import generate_audio
from auth_router import get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# Optional dependency for authentication
security = HTTPBearer(auto_error=False)

async def get_user_or_none(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current user if token is provided, otherwise return None"""
    if credentials:
        try:
            return await get_current_user(credentials)
        except:
            return None
    return None

router = APIRouter(prefix="/feature2", tags=["Feature2"])

FEATURE1_ENDPOINT = "http://127.0.0.1:8000/feature1/create-job"


import subprocess

def normalize_audio(input_wav: str) -> str:
    normalized_wav = input_wav.replace(".wav", "_norm.wav")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", input_wav,
            "-ar", "16000",
            "-ac", "1",
            normalized_wav
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return normalized_wav
# After Sarvam TTS



def enqueue_feature1_job(user_id_int, video_path, audio_path):
    """Enqueue feature1 job - user_id_int is integer from database"""
    try:
        with open(video_path, "rb") as v, open(audio_path, "rb") as a:
            # Pass user_id as query param for internal service call
            requests.post(
                FEATURE1_ENDPOINT,
                params={"user_id": str(user_id_int)},
                files={
                    "video": (os.path.basename(video_path), v, "video/mp4"),
                    "audio": (os.path.basename(audio_path), a, "audio/wav"),
                },
                timeout=5
            )
    except Exception as e:
        # Log only — never crash Feature-2
        print(f"[Feature2] Failed to enqueue Feature-1 job: {e}")


@router.post("/text-to-avatar")
async def text_to_avatar(
    text: str = Form(...),
    gender: str = Form(...),
    video: UploadFile = File(...),
    user_id: str = Query(None),  # Optional for internal service calls
    current_user: Optional[dict] = Depends(get_user_or_none)
):
    job_id = str(uuid.uuid4())
    upload_dir = f"storage/uploads/{job_id}"
    os.makedirs(upload_dir, exist_ok=True)

    video_path = os.path.join(upload_dir, f"{job_id}.mp4")
    with open(video_path, "wb") as f:
        f.write(await video.read())

    try:
        voice = get_voice(gender)
        audio_path = os.path.join(upload_dir, f"{job_id}.wav")
        # audio_path = normalize_audio(audio_path)
        generate_audio(text=text, voice=voice, output_path=audio_path)
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {e}")

    # Get user_id from authenticated user or from query param (for internal calls)
    if user_id:
        # Internal service call - resolve user_id from username/email or use as-is if integer
        try:
            user_id_int = int(user_id)
        except ValueError:
            # If not an int, treat as username and look up user_id
            from db import get_db_connection, return_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", (user_id, user_id))
            user_row = cursor.fetchone()
            return_db_connection(conn)
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
            user_id_int = user_row[0]
    elif current_user:
        # External authenticated call
        user_id_int = current_user["user_id"]
    else:
        # No authentication and no user_id provided
        raise HTTPException(status_code=401, detail="Authentication required or user_id must be provided")
    
    # 🔥 FIRE & FORGET - Pass user_id_int for internal service call
    threading.Thread(
        target=enqueue_feature1_job,
        args=(user_id_int, video_path, audio_path),
        daemon=True
    ).start()

    # ✅ Immediate success response
    return {
        "status": "QUEUED",
        "job_id": job_id,
        "message": "Job queued successfully"
    }
