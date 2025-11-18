# Optiwell AI Doctor – Comprehensive Reference

This document provides a full reference of the project structure, purpose of each file/folder, core workflows (Vision, STT, TTS), and integration points (UI + API). Use this alongside the concise `README.md`.

## 1. High-Level Overview
Optiwell AI Doctor is a multimodal triage assistant that:
- Accepts text or image (medical photo) input and queries Groq LLM models.
- Records or uploads patient speech, transcribes via Groq Whisper models.
- Synthesizes doctor voice responses via OpenAI TTS (fallback to gTTS).
- Provides both a Gradio UI and a FastAPI endpoint for speech transcription.

## 2. Directory Structure
```
Optiwell Chatbox/
├─ ai-doctor-2.0-voice-and-vision/        (legacy subfolder; active code placed directly under root now)
├─ assets/
│  ├─ images/                             Example medical images (acne, rash)
│  └─ audio/                              Sample audio assets
├─ brain_of_the_doctor.py                 Deprecated shim -> re-exports vision utilities
├─ docs/                                  Slide decks / PDFs (non-code resources)
├─ gradio_starter.py                      Boots environment (.env) then launches Gradio UI
├─ outputs/                               Generated output artifacts (e.g. final.mp3)
├─ patient_voice_auto_record.mp3          Example recorded patient audio
├─ Pipfile / Pipfile.lock                 Optional Pipenv environment definition
├─ README.md                              Concise usage & setup guide
├─ REFERENCE.md                           (This file) full reference
├─ requirements.txt                       Python dependencies
├─ scripts/                               (Currently empty; place utility scripts here)
├─ src/
│  └─ ai_doctor/
│     ├─ __init__.py                      Public package exports
│     ├─ api.py                           FastAPI app exposing /transcribe endpoint
│     ├─ prompts.py                       SYSTEM_PROMPT controlling medical response style
│     ├─ stt.py                           Speech recording + Groq transcription & translation helpers
│     ├─ tts.py                           Text-to-speech (OpenAI primary, gTTS fallback)
│     ├─ ui.py                            Gradio Blocks UI definition
│     ├─ vision.py                        Image & text analysis via Groq chat completions
│     └─ __pycache__/                     Python cache artifacts
├─ voice_of_the_doctor.py                 Deprecated shim -> re-exports tts functions
├─ voice_of_the_patient.py                Deprecated shim -> re-exports stt functions
└─ __pycache__/                           Root-level Python cache artifacts
```

## 3. Key Modules
### 3.1 `prompts.py`
- Defines `SYSTEM_PROMPT`: medical guidance and stylistic constraints for responses.

### 3.2 `vision.py`
- `encode_image(path)` → base64 string for inline image sending.
- `analyze_image_with_query(query, model, encoded_image)` → multimodal LLM call.
- `analyze_text_query(query, model=...)` → pure text query.
- Requires `GROQ_API_KEY`.

### 3.3 `stt.py`
Core speech-to-text utilities:
- `record_audio(file_path, timeout=..., phrase_time_limit=...)` (microphone capture using SpeechRecognition + pydub MP3 export).
- `groq_transcribe(file_path=..., url=..., model=..., response_format='json', timestamp_granularities=[...])` → returns `(text, detected_language)`.
- `groq_translate(file_path=..., url=..., model='whisper-large-v3')` → translate to English.
- `preprocess_audio(input_path, output_path, sample_rate=16000, channels=1, export_format='flac')` → downsampling helper.
- `analyze_verbose_segments(verbose_json)` → interpret Whisper metadata flags.
- Backward compatibility: `transcribe_with_groq(...)` wrapper.

### 3.4 `tts.py`
Text-to-speech strategies:
- `text_to_speech_with_openai(...)` uses `gpt-4o-mini-tts` when `OPENAI_API_KEY` exists.
- `text_to_speech_with_gtts(...)` fallback using gTTS (supports basic languages; primary usage English).

### 3.5 `ui.py`
Gradio interface:
- Image upload, text input, speech input accordion (record/upload → transcribe).
- Uses `ui_transcribe_audio(...)` internally to normalize audio and forward to Groq.
- Auto-deletes temporary audio files after ~5 minutes.
- Produces doctor response text + synthesized audio.

### 3.6 `api.py`
FastAPI microservice:
- `POST /transcribe` accepts either `file` multipart upload or `url` form field.
- Parameters: `model`, `response_format` (default `json`).
- Returns JSON `{ "text": ..., "language": ... }`.

### 3.7 Shim Files (Deprecated)
- `brain_of_the_doctor.py`, `voice_of_the_patient.py`, `voice_of_the_doctor.py` now only re-export package functions to avoid breaking older imports.

## 4. Dependency Notes
Primary libraries:
- Gradio (UI)
- Groq SDK (`groq`) for Whisper + LLM
- OpenAI SDK (`openai`) for TTS (optional)
- gTTS fallback for TTS
- SpeechRecognition + pydub + portaudio/ffmpeg for microphone capture
- FastAPI + Uvicorn for API service

Ensure system dependencies: FFmpeg, PortAudio. On Windows install appropriate binaries and add to PATH.

## 5. Environment Configuration
Mandatory:
- `GROQ_API_KEY`: required for vision and STT.
Optional:
- `OPENAI_API_KEY`: enables enhanced TTS; otherwise fallback.

Example (PowerShell):
```powershell
$env:GROQ_API_KEY="your_groq_key"
$env:OPENAI_API_KEY="your_openai_key"
```

Persistent:
```powershell
setx GROQ_API_KEY "your_groq_key"
setx OPENAI_API_KEY "your_openai_key"
```
Restart terminal after `setx`.

## 6. Running Components
### Gradio UI
```powershell
python gradio_starter.py
# or
python -m src.ai_doctor.ui
```
Visit: http://127.0.0.1:7860

### FastAPI STT Service
```powershell
uvicorn src.ai_doctor.api:app --reload --port 8000
```
Test:
```powershell
curl -X POST http://127.0.0.1:8000/transcribe -F "file=@sample.wav" -F "model=whisper-large-v3-turbo"
```

## 7. Speech Input Flow (UI)
1. Record or upload audio.
2. Click "Transcribe Audio".
3. Transcription populates patient text.
4. Submit to get medical response + doctor voice.
5. Temp file auto-deletes after ~5 minutes.

## 8. Choosing STT Model
| Use Case | Model | Notes |
|----------|-------|-------|
| Highest accuracy multilingual | whisper-large-v3 | Supports translation & transcription |
| Fast, cost-efficient transcription | whisper-large-v3-turbo | No translation endpoint |

## 9. Handling Large Audio
Preprocess or chunk when exceeding size limits:
```python
from src.ai_doctor.stt import preprocess_audio
processed = preprocess_audio("large.mp3", "downsampled.flac")
```
For advanced chunking, implement segmentation + overlap merging (see Groq cookbook).

## 10. Error Handling Patterns
- Missing key → human-readable message (vision, STT).
- Transcription failures return status in UI language/status textbox.
- TTS failures fallback to gTTS silently returning a valid path.

## 11. Extensibility Suggestions
| Goal | Approach |
|------|----------|
| Add streaming STT | Implement incremental chunks and unify before display |
| More TTS voices | Parameterize `voice` list & expose dropdown in UI |
| Persist sessions | Add lightweight DB (SQLite) storing interactions |
| Rich metadata view | Surface segment flags from `analyze_verbose_segments` in UI table |
| Authentication | Add API key middleware for FastAPI endpoints |

## 12. Maintenance & Temp Files
- Temp audio stored in OS temp under `ai_doctor_temp/` and cleaned after ~300s.
- Adjust timing logic in `ui_transcribe_audio` if retention needs change.

## 13. Public API Summary
| Function | File | Purpose |
|----------|------|---------|
| `groq_transcribe` | stt.py | Transcribe audio file or URL |
| `groq_translate` | stt.py | Translate non-English audio to English |
| `preprocess_audio` | stt.py | Downsample + mono convert |
| `analyze_verbose_segments` | stt.py | Quality flags for verbose_json |
| `text_to_speech_with_openai` | tts.py | Generate speech via OpenAI |
| `text_to_speech_with_gtts` | tts.py | Fallback speech synth |
| `encode_image` | vision.py | Base64 image encoding |
| `analyze_image_with_query` | vision.py | Multimodal image+text LLM query |
| `analyze_text_query` | vision.py | Text-only LLM query |
| `create_app` | ui.py | Build Gradio Blocks instance |
| FastAPI `/transcribe` | api.py | HTTP transcription service |

## 14. License & Compliance
(Insert license details if applicable. Currently no explicit license file.)

## 15. Troubleshooting Quick Checks
| Symptom | Check |
|---------|-------|
| Vision returns key error | Ensure `GROQ_API_KEY` set |
| TTS falls back unexpectedly | Verify `OPENAI_API_KEY` valid & not rate-limited |
| STT empty text | Confirm audio path exists & supported format |
| API 400 error | Ensure file or url provided in form data |
| Temp files not deleted | Verify timer threads not blocked; inspect OS temp dir |

## 16. Roadmap Ideas
- Realtime streaming (WebSocket) for conversation.
- Integration with medical ontology for structured differential.
- Multi-speaker diarization pre-processing option.
- UI segment confidence heatmap.

---
For concise run instructions use `README.md`. This reference emphasizes internal architecture and extension points.
