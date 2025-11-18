import os
import gradio as gr
from .prompts import SYSTEM_PROMPT
from .vision import encode_image, analyze_image_with_query, analyze_text_query
from .tts import text_to_speech_with_openai
from .stt import groq_transcribe
from .db import init_db, create_session, save_message

from typing import Optional, Tuple
from pathlib import Path
import shutil
import threading
import uuid
import base64
import tempfile


def process_inputs(image_filepath, patient_text):
    patient_text = patient_text or ""
    if image_filepath:
        doctor_query = SYSTEM_PROMPT + patient_text
        doctor_response = analyze_image_with_query(
            query=doctor_query,
            encoded_image=encode_image(image_filepath),
            model="meta-llama/llama-4-scout-17b-16e-instruct",
        )
    elif patient_text.strip():
        doctor_query = SYSTEM_PROMPT + patient_text
        doctor_response = analyze_text_query(query=doctor_query)
    else:
        doctor_response = "No input provided. Please provide an image or chat text."

    tts_out_path = os.path.join("outputs", "final.mp3")
    voice_of_doctor = text_to_speech_with_openai(
        input_text=doctor_response,
        output_filepath=tts_out_path,
        lang="en",
    )
    return doctor_response, voice_of_doctor

def process_and_log(image_filepath, patient_text, session_uuid):
    doctor_response, voice_path = process_inputs(image_filepath, patient_text)
    try:
        if patient_text and patient_text.strip():
            save_message(session_uuid, "patient", patient_text, image_filepath)
        if doctor_response:
            save_message(session_uuid, "doctor", doctor_response, None)
    except Exception as e:
        # Non-fatal; log to console
        print(f"DB logging failed: {e}")
    return doctor_response, voice_path


def ui_transcribe_audio(audio_file: Optional[str], file_obj: Optional[str]) -> Tuple[str, str, Optional[str]]:
    """Transcribe an uploaded or recorded audio clip and return (text, language).

    `audio_file` is a Gradio-uploaded path, `file_obj` is an alternative file path.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return ("", "GROQ_API_KEY not set in environment", None)

    # Prefer direct upload path provided by Gradio (audio_file)
    source = audio_file or file_obj
    if not source:
        return ("", "No audio provided", None)

    # Prepare temp directory for copying/storing incoming audio
    TEMP_DIR = Path(tempfile.gettempdir()) / "ai_doctor_temp"
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def schedule_delete(p: Path, delay: int = 300):
        def _del():
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass

        t = threading.Timer(delay, _del)
        t.daemon = True
        t.start()

    # Normalize common Gradio return formats to a filesystem path and copy into temp dir
    dest_path = None
    try:
        if isinstance(source, str):
            src_path = Path(source)
            if src_path.exists():
                dest_path = TEMP_DIR / f"{uuid.uuid4().hex}{src_path.suffix or '.wav'}"
                shutil.copy2(src_path, dest_path)
            else:
                # sometimes Gradio returns a URL string
                # let groq_transcribe handle URL directly
                dest_path = str(source)
        elif isinstance(source, dict):
            # support keys that may hold a tmp path
            path_candidate = source.get("tmp_path") or source.get("path") or source.get("name")
            data = source.get("data")
            if path_candidate and Path(path_candidate).exists():
                src_path = Path(path_candidate)
                dest_path = TEMP_DIR / f"{uuid.uuid4().hex}{src_path.suffix or '.wav'}"
                shutil.copy2(src_path, dest_path)
            elif data:
                # data may be a data URL or raw base64/bytes
                if isinstance(data, str) and data.startswith("data:"):
                    header, b64 = data.split(",", 1)
                    ext = ".wav"
                    if "wav" in header:
                        ext = ".wav"
                    elif "mp3" in header:
                        ext = ".mp3"
                    dest_path = TEMP_DIR / f"{uuid.uuid4().hex}{ext}"
                    with open(dest_path, "wb") as fh:
                        fh.write(base64.b64decode(b64))
                elif isinstance(data, (bytes, bytearray)):
                    dest_path = TEMP_DIR / f"{uuid.uuid4().hex}.wav"
                    with open(dest_path, "wb") as fh:
                        fh.write(data)
                else:
                    return ("", "Unsupported data payload from Gradio audio component", None)
            else:
                return ("", "Could not find audio data in upload", None)
        elif isinstance(source, (list, tuple)) and len(source) == 2:
            return ("", "Recorded audio returned as array; set the audio component to return filepaths (type='filepath').", None)
        else:
            return ("", "Unsupported audio input type", None)
    except Exception as e:
        return ("", f"Failed to normalize audio input: {e}", None)

    # If dest_path is a Path, schedule its deletion after a delay and use path for transcription
    preview_path = None
    transcribe_path = None
    if isinstance(dest_path, Path):
        preview_path = str(dest_path)
        transcribe_path = str(dest_path)
        schedule_delete(dest_path, delay=300)
    else:
        # dest_path might be a URL string
        transcribe_path = dest_path
        preview_path = None

    try:
        text, lang = groq_transcribe(file_path=transcribe_path if isinstance(transcribe_path, str) else None, url=(transcribe_path if (isinstance(transcribe_path, str) and transcribe_path.startswith('http')) else None), model="whisper-large-v3-turbo", api_key=api_key, response_format="json")
        return (text or "", lang or "", preview_path)
    except Exception as e:
        return ("", f"Transcription failed: {e}", preview_path)


def create_app():
    # Initialize DB & session
    try:
        init_db()
    except Exception as e:
        print(f"Database init error: {e}")
    session_uuid = create_session()
    with gr.Blocks() as demo:
        gr.Markdown("# AI Doctor (Vision + Text)")
        with gr.Row():
            with gr.Column():
                image_in = gr.Image(type="filepath", label="Image (optional)")
                patient_text = gr.Textbox(label="Patient Input", placeholder="Describe symptoms here", lines=4)
                # Speech-to-text panel
                with gr.Accordion("Speech Input (record or upload)", open=False):
                    audio_rec = gr.Audio(sources=["microphone"], type="filepath", label="Record or upload audio")
                    audio_file = gr.File(label="Upload audio file (optional)")
                    transcribe_btn = gr.Button("Transcribe Audio")
                    detected_lang = gr.Textbox(label="Detected Language / Status", interactive=False)
                    audio_preview = gr.Audio(label="Preview Audio", interactive=False)
                submit_btn = gr.Button("Submit", variant="primary")
            with gr.Column():
                doctor_out = gr.Textbox(label="Doctor's Response", lines=10)
                audio_out = gr.Audio(label="Doctor Voice", visible=True)
                session_state = gr.State(session_uuid)

        # Wire transcription button: populate patient_text and show language/status
        transcribe_btn.click(
            fn=ui_transcribe_audio,
            inputs=[audio_rec, audio_file],
            outputs=[patient_text, detected_lang, audio_preview],
        )

        submit_btn.click(
            fn=process_and_log,
            inputs=[image_in, patient_text, session_state],
            outputs=[doctor_out, audio_out],
        )
    return demo