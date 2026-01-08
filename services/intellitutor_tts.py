# Text-to-speech helpers for IntelliTutor (Feature 4)
# Uses the same TTS implementation as feature2 (SarvamAI)
from config.tts_config import get_voice
from services.tts_client import generate_audio


def generate_slide_audio(text: str, output_wav: str, language: str = "en", gender: str = "male") -> str:
    """
    Generate narration for a single slide as a WAV file.
    Uses SarvamAI TTS (same as feature2).
    """
    voice = get_voice(gender)  # Maps gender to voice: male -> "hitesh", female -> "manisha"
    generate_audio(text=text, voice=voice, output_path=output_wav)
    return output_wav

