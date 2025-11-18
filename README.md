<div align="center">

# Optiwell AI Doctor

Multimodal prototype for educational medical triage combining:
image + text (Groq LLM), speech‑to‑text (Groq Whisper), and text‑to‑speech (OpenAI TTS with gTTS fallback) in a Gradio UI plus an optional FastAPI STT endpoint and MySQL persistence.

⚠️ Disclaimer: This project is for learning and demonstration only. It does NOT provide real medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical concerns.

</div>

---

## Table of Contents
1. Overview
2. Features
3. Architecture
4. Requirements
5. Installation (pip / Pipenv / Conda)
6. Environment Variables
7. Running the Gradio App
8. FastAPI STT Endpoint
9. Database Persistence (MySQL)
10. Docker (App & Full Stack)
11. Speech & Vision Workflows
12. Testing
13. Extensibility & Configuration
14. Troubleshooting
15. Roadmap

---

## 1. Overview
The Optiwell AI Doctor accepts an image (optional), free‑text symptom description, or recorded/uploaded audio. It forms a medical‑style prompt, queries a Groq multimodal LLM, and returns a concise paragraph styled as an educational doctor response. The response is converted to speech (OpenAI TTS if available, otherwise gTTS). Each interaction can be stored in MySQL for later analysis.

## 2. Features
- Vision + Text Fusion: Image embedding and textual prompt fused for multimodal analysis.
- Speech‑to‑Text (Groq Whisper): Supports file upload or microphone recording with auto language detection.
- Text‑to‑Speech: Streams OpenAI `gpt-4o-mini-tts` or falls back to gTTS when no API key.
- Session Logging: Patient/doctor exchanges persisted (session UUID) in MySQL.
- FastAPI Microservice: Dedicated `/transcribe` endpoint for STT.
- Temp File Hygiene: Audio uploads scheduled for auto‑cleanup.
- Pluggable Prompts: Centralized `SYSTEM_PROMPT` for easy tuning.

## 3. Architecture (High Level)
```
gradio_starter.py   -> loads .env then launches UI (create_app)
src/ai_doctor/
  prompts.py        -> SYSTEM_PROMPT (doctor style & constraints)
  vision.py         -> encode_image + LLM multimodal / text queries
  stt.py            -> record_audio, groq_transcribe, preprocess helpers
  tts.py            -> OpenAI or gTTS output
  ui.py             -> Gradio Blocks layout + wiring
  db.py             -> init_db, create_session, save_message, fetch_messages
  api.py            -> FastAPI app exposing POST /transcribe
```
Shim scripts (`brain_of_the_doctor.py`, `voice_of_the_patient.py`, `voice_of_the_doctor.py`) re‑export functions for backward compatibility.

## 4. Requirements
- Python 3.11
- FFmpeg (audio conversion via pydub)
- PortAudio (for microphone capture via `speech_recognition` / PyAudio)
- MySQL 8+ (optional; required for persistence)

### Install FFmpeg & PortAudio
macOS (Homebrew):
```bash
brew install ffmpeg portaudio mysql
```
Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg portaudio19-dev libportaudio2 mysql-server
```
Windows:
1. Download FFmpeg static build -> extract to `C:\ffmpeg` -> add `C:\ffmpeg\bin` to PATH.
2. Install PyAudio dependencies (already bundled via wheel where available) / PortAudio dev build if needed.
3. Install MySQL from official installer.

## 5. Installation
### pip + venv
```powershell
python -m venv venv
& venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Pipenv
```powershell
pip install pipenv
pipenv install
pipenv shell
```

### Conda
```bash
conda create -n optiwell python=3.11
conda activate optiwell
pip install -r requirements.txt
```

## 6. Environment Variables
Required / optional keys:
```
GROQ_API_KEY=your_groq_key               # required for vision & STT
OPENAI_API_KEY=your_openai_key_optional  # optional (enables OpenAI TTS)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
```
Windows (session):
```powershell
$env:GROQ_API_KEY='your_groq_key'
$env:OPENAI_API_KEY='your_openai_key'
```
Persist (Windows):
```powershell
setx GROQ_API_KEY "your_groq_key"
setx OPENAI_API_KEY "your_openai_key"
```
Place a `.env` file at project root if preferred:
```
GROQ_API_KEY=...
OPENAI_API_KEY=...
DB_PASSWORD=...
```

## 7. Running the Gradio App
```powershell
python gradio_starter.py
```
Open http://127.0.0.1:7860

UI Panels:
- Image (optional) – adds multimodal context.
- Patient Input – text or auto‑filled via transcription.
- Speech Input Accordion – record or upload audio then click Transcribe.
- Submit – runs prompt assembly → LLM → TTS.

## 8. FastAPI STT Endpoint
Launch standalone:
```powershell
uvicorn src.ai_doctor.api:app --reload --port 8000
```
File upload:
```powershell
curl -X POST http://127.0.0.1:8000/transcribe -F "file=@sample.wav" -F "model=whisper-large-v3-turbo"
```
Remote URL:
```powershell
curl -X POST http://127.0.0.1:8000/transcribe -F "url=https://example.com/audio.wav"
```
Response JSON:
```json
{ "text": "...", "language": "en" }
```

### Media Upload Endpoint (/upload-media)
Store patient‑submitted images and videos under the project `assets` directory, separated per session.

Folder layout (created on demand):
```
assets/
  <session_id>/
    images/   # image files (.jpg .png ...)
    audio/    # audio files (.mp3 .wav .m4a .ogg ...)
```

Example (multiple files):
```powershell
curl -X POST http://127.0.0.1:8000/upload-media ^
  -F "session_id=123e4567" ^
  -F "files=@assets/images/sample_skin.jpg" ^
  -F "files=@assets/audio/patient_voice_test_for_patient.mp4"
```

Response sample (paths will be absolute on Windows):
```json
{
  "session_id": "123e4567",
  "directories": {
    "base": "assets/123e4567",
    "images": "assets/123e4567/images",
    "videos": "assets/123e4567/videos"
  },
  "files": [
    {"filename": "sample_skin.jpg", "stored": true, "kind": "image", "path": "assets/123e4567/images/sample_skin.jpg"},
    {"filename": "patient_voice_test_for_patient.mp3", "stored": true, "kind": "audio", "path": "assets/123e4567/audio/patient_voice_test_for_patient.mp3"}
  ]
}
```

Unsupported extensions are skipped with `stored=false` and a reason.

### Whisper Model Guidance
- Highest quality: `whisper-large-v3`
- Faster / cheaper: `whisper-large-v3-turbo`

## 9. Database Persistence (MySQL)
On app start:
1. Create database `Optiwell` if missing.
2. Create tables `sessions`, `messages`.
3. Generate a session UUID.

Schema:
```
sessions(id PK, session_uuid UNIQUE, created_at)
messages(id PK, session_uuid FK, role ENUM('patient','doctor'), content TEXT, image_path VARCHAR(255), created_at)
```
Manual test (PowerShell):
```powershell
python - <<'PY'
from src.ai_doctor.db import init_db, create_session, save_message
init_db(); sid=create_session();
save_message(sid,'patient','Ping',None); save_message(sid,'doctor','Pong',None);
print('Session', sid, 'OK')
PY
```

## 10. Docker
### App Only
```powershell
docker build -t optiwell-app .
docker run --rm -p 7860:7860 ^
  -e GROQ_API_KEY=$env:GROQ_API_KEY ^
  -e OPENAI_API_KEY=$env:OPENAI_API_KEY optiwell-app
```

### Compose (App + MySQL)
Create `.env` (optional):
```
DB_PASSWORD=rootpassword
GROQ_API_KEY=your_groq
OPENAI_API_KEY=your_openai_optional
```
Run:
```powershell
docker compose up --build
```
Rebuild:
```powershell
docker compose build app
docker compose up -d
```
Stop & remove volume:
```powershell
docker compose down -v
```

Expose only API (edit compose service command):
```yaml
command: uvicorn src.ai_doctor.api:app --host 0.0.0.0 --port 8000
```

## 11. Speech & Vision Workflows
Speech Flow:
```
Microphone/File -> temp copy -> groq_transcribe() -> text + lang -> prompt assembly -> LLM -> TTS -> final.mp3
```
Vision Flow:
```
Image -> encode_image() (base64) -> SYSTEM_PROMPT + patient text -> Groq multimodal model -> response -> TTS
```

## 12. Testing
Pytest DB flow tests (requires running MySQL or accessible container):
```powershell
pytest -q
```
Selective:
```powershell
pytest tests/test_db_flow.py::test_db_flow_insert_and_fetch -q
```

## 13. Extensibility & Configuration
- Prompt Tuning: Edit `prompts.py` SYSTEM_PROMPT.
- Alternate Models: Change default model in `vision.py` / UI logic.
- Additional Metadata: Extend `messages` table columns (e.g., severity score).
- STT Enhancements: Use `verbose_json` response format + `analyze_verbose_segments` for confidence overlays.
- Auth: Wrap FastAPI with auth middleware (e.g., API keys, JWT).

## 14. Troubleshooting
| Issue | Cause | Fix |
|-------|-------|-----|
| Missing GROQ key message | `GROQ_API_KEY` unset | Export or put in `.env` |
| TTS fallback to gTTS | No `OPENAI_API_KEY` or OpenAI import | Set key / install `openai` |
| Microphone errors | PortAudio not found | Install PortAudio / PyAudio, restart shell |
| MySQL connection fail | Service not running / wrong password | Start MySQL, verify env vars |
| Empty transcription | Low quality audio or wrong model | Try `whisper-large-v3`, preprocess audio |

## 15. Roadmap
- [ ] Streaming real‑time transcription
- [ ] Segment confidence visualization
- [ ] Basic authentication & rate limiting
- [ ] Export session logs (CSV/JSON)
- [ ] Docker multi‑arch build
- [ ] Enhanced medical safety disclaimers & guardrails

---

## Minimal Code Examples
Transcription:
```python
from src.ai_doctor.stt import groq_transcribe
text, lang = groq_transcribe(file_path="sample.wav", model="whisper-large-v3-turbo")
print(lang, text)
```
TTS:
```python
from src.ai_doctor.tts import text_to_speech_with_openai
audio_path = text_to_speech_with_openai("Hello patient", "outputs/hello.mp3")
```
Vision Query:
```python
from src.ai_doctor.vision import encode_image, analyze_image_with_query
enc = encode_image("assets/images/acne.jpg")
resp = analyze_image_with_query("Describe findings", "meta-llama/llama-4-scout-17b-16e-instruct", enc)
```

---

## Maintenance Notes
- Temp audio deletion scheduled in `ui.py` (~5 minutes).
- Update dependencies via `pip install -r requirements.txt --upgrade` cautiously.
- Ensure FFmpeg stays on PATH after OS updates.

## Related Internal Docs
- `src/ai_doctor/README.md` – API & module specifics.
- `assets/README.md` – Sample media guidelines.

---

If you build on this, please retain the educational disclaimer and verify any medical phrasing before external use.



