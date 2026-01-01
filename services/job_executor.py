# services/job_executor.py

from services.feature1_executor import run_feature1_job
from services.job_repository import update_job_status
from datetime import datetime


def execute_job(job):
    job_id = job["job_id"]

    # Mark job started
    started_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    update_job_status(
        job_id=job_id,
        status="IN_PROGRESS",
        started_at=started_at
    )

    # try:
        # 🚀 Run Feature-1 (this already:
        # - hits model
        # - downloads output
        # - renames to <uuid>.mp4
        # - saves to storage/outputs
        # - updates job["output_video"])
    run_feature1_job(job)
    completed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        # ✅ Mark completed (NO video parsing here)
    update_job_status(
        job_id=job_id,
        status="COMPLETED",
        completed_at=completed_at
    )

    print(f"🟢 Job {job_id} COMPLETED")

    # except Exception as e:
        # update_job_status(job_id, "FAILED")
        # print(f"🔴 Job {job_id} FAILED → {e}")
