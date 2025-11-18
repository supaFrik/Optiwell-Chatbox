import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

import speech_recognition as sr
from pydub import AudioSegment
from groq import Groq
from langdetect import detect, LangDetectException

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def record_audio(file_path: str, timeout: int = 20, phrase_time_limit: int | None = None) -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        logging.info("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        logging.info("Start speaking now...")
        audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    wav_data = audio_data.get_wav_data()
    audio_segment = AudioSegment.from_wav(BytesIO(wav_data))
    audio_segment.export(file_path, format="mp3", bitrate="128k")
    logging.info(f"Audio saved to {file_path}")
    return file_path

def transcribe_with_groq(stt_model: str, audio_filepath: str, GROQ_API_KEY: str) -> tuple[str, str]:
    """Backward-compatible simple transcription function.

    Prefer using :func:`groq_transcribe` for richer control.
    """
    return groq_transcribe(
        file_path=audio_filepath,
        model=stt_model,
        api_key=GROQ_API_KEY,
    )


def groq_client(api_key: Optional[str] = None) -> Groq:
    """Create a Groq client using explicit or environment API key."""
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY missing. Set env var or pass api_key.")
    return Groq(api_key=key)


def groq_transcribe(
    *,
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    model: str = "whisper-large-v3-turbo",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    response_format: str = "json",
    timestamp_granularities: Optional[Iterable[str]] = None,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
) -> tuple[str, str]:
    """Transcribe audio using Groq.

    Returns (text, detected_language_code).

    Parameters mirror Groq API docs. If both file_path and url are given, file_path wins.
    """
    client = groq_client(api_key)

    if not file_path and not url:
        raise ValueError("Provide either file_path or url for transcription.")

    file_obj = None
    if file_path:
        file_obj = open(file_path, "rb")

    kwargs = {
        "model": model,
        "temperature": temperature,
        "response_format": response_format,
    }
    if prompt:
        kwargs["prompt"] = prompt
    if language:
        kwargs["language"] = language
    if timestamp_granularities and response_format == "verbose_json":
        kwargs["timestamp_granularities"] = list(timestamp_granularities)
    if file_obj:
        kwargs["file"] = file_obj
    elif url:
        kwargs["url"] = url

    transcription = client.audio.transcriptions.create(**kwargs)

    # Robust text extraction
    text = getattr(transcription, "text", None) or (
        isinstance(transcription, dict) and transcription.get("text")
    ) or str(transcription)

    detected_language = "en"
    try:
        if text and text.strip():
            detected_language = detect(text)
    except LangDetectException:
        pass
    except Exception:
        pass

    if file_obj:
        file_obj.close()
    return text, detected_language


def groq_translate(
    *,
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    model: str = "whisper-large-v3",
    prompt: Optional[str] = None,
    response_format: str = "json",
    temperature: float = 0.0,
    api_key: Optional[str] = None,
) -> str:
    """Translate audio to English using Groq translations endpoint.

    Returns translated English text.
    """
    client = groq_client(api_key)
    if not file_path and not url:
        raise ValueError("Provide either file_path or url for translation.")

    file_obj = None
    if file_path:
        file_obj = open(file_path, "rb")

    kwargs = {
        "model": model,
        "language": "en",
        "response_format": response_format,
        "temperature": temperature,
    }
    if prompt:
        kwargs["prompt"] = prompt
    if file_obj:
        kwargs["file"] = file_obj
    elif url:
        kwargs["url"] = url

    translation = client.audio.translations.create(**kwargs)
    text = getattr(translation, "text", None) or (
        isinstance(translation, dict) and translation.get("text")
    ) or str(translation)
    if file_obj:
        file_obj.close()
    return text


def preprocess_audio(
    input_path: str,
    output_path: str,
    sample_rate: int = 16000,
    channels: int = 1,
    export_format: str = "flac",
) -> str:
    """Downsample + mono-convert audio for optimal STT.

    Uses pydub (ffmpeg backend). Returns path to processed file.
    """
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(sample_rate).set_channels(channels)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    audio.export(output_path, format=export_format)
    return output_path


def analyze_verbose_segments(verbose_json: dict) -> list[dict]:
    """Extract and annotate segment-level metadata from a verbose_json response.

    Returns list of segment dicts with basic quality flags.
    """
    segments = []
    data = verbose_json if isinstance(verbose_json, dict) else {}
    raw_segments = data.get("segments") or data.get("segments", [])
    if not raw_segments and "text" in data:
        # Some SDKs may flatten; attempt to reconstruct minimal info
        return []

    for seg in raw_segments:
        avg_logprob = seg.get("avg_logprob")
        no_speech_prob = seg.get("no_speech_prob")
        compression_ratio = seg.get("compression_ratio")
        flags = []
        if avg_logprob is not None and avg_logprob < -0.5:
            flags.append("low_confidence")
        if no_speech_prob is not None and no_speech_prob > 0.6:
            flags.append("possible_silence")
        if compression_ratio is not None and (compression_ratio < 0.5 or compression_ratio > 3.0):
            flags.append("unusual_speech_pattern")
        segments.append({
            "id": seg.get("id"),
            "text": seg.get("text"),
            "start": seg.get("start"),
            "end": seg.get("end"),
            "avg_logprob": avg_logprob,
            "no_speech_prob": no_speech_prob,
            "compression_ratio": compression_ratio,
            "flags": flags,
        })
    return segments


__all__ = [
    "record_audio",
    "transcribe_with_groq",
    "groq_transcribe",
    "groq_translate",
    "preprocess_audio",
    "analyze_verbose_segments",
]
