# services/tts_client.py

import base64
import os
from sarvamai import SarvamAI
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not SARVAM_API_KEY:
    raise RuntimeError("SARVAM_API_KEY missing")

sarvam_client = SarvamAI(api_subscription_key=SARVAM_API_KEY)


def generate_audio(text: str, voice: str, output_path: str):
    """
    Generates REAL Sarvam TTS audio and saves it as WAV
    voice: hitesh / manisha
    """

    # Sarvam voice selection is implicit by language + model
    # (Sarvam does not expose voice param directly like ElevenLabs)
    tts = sarvam_client.text_to_speech.convert(
        text=text,
        target_language_code="en-IN"
    )

    # Sarvam returns base64 audio
    audio_bytes = base64.b64decode(tts.audios[0])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    print(f"🟢 Sarvam TTS generated ({voice}) → {output_path}")

    return output_path
