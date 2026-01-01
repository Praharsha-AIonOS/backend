AlonOS – IntelliAvatar Backend

This repository contains the backend services for IntelliAvatar, an AI-powered avatar video generation system.

The backend is responsible for:

Job creation & lifecycle management

Feature-1 (Audio + Video → Lip-synced Video)

Feature-2 (Text → Speech → Feature-1)

Scheduling & execution

Download & storage management

🧠 High-Level Architecture
Frontend
   ↓
FastAPI Backend
   ├── Feature-2 (Text → Speech → Job Creation)
   ├── Feature-1 (Audio + Video → Model)
   ├── Job Repository (SQLite)
   ├── Scheduler (Single-Job Queue)
   └── GPU Model Server (External)

📂 Folder Structure
backend/
├── main.py                    # FastAPI app entry
├── scheduler.py               # Job scheduler (single-job mode)
├── db.py                      # SQLite DB connection
├── jobs.db                    # Job metadata
│
├── services/
│   ├── feature1_executor.py   # Feature-1 execution logic
│   ├── job_executor.py        # Job orchestration
│   ├── job_repository.py      # DB CRUD operations
│
├── feature1.py                # Feature-1 API routes
├── feature2.py                # Feature-2 API routes
│
├── storage/
│   ├── uploads/               # Input files (video/audio)
│   └── outputs/               # Final generated videos
│
└── .env                       # Environment variables

⚙️ Prerequisites

Python 3.9+

pip

Internet access (Sarvam TTS + GPU VM)

GPU model server running separately

📦 Install Dependencies
cd backend
pip install -r requirements.txt

🔐 Environment Variables

Create a .env file:

SARVAM_API_KEY=your_api_key_here

▶️ Running the Backend
1️⃣ Start FastAPI Server
uvicorn main:app --reload


Backend runs at:

http://127.0.0.1:8000


Swagger Docs:

http://127.0.0.1:8000/docs

2️⃣ Start Scheduler (IMPORTANT)

The scheduler must run in a separate terminal.

python scheduler.py


The scheduler:

Picks QUEUED jobs

Executes Feature-1

Downloads model output

Saves to storage/outputs/{job_id}.mp4

Updates job status & timestamps

🎯 Feature Breakdown
🔹 Feature-1: Avatar Sync Studio

Input

Video (.mp4)

Audio (.wav)

Flow

Job created (QUEUED)

Scheduler picks job

Sends video + audio to GPU model

Model returns output filename

Backend downloads video

Renames → {job_id}.mp4

Saves to storage/outputs/

Job marked COMPLETED

Endpoint

POST /feature1/create-job
GET  /feature1/jobs
GET  /feature1/download/{job_id}

🔹 Feature-2: Text to Avatar

Input

Text

Base video

Voice (Sarvam)

Flow

Text → Sarvam TTS → Audio

Audio + Video saved in uploads

Feature-1 job automatically created

Scheduler processes job

Endpoint

POST /feature2/text-to-avatar

🕒 Job Lifecycle
QUEUED → IN_PROGRESS → COMPLETED / FAILED

Timestamps Stored

created_at → Job submission time

started_at → Scheduler pickup

completed_at → Output saved

📥 Output Handling

Outputs are automatically downloaded

Saved as:

storage/outputs/{job_id}.mp4


No manual download needed for execution

❗ Common Notes

Model failures (500) are external GPU issues

Backend correctly retries next jobs

Failed jobs remain visible in dashboard

✅ Backend Status

✔ Job queue working
✔ Feature-1 stable
✔ Feature-2 integrated
✔ Scheduler reliable
✔ Output storage consistent