import os
from gtts import gTTS
from pathlib import Path
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

def text_to_speech_with_gtts(input_text: str, output_filepath: str, lang: str = "en") -> str:
    out_path = Path(output_filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    audioobj = gTTS(text=input_text, lang=lang if lang else "en", slow=False)
    try:
        audioobj.save(str(out_path))
    except Exception:
        raise
    return str(out_path)

def text_to_speech_with_openai(
    input_text: str,
    output_filepath: str,
    voice: str = "alloy",
    instructions: str | None = None,
    lang: str | None = None,
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if OpenAI is None or not api_key:
        # Fallback to gTTS and try to use the detected language
        return text_to_speech_with_gtts(input_text, output_filepath, lang=(lang or "en"))
    client = OpenAI(api_key=api_key)
    out_path = Path(output_filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=input_text,
            instructions=instructions,
        ) as response:
            response.stream_to_file(out_path)
        return output_filepath
    except Exception:
        return text_to_speech_with_gtts(input_text, output_filepath, lang=(lang or "en"))