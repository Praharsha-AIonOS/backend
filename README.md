# AlonOS – IntelliAvatar Backend

This repository contains the backend services for IntelliAvatar.
The backend manages job creation, scheduling, AI execution, and file storage
for avatar video generation.

------------------------------------------------------------

OVERVIEW

The backend is responsible for:
- Managing video generation jobs
- Executing Feature-1 (Audio + Video → Avatar Video)
- Executing Feature-2 (Text → Speech → Feature-1)
- Running a scheduler for queued jobs
- Downloading and storing generated outputs

------------------------------------------------------------

TECH STACK

- Python 3.9+
- FastAPI
- SQLite
- Requests
- Uvicorn

------------------------------------------------------------

FOLDER STRUCTURE

backend/
│
├── main.py                    → FastAPI entry point
├── scheduler.py               → Job scheduler (single-job execution)
├── db.py                      → Database connection
├── jobs.db                    → Job metadata database
│
├── services/
│   ├── feature1_executor.py   → Feature-1 execution logic
│   ├── job_executor.py        → Job orchestration
│   └── job_repository.py      → Job DB operations
│
├── feature1.py                → Feature-1 API routes
├── feature2.py                → Feature-2 API routes
│
├── storage/
│   ├── uploads/               → Input audio/video files
│   └── outputs/               → Final generated videos
│
└── .env                       → Environment variables

------------------------------------------------------------

PREREQUISITES

- Python 3.9 or higher
- pip
- Internet connection
- GPU model server running separately

------------------------------------------------------------

INSTALLATION

1. Navigate to backend folder

   cd backend

2. Install dependencies

   pip install -r requirements.txt

------------------------------------------------------------

ENVIRONMENT VARIABLES

Create a .env file inside backend directory:

SARVAM_API_KEY=your_api_key_here

------------------------------------------------------------

RUNNING THE BACKEND

1. Start FastAPI server

   uvicorn main:app --reload

   Server runs at:
   http://127.0.0.1:8000

   API Docs:
   http://127.0.0.1:8000/docs

2. Start Scheduler (mandatory)

   Open a new terminal and run:

   python scheduler.py

The scheduler continuously:
- Picks QUEUED jobs
- Executes Feature-1
- Downloads output video
- Saves output
- Updates job status

------------------------------------------------------------

FEATURE-1: AVATAR SYNC STUDIO

Input:
- Video (.mp4)
- Audio (.wav)

Flow:
1. Job is created with status QUEUED
2. Scheduler picks the job
3. Video + Audio sent to GPU model
4. Model returns output filename
5. Backend downloads the video
6. File is renamed to job_id.mp4
7. Saved to storage/outputs
8. Job marked COMPLETED

Endpoints:
POST /feature1/create-job
GET  /feature1/jobs
GET  /feature1/download/{job_id}

------------------------------------------------------------

FEATURE-2: TEXT TO AVATAR

Input:
- Text
- Base video
- Voice selection

Flow:
1. Text converted to audio using Sarvam TTS
2. Audio + video saved in uploads
3. Feature-1 job is automatically created
4. Scheduler processes the job

Endpoint:
POST /feature2/text-to-avatar

------------------------------------------------------------

JOB LIFECYCLE

QUEUED → IN_PROGRESS → COMPLETED / FAILED

Timestamps stored:
- created_at   → Job submitted
- started_at   → Scheduler start
- completed_at → Job finished

------------------------------------------------------------

OUTPUT STORAGE

All completed videos are stored as:

storage/outputs/{job_id}.mp4

------------------------------------------------------------

NOTES

- Model failures (500 errors) originate from GPU server
- Backend safely continues processing next jobs
- Failed jobs remain visible in dashboard

------------------------------------------------------------

STATUS

Backend implementation is stable and production-ready.
