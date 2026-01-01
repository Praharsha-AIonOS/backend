CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    input_video TEXT NOT NULL,
    input_audio TEXT NOT NULL,
    output_video TEXT NOT NULL,
    status TEXT NOT NULL,

    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);
