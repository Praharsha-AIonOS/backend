# Text-to-speech helpers for IntelliTutor (Feature 4)
import asyncio
from gtts import gTTS
from pydub import AudioSegment
import edge_tts


def generate_slide_audio(text: str, output_wav: str, language: str = "en", gender: str = "male") -> str:
    """
    Generate narration for a single slide as a WAV file.
    Tries Edge TTS first, falls back to gTTS.
    """
    try:
        asyncio.run(_edge(text, output_wav, language, gender))
    except Exception:
        _fallback(text, output_wav, language)
    return output_wav


async def _edge(text: str, output_wav: str, language: str, gender: str):
    voice_map = {
        ("en", "male"): "en-IN-PrabhatNeural",
        ("en", "female"): "en-IN-NeerjaNeural",
    }
    voice = voice_map.get((language, gender), "en-US-GuyNeural")
    mp3 = output_wav.replace(".wav", ".mp3")
    await edge_tts.Communicate(text, voice).save(mp3)
    AudioSegment.from_mp3(mp3).export(output_wav, format="wav")


def _fallback(text: str, output_wav: str, language: str):
    mp3 = output_wav.replace(".wav", ".mp3")
    gTTS(text=text, lang=language).save(mp3)
    AudioSegment.from_mp3(mp3).export(output_wav, format="wav")

