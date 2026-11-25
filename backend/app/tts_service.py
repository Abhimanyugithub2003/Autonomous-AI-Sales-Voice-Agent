import re
import io
import asyncio
import logging
import edge_tts
from typing import Optional
from app.config import DEFAULT_VOICE, VOICE_RATE, VOICE_PITCH

logger = logging.getLogger("tts_service")

class TTSService:
    """
    High-fidelity Neural Text-to-Speech service using Edge-TTS.
    Converts sales agent responses to natural, expressive voice audio.
    """
    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice

    def clean_text_for_speech(self, text: str) -> str:
        """
        Removes markdown, code tags, URLs, and excessive symbols for smooth vocalization.
        """
        # Remove markdown bold/italics
        cleaned = re.sub(r"[*_#`~]", "", text)
        # Remove markdown links [title](url) -> title
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        # Remove URLs
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        # Remove bullet symbols
        cleaned = re.sub(r"^[\s•\-\*]+\s*", "", cleaned, flags=re.MULTILINE)
        # Replace multiple spaces / newlines with single space
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    async def generate_speech_audio(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        Synthesizes speech and returns MP3 audio bytes.
        """
        target_voice = voice or self.voice
        spoken_text = self.clean_text_for_speech(text)
        
        if not spoken_text:
            spoken_text = "I am listening. How can I help you today?"

        communicate = edge_tts.Communicate(
            text=spoken_text,
            voice=target_voice,
            rate=VOICE_RATE,
            pitch=VOICE_PITCH
        )
        
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        return audio_buffer.getvalue()

tts_service = TTSService()
