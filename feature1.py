# backend/feature1.py

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends
from datetime import datetime
import uuid
import os
import psycopg2.extras
from db import get_db_connection, return_db_connection
from fastapi.responses import FileResponse
from services.job_repository import get_job_by_id
from services.feature1_executor import download_mp4
from auth_router import get_current_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

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

@router.post("/create-job")
async def create_job(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    user_id: str = Query(None),  # Optional for internal service calls
    current_user: Optional[dict] = Depends(get_user_or_none)
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
    
    # Get user_id from authenticated user (from JWT token) or from query param (for internal calls)
    if user_id:
        # Internal service call - resolve user_id from username/email or use as-is if integer
        try:
            user_id_int = int(user_id)
        except ValueError:
            # If not an int, treat as username and look up user_id
            cursor.execute("SELECT user_id FROM users WHERE username = %s OR email = %s", (user_id, user_id))
            user_row = cursor.fetchone()
            if not user_row:
                return_db_connection(conn)
                raise HTTPException(status_code=404, detail="User not found")
            user_id_int = user_row[0]
    elif current_user:
        # External authenticated call - use user_id from JWT token
        user_id_int = current_user["user_id"]
    else:
        # No authentication and no user_id provided
        return_db_connection(conn)
        raise HTTPException(status_code=401, detail="Authentication required or user_id must be provided")

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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        job_id,
        user_id_int,
        video_path,
        audio_path,
        output_path,
        "QUEUED",
        created_at,
        None,
        None
    ))

    conn.commit()
    return_db_connection(conn)

    return {
        "job_id": job_id,
        "status": "QUEUED"
    }

@router.get("/jobs")
def list_jobs(current_user: dict = Depends(get_current_user)):
    """Get jobs for the authenticated user only"""
    conn = get_db_connection()
    # Use RealDictCursor to get dictionary-like rows
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Filter jobs by user_id - only return jobs for the authenticated user
    cursor.execute(
        "SELECT * FROM jobs WHERE user_id = %s ORDER BY created_at DESC",
        (current_user["user_id"],)
    )
    rows = cursor.fetchall()

    # Convert RealDictRow to regular dict
    result = [{k: v for k, v in row.items()} for row in rows]
    return_db_connection(conn)
    return result


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
def download_job_output(job_id: str, current_user: dict = Depends(get_current_user)):
    """Download job output - only if job belongs to authenticated user"""
    # Verify job belongs to the user
    job = get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if job belongs to the authenticated user
    if job.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied: This job does not belong to you")
    
    file_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=f"{job_id}.mp4"
    )
