# backend/feature2.py

import os
import uuid
import threading
import requests
from fastapi import APIRouter, UploadFile, Form, File, HTTPException

from config.tts_config import get_voice
from services.tts_client import generate_audio

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



def enqueue_feature1_job(user_id, video_path, audio_path):
    try:
        with open(video_path, "rb") as v, open(audio_path, "rb") as a:
            requests.post(
                FEATURE1_ENDPOINT,
                params={"user_id": user_id},
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
    user_id: str = Form(...),
    text: str = Form(...),
    gender: str = Form(...),
    video: UploadFile = File(...)
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

    # 🔥 FIRE & FORGET
    threading.Thread(
        target=enqueue_feature1_job,
        args=(user_id, video_path, audio_path),
        daemon=True
    ).start()

    # ✅ Immediate success response
    return {
        "status": "QUEUED",
        "job_id": job_id,
        "message": "Job queued successfully"
    }
