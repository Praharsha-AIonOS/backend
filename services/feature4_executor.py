# Executor for IntelliTutor (Feature 4) jobs
import os
import tempfile
from datetime import datetime

from services.intellitutor_ppt import parse_ppt
from services.intellitutor_tts import generate_slide_audio
from services.intellitutor_video import compose_video
from services.intellitutor_duix import submit_intellitutor
from services.job_repository import update_job_status, update_job_output


def run_feature4_job(job: dict):
    """
    Process an IntelliTutor job:
    - Parse PPT to slide images + summarized text
    - Generate TTS per slide and merge
    - Generate avatar video via Duix
    - Compose slides + avatar into final video
    """
    job_id = job["job_id"]
    ppt_path = job["input_audio"]  # stored ppt path
    face_video = job["input_video"]  # stored face video path
    output_video = job["output_video"]

    print(f"\n=== [IntelliAvatar - IntelliTutor] Starting job {job_id} ===")

    # Working directory
    workdir = tempfile.mkdtemp(prefix=f"intellitutor_{job_id}_")
    print(f"[IntelliTutor] Working directory: {workdir}")

    # 1) Parse PPT and summarize
    print("[IntelliTutor][1] Parsing PPT and generating slide texts...")
    parsed = parse_ppt(ppt_path, workdir)
    slide_images = parsed["slide_images"]
    slide_texts = parsed["slide_texts"]
    print(f"[IntelliTutor] Parsed {len(slide_images)} slides")
    if slide_texts:
        print("[IntelliTutor] Sample summarized text:", slide_texts[0])

    # 2) Generate TTS for each slide
    print("\n[IntelliTutor][2] Generating TTS for each slide...")
    
    # Read gender from metadata file (stored in job directory)
    job_dir = os.path.dirname(ppt_path)
    metadata_path = os.path.join(job_dir, "metadata.txt")
    gender = "male"  # default
    
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            for line in f:
                if line.startswith("gender="):
                    gender = line.split("=", 1)[1].strip()
    
    print(f"[IntelliTutor] Using TTS: gender={gender}")
    
    audio_files = []
    for i, text in enumerate(slide_texts):
        wav = os.path.join(workdir, f"slide_{i}.wav")
        print(f"[IntelliTutor] Generating audio for slide {i+1}/{len(slide_texts)}...")
        generate_slide_audio(text, wav, gender=gender)
        audio_files.append(wav)
    print(f"[IntelliTutor] Generated {len(audio_files)} audio files")

    # 3) Merge narration
    print("\n[IntelliTutor][3] Merging narration audio...")
    from pydub import AudioSegment

    combined = AudioSegment.silent(0)
    for wav in audio_files:
        combined += AudioSegment.from_wav(wav)

    narration_audio = os.path.join(workdir, "narration.wav")
    combined.export(narration_audio, format="wav")

    duration = combined.duration_seconds
    print(f"[IntelliTutor] Narration duration: {duration} seconds")

    # 4) Generate avatar video via Duix
    print("\n[IntelliTutor][4] Calling Duix avatar service...")
    avatar_video = os.path.join(workdir, "avatar.mp4")
    submit_intellitutor(face_path=face_video, audio_path=narration_audio, output_video=avatar_video)
    print(f"[IntelliTutor] Avatar video created: {avatar_video}")

    # 5) Compose final video
    print("\n[IntelliTutor][5] Composing final video...")
    compose_video(slide_images=slide_images, avatar_video=avatar_video, duration=duration, output_video=output_video)
    print(f"[IntelliTutor] Final video created: {output_video}")

    # Update job output path and completion timestamp
    completed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    update_job_output(job_id, output_video, completed_at)

