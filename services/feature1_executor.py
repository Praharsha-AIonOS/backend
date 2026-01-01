import requests
import os
import shutil
import logging

# ---------------- LOGGING SETUP ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)
# ------------------------------------------------


# 🔹 GPU MODEL SERVER (INFERENCE)
MODEL_GPU_URL = "http://154.201.127.0:7001"
INFER_ENDPOINT = f"{MODEL_GPU_URL}/generate"

# 🔹 FILE SERVER (DOWNLOAD)
FILE_SERVER_URL = "http://154.201.127.0:7000"
DOWNLOAD_ENDPOINT = f"{FILE_SERVER_URL}/get_file"

# 🔹 OUTPUT STORAGE
OUTPUT_DIR = "storage/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_feature1_job(job):
    job_id = job["job_id"]

    logger.info(f"[JOB {job_id}] Starting Feature-1 execution")
    logger.info(f"[JOB {job_id}] Sending video & audio to model")

    # 1️⃣ Call model
    response = requests.post(
        INFER_ENDPOINT,
        files={
            "media": open(job["input_video"], "rb"),
            "audio": open(job["input_audio"], "rb")
        },
        timeout=1800
    )

    logger.info(f"[JOB {job_id}] Model HTTP status: {response.status_code}")
    logger.info(f"[JOB {job_id}] Model raw response: {response.text}")

    if response.status_code != 200:
        raise Exception(f"Model failed: {response.text}")

    data = response.json()

    if data.get("status") != "success":
        raise Exception(f"Model returned non-success: {data}")

    # 2️⃣ Extract remote filename (uuid_date-r.mp4)
    remote_filename = data["video"].split("/")[-1]
    logger.info(f"[JOB {job_id}] Model output filename: {remote_filename}")

    # 3️⃣ Download immediately
    logger.info(f"[JOB {job_id}] Downloading output from file server")
    temp_path = download_mp4(remote_filename)

    # 4️⃣ Move + rename to outputs/<uuid>.mp4
    final_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    logger.info(f"[JOB {job_id}] Moving file to: {final_path}")
    shutil.move(temp_path, final_path)

    logger.info(f"[JOB {job_id}] Output saved successfully")
    logger.info(f"[JOB {job_id}] Final file exists: {os.path.exists(final_path)}")

    # 5️⃣ Update job object
    job["output_video"] = final_path

    logger.info(f"[JOB {job_id}] Feature-1 execution COMPLETED")

    return {
        "status": "success",
        "output_video": final_path
    }


def download_mp4(filename):
    logger.info(f"[DOWNLOAD] Requesting file: {filename}")

    response = requests.get(
        DOWNLOAD_ENDPOINT,
        params={"filename": filename},
        stream=True,
        timeout=300
    )

    logger.info(f"[DOWNLOAD] HTTP status: {response.status_code}")

    if response.status_code != 200:
        logger.error(f"[DOWNLOAD] Failed response: {response.text}")
        raise Exception(f"Download failed: {response.text}")

    temp_path = os.path.join(os.getcwd(), f"_tmp_{filename}")
    logger.info(f"[DOWNLOAD] Saving temp file at: {temp_path}")

    with open(temp_path, "wb") as f:
        for chunk in response.iter_content(8192):
            if chunk:
                f.write(chunk)

    logger.info(f"[DOWNLOAD] File written successfully")
    return temp_path
