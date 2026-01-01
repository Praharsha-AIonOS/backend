# scheduler.py

import time
from services.job_repository import (
    fetch_oldest_pending_job,
    has_in_progress_job
)
from services.job_executor import execute_job

CHECK_INTERVAL = 5  # seconds


def run_scheduler():
    print("🟢 Scheduler started (STRICT SINGLE-JOB MODE)")

    in_progress_logged = False

    while True:
        # If a job is already running, wait silently
        if has_in_progress_job():
            if not in_progress_logged:
                print("⏳ Job execution in progress. Waiting for completion...")
                in_progress_logged = True

            time.sleep(CHECK_INTERVAL)
            continue

        # If we reach here, no job is IN_PROGRESS anymore
        if in_progress_logged:
            print("✅ Job execution completed.")
            print("🔁 Checking for next job...\n")
            in_progress_logged = False

        # Fetch next QUEUED job
        job = fetch_oldest_pending_job()

        if not job:
            time.sleep(CHECK_INTERVAL)
            continue

        job_id = job["job_id"]
        print(f"🚀 Starting job {job_id}")

        execute_job(job)
        # After this, job will be IN_PROGRESS and loop will wait silently


if __name__ == "__main__":
    run_scheduler()
