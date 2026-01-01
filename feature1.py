# backend/feature1.py

from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from datetime import datetime
import uuid
import os
from db import get_db_connection
from fastapi.responses import FileResponse
from services.job_repository import get_job_by_id
from services.feature1_executor import download_mp4
import os

router = APIRouter(prefix="/feature1", tags=["Feature1"])

UPLOAD_DIR = "storage/uploads"
OUTPUT_DIR = "storage/outputs"

# import os
# import requests

# GPU_VM_URL = "http://154.201.127.0:7000"
# DOWNLOAD_ENDPOINT = f"{GPU_VM_URL}/get_file"

# def download_mp4(filename: str) -> str:
#     """
#     Downloads the generated video from GPU VM
#     and stores it in storage/outputs/
#     """

#     params = {"filename": filename}

#     response = requests.get(
#         DOWNLOAD_ENDPOINT,
#         params=params,
#         stream=True,
#         timeout=300
#     )

#     print("📥 Requesting file:", filename)
#     print("📡 Status Code:", response.status_code)

#     if response.status_code != 200:
#         raise Exception(f"Download failed: {response.text}")

#     # ✅ Ensure outputs directory exists
#     output_dir = "storage/outputs"
#     os.makedirs(output_dir, exist_ok=True)

#     # ✅ Save EXACT filename (no prefix)
#     local_path = os.path.join(output_dir, filename)

#     with open(local_path, "wb") as f:
#         for chunk in response.iter_content(chunk_size=8192):
#             if chunk:
#                 f.write(chunk)

#     print(f"✅ Saved to {local_path}")
#     return local_path



@router.post("/create-job")
async def create_job(
    user_id: str = Query(...),
    video: UploadFile = File(...),
    audio: UploadFile = File(...)
):
    job_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    video_path = os.path.join(job_dir, f"{job_id}.mp4")
    audio_path = os.path.join(job_dir, f"{job_id}.wav")
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    with open(video_path, "wb") as v:
        v.write(await video.read())

    with open(audio_path, "wb") as a:
        a.write(await audio.read())

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs (
            job_id,
            user_id,
            input_video,
            input_audio,
            output_video,
            status,
            created_at,
            started_at,
            completed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        user_id,
        video_path,
        audio_path,
        output_path,
        "QUEUED",
        created_at,
        None,
        None
    ))

    conn.commit()
    conn.close()

    return {
        "job_id": job_id,
        "status": "QUEUED"
    }

@router.get("/jobs")
def list_jobs():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs ORDER BY created_at")
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]


# from fastapi.responses import FileResponse
# from services.feature1_executor import download_mp4
# from services.job_repository import get_job_by_id

# @router.get("/download/{job_id}")
# def download_job_output(job_id: str):
#     job = get_job_by_id(job_id)

#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")

#     if job["status"] != "COMPLETED":
#         raise HTTPException(status_code=400, detail="Job not completed")

#     # ✅ THIS IS CRITICAL
#     filename = job["output_video"]

#     if not filename:
#         raise HTTPException(status_code=500, detail="Output file missing")

#     local_path = download_mp4(
#     job_id=job_id,
#     model_filename=job["output_video"]
# )

# feature1.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

# router = APIRouter(prefix="/feature1")

OUTPUT_DIR = "storage/outputs"


@router.get("/download/{job_id}")
def download_job_output(job_id: str):
    file_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=f"{job_id}.mp4"
    )
