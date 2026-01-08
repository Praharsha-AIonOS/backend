# Feature 4: IntelliTutor
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from datetime import datetime
import uuid
import os
import psycopg2.extras
from typing import Optional

from db import get_db_connection, return_db_connection
from auth_router import get_current_user
from quota_utils import validate_and_increment_quota

router = APIRouter(prefix="/feature4", tags=["Feature4"])

UPLOAD_DIR = "storage/uploads"
OUTPUT_DIR = "storage/outputs"


@router.post("/create-job")
async def create_job(
    ppt: UploadFile = File(..., description="PowerPoint file"),
    face_video: UploadFile = File(..., description="Talking-head video"),
    language: str = Form("en"),
    gender: str = Form("male"),
    current_user: dict = Depends(get_current_user),
):
    # Validate file types (basic)
    if not ppt.filename.lower().endswith((".ppt", ".pptx")):
        raise HTTPException(status_code=400, detail="PPT file must be .ppt or .pptx")
    if not face_video.filename.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
        raise HTTPException(status_code=400, detail="Face video must be a video file")

    # Check quota before processing
    user_id_int = current_user["user_id"]
    validate_and_increment_quota(user_id_int, "IntelliTutor")

    job_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    ppt_path = os.path.join(job_dir, f"{job_id}.pptx")
    face_path = os.path.join(job_dir, f"{job_id}_face.mp4")
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    with open(ppt_path, "wb") as f:
        f.write(await ppt.read())

    with open(face_path, "wb") as f:
        f.write(await face_video.read())

    # Store gender in metadata file (same pattern as feature2, no DB changes needed)
    metadata_path = os.path.join(job_dir, "metadata.txt")
    with open(metadata_path, "w") as f:
        f.write(f"gender={gender}\n")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Store ppt path in input_audio, face video in input_video to reuse schema
    cursor.execute(
        """
        INSERT INTO jobs (
            job_id,
            user_id,
            input_video,
            input_audio,
            output_video,
            status,
            feature,
            created_at,
            started_at,
            completed_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            job_id,
            user_id_int,
            face_path,
            ppt_path,
            output_path,
            "QUEUED",
            "IntelliTutor",
            created_at,
            None,
            None,
        ),
    )

    conn.commit()
    return_db_connection(conn)

    return {
        "job_id": job_id,
        "status": "QUEUED",
        "feature": "IntelliTutor",
    }

