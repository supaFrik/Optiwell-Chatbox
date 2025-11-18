# ai_doctor Package Reference

Core multimodal logic for Optiwell AI Doctor.

## Modules
- `prompts.py` – Defines `SYSTEM_PROMPT` medical guidance.
- `vision.py` – Image + text analysis via Groq LLM.
  - `encode_image(path)`
  - `analyze_image_with_query(query, model, encoded_image)`
  - `analyze_text_query(query, model=...)`
- `stt.py` – Speech utilities.
  - `record_audio(file_path, timeout, phrase_time_limit)`
  - `groq_transcribe(file_path|url, model, response_format, timestamp_granularities)` → `(text, lang)`
  - `groq_translate(file_path|url, model)` → English text
  - `preprocess_audio(input, output)`
  - `analyze_verbose_segments(verbose_json)`
- `tts.py` – Text to speech.
  - `text_to_speech_with_openai(input_text, output_filepath, voice, instructions, lang)`
  - `text_to_speech_with_gtts(input_text, output_filepath, lang)`
- `ui.py` – Gradio app builder (`create_app()`). Speech Input accordion handles audio capture + transcription + temp cleanup.
- `api.py` – FastAPI app exposing `POST /transcribe`.
- `__init__.py` – Public exports for top-level imports.

## Environment Variables
- `GROQ_API_KEY` (required for vision/STT)
- `OPENAI_API_KEY` (optional for OpenAI TTS)

## Typical Flow (UI)
1. User provides image and/or text.
2. (Optional) records or uploads audio → transcription populates text box.
3. Submit → vision/text analysis → TTS generation.

## FastAPI STT
Run:
```powershell
uvicorn src.ai_doctor.api:app --reload --port 8000
```
Request:
```powershell
curl -X POST http://127.0.0.1:8000/transcribe -F "file=@sample.wav" -F "model=whisper-large-v3-turbo"
```

## Model Selection (Whisper)
- Accuracy: `whisper-large-v3`
- Cost/Speed: `whisper-large-v3-turbo`

## Temp Files
Audio temp files auto-delete (~5 min) in `ui_transcribe_audio`.

## Extension Ideas
- Streaming STT
- Segment confidence UI (using `analyze_verbose_segments`)
- Authentication for API
