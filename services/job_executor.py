import os

from services.feature1_executor import run_feature1_job
from services.feature4_executor import run_feature4_job
from services.job_repository import update_job_status
from datetime import datetime


def _normalize_path(path: str) -> str:
    """
    Normalize paths stored in DB so they work on both Windows and Linux.
    Converts backslashes to the current OS separator and normalizes.
    """
    if not path:
        return path
    # Replace Windows-style separators then normalize
    return os.path.normpath(path.replace("\\", os.sep))


def execute_job(job):
    # Make a shallow copy so we can safely modify paths
    job = dict(job)

    # Normalize file paths for cross‑platform execution (Windows backend, WSL scheduler)
    for key in ("input_video", "input_audio", "output_video"):
        if key in job and job[key]:
            job[key] = _normalize_path(job[key])

    job_id = job["job_id"]

    # Mark job started
    started_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    update_job_status(
        job_id=job_id,
        status="IN_PROGRESS",
        started_at=started_at,
    )

    try:
        # Dispatch based on feature
        feature = job.get("feature") or "Avatar Sync Studio"
        if feature == "IntelliTutor":
            run_feature4_job(job)
        else:
            run_feature1_job(job)

        # Mark completed
        completed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        update_job_status(
            job_id=job_id,
            status="COMPLETED",
            completed_at=completed_at,
        )
        print(f"🟢 Job {job_id} COMPLETED")

    except Exception as exc:
        # On any failure, mark job as FAILED so the scheduler can move on
        failed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        try:
            update_job_status(
                job_id=job_id,
                status="FAILED",
                completed_at=failed_at,
            )
        except Exception:
            # Avoid crashing if even the status update fails
            pass

        # Log the error for debugging
        print(f"🔴 Job {job_id} FAILED → {exc}")
        import traceback

        traceback.print_exc()
        # Do NOT re-raise, so the scheduler loop can continue to next job
