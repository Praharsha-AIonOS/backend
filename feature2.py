# api/feature2.py

import os
import uuid
import requests
from fastapi import APIRouter, UploadFile, Form, File, HTTPException

from config.tts_config import get_voice
from services.tts_client import generate_audio

router = APIRouter(prefix="/feature2", tags=["Feature2"])

FEATURE1_ENDPOINT = "http://127.0.0.1:8000/feature1/create-job"


@router.post("/text-to-avatar")
async def text_to_audio(
    user_id: str = Form(...),
    text: str = Form(...),
    gender: str = Form(...),
    video: UploadFile = File(...)
):
    # 1️⃣ Create single UUID for this job
    job_id = str(uuid.uuid4())

    upload_dir = f"storage/uploads/{job_id}"
    os.makedirs(upload_dir, exist_ok=True)

    # 2️⃣ Save uploaded video
    video_path = os.path.join(upload_dir, f"{job_id}.mp4")
    with open(video_path, "wb") as f:
        f.write(await video.read())

    # 3️⃣ Generate REAL Sarvam TTS audio
    try:
        voice = get_voice(gender)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    audio_path = os.path.join(upload_dir, f"{job_id}.wav")

    try:
        generate_audio(
            text=text,
            voice=voice,
            output_path=audio_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    # 4️⃣ Forward audio + video to Feature-1
    try:
        with open(video_path, "rb") as v, open(audio_path, "rb") as a:
            response = requests.post(
                FEATURE1_ENDPOINT,
                params={"user_id": user_id},
                files={
                    "video": (f"{job_id}.mp4", v, "video/mp4"),
                    "audio": (f"{job_id}.wav", a, "audio/wav"),
                },
                timeout=60
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to call Feature1: {e}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Feature1 error: {response.text}"
        )

    return {
        "message": "Feature2 job created successfully",
        "job_id": job_id,
        "feature1_response": response.json()
    }
