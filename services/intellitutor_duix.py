# Client for Duix avatar generation used in IntelliTutor (Feature 4)
import os
import time
import subprocess
import requests

# ---------------- CONFIG ----------------
GENERATE_ENDPOINT = "http://154.201.127.0:7001/generate"
DOWNLOAD_ENDPOINT = "http://154.201.127.0:7000/get_file"

POLL_INTERVAL = 5
MAX_WAIT_TIME = 600


def _validate_mp4(path: str):
    """
    Validate MP4 using ffprobe.
    """
    proc = subprocess.run(
        ["ffprobe", "-v", "error", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError("Downloaded avatar.mp4 is INVALID")


def _download_video(url: str, output_path: str):
    """
    Download video from Duix.
    Supports JSON indirection + final MP4 download.
    """
    r = requests.get(url, timeout=300)
    ct = r.headers.get("content-type", "").lower()

    # Case 1: Direct MP4
    if "video" in ct:
        with open(output_path, "wb") as f:
            f.write(r.content)
        _validate_mp4(output_path)
        return

    # Case 2: JSON indirection
    if "application/json" in ct:
        data = r.json()
        filename = data.get("file") or data.get("filename")
        if not filename:
            raise RuntimeError(f"Download JSON missing filename: {data}")

        final_url = f"{DOWNLOAD_ENDPOINT}?filename={filename}"
        r2 = requests.get(final_url, stream=True, timeout=300)
        ct2 = r2.headers.get("content-type", "").lower()

        if "video" not in ct2:
            raise RuntimeError(f"Final download not video, content-type={ct2}")

        with open(output_path, "wb") as f:
            for chunk in r2.iter_content(8192):
                if chunk:
                    f.write(chunk)

        _validate_mp4(output_path)
        return

    raise RuntimeError(f"Unsupported download response: content-type={ct}")


def submit_intellitutor(face_path: str, audio_path: str, output_video: str) -> str:
    """
    Submit a job to Duix and download the resulting avatar video.
    """
    # 1. Call generate endpoint
    with open(face_path, "rb") as fv, open(audio_path, "rb") as fa:
        r = requests.post(
            GENERATE_ENDPOINT,
            headers={"accept": "application/json"},
            files={
                "media": ("face.mp4", fv, "video/mp4"),
                "audio": ("audio.wav", fa, "audio/wav"),
            },
            timeout=300,
        )

    if r.status_code != 200:
        raise RuntimeError(f"Generate failed: {r.text}")

    data = r.json()

    if "video" not in data:
        raise RuntimeError(f"Unexpected generate response: {data}")

    filename = os.path.basename(data["video"])

    # 3. Download using download endpoint
    resp = requests.get(
        DOWNLOAD_ENDPOINT,
        params={"filename": filename},
        stream=True,
        timeout=300,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Download failed: {resp.text}")

    with open(output_video, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)

    _validate_mp4(output_video)
    return output_video

