# Optiwell AI Doctor

Multimodal medical triage prototype: image + text analysis (Groq LLM), speech-to-text (Groq Whisper), and text-to-speech (OpenAI or gTTS fallback) behind a Gradio UI and optional FastAPI endpoint.

## Quick Start

```powershell
python -m venv venv
& venv\Scripts\Activate.ps1
pip install -r requirements.txt
# set keys
$env:GROQ_API_KEY="your_groq_key"
$env:OPENAI_API_KEY="optional_openai_key"  # for TTS; omit to use gTTS fallback
python gradio_starter.py
```

Open http://127.0.0.1:7860

## Environment Variables

```
GROQ_API_KEY=...
OPENAI_API_KEY=...   # optional
```
Windows persistence:
```powershell
setx GROQ_API_KEY "your_groq_key"
setx OPENAI_API_KEY "your_openai_key"
```

## UI Overview

- Image input (optional) for vision analysis.
- Text box for manual symptom description.
- Speech Input accordion:
  - Record or upload audio, click "Transcribe Audio".
  - Transcribed text populates Patient Input.
  - Detected language/status shown; preview audio playable.
- Submit runs medical prompt workflow and returns response + generated doctor voice.

## FastAPI STT Endpoint (optional)

Run:
```powershell
uvicorn src.ai_doctor.api:app --reload --port 8000
```
Transcribe via curl (file upload):
```powershell
curl -X POST http://127.0.0.1:8000/transcribe -F "file=@sample.wav" -F "model=whisper-large-v3-turbo"
```
Or with URL:
```powershell
curl -X POST http://127.0.0.1:8000/transcribe -F "url=https://example.com/audio.wav"
```

## Groq Speech-to-Text Helpers

Located in `src/ai_doctor/stt.py`:
- `groq_transcribe(file_path=..., url=..., model=..., response_format=...)`
- `groq_translate(file_path=...)` (English translation via translation endpoint)
- `preprocess_audio(input, output)` downsample/mono to 16kHz FLAC
- `analyze_verbose_segments(verbose_json)` flag low-confidence segments

Example:
```python
from src.ai_doctor.stt import groq_transcribe
text, lang = groq_transcribe(file_path="sample.wav", model="whisper-large-v3-turbo")
print(lang, text)
```

## Choosing Whisper Model
- Accuracy: `whisper-large-v3`
- Speed/cost: `whisper-large-v3-turbo`

## TTS
`src/ai_doctor/tts.py` attempts OpenAI TTS (`gpt-4o-mini-tts`); falls back to gTTS if missing key.

## Architecture

## Installing FFmpeg and PortAudio

### macOS

1. **Install Homebrew** (if not already installed):

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install FFmpeg and PortAudio:**

   ```bash
   brew install ffmpeg portaudio
   ```


### Linux
For Debian-based distributions (e.g., Ubuntu):

1. **Update the package list**

```
sudo apt update
```

2. **Install FFmpeg and PortAudio:**
```
sudo apt install ffmpeg portaudio19-dev
```

### Windows

#### Download FFmpeg:
1. Visit the official FFmpeg download page: [FFmpeg Downloads](https://ffmpeg.org/download.html)
2. Navigate to the Windows builds section and download the latest static build.

#### Extract and Set Up FFmpeg:
1. Extract the downloaded ZIP file to a folder (e.g., `C:\ffmpeg`).
2. Add the `bin` directory to your system's PATH:
   - Search for "Environment Variables" in the Start menu.
   - Click on "Edit the system environment variables."
   - In the System Properties window, click on "Environment Variables."
   - Under "System variables," select the "Path" variable and click "Edit."
   - Click "New" and add the path to the `bin` directory (e.g., `C:\ffmpeg\bin`).
   - Click "OK" to apply the changes.

#### Install PortAudio:
1. Download the PortAudio binaries from the official website: [PortAudio Downloads](http://www.portaudio.com/download.html)
2. Follow the installation instructions provided on the website.

---

## Setting Up a Python Virtual Environment

### Using Pipenv
1. **Install Pipenv (if not already installed):**  
```
pip install pipenv
```

2. **Install Dependencies with Pipenv:** 

```
pipenv install
```

3. **Activate the Virtual Environment:** 

```
pipenv shell
```

---

### Using `pip` and `venv`
#### Create a Virtual Environment:
```
python -m venv venv
```

#### Activate the Virtual Environment:
**macOS/Linux:**
```
source venv/bin/activate
```

**Windows:**
```
venv\Scripts\activate
```

#### Install Dependencies:
```
pip install -r requirements.txt
```

---

### Using Conda
#### Create a Conda Environment:
```
conda create --name myenv python=3.11
```

#### Activate the Conda Environment:
```
conda activate myenv
```

#### Install Dependencies:
```
pip install -r requirements.txt
```


Deprecated shim scripts (`brain_of_the_doctor.py`, `voice_of_the_patient.py`, `voice_of_the_doctor.py`) now just re-export functions; use the UI or import from `src.ai_doctor` directly.

## Detailed References
For deeper architectural details see:
- `src/ai_doctor/README.md` – Core package & APIs
- `assets/README.md` – Media assets usage
- `docs/README.md` – Documentation artifacts
- `scripts/README.md` – Utility script guidelines
- `REFERENCE.md` – Comprehensive project reference

## Environment Variables

Set the following in your shell or a `.env` file at the project root:

```
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
```

Windows (temporary session):
```
$env:OPENAI_API_KEY = 'your_openai_key_here'
$env:GROQ_API_KEY = 'your_groq_key_here'
```

Windows (persist for new shells):
```
setx OPENAI_API_KEY "your_openai_key_here"
setx GROQ_API_KEY "your_groq_key_here"
setx DB_HOST "localhost"
setx DB_PORT "3306"
setx DB_USER "root"
setx DB_PASSWORD "your_mysql_password"
```

If `OPENAI_API_KEY` is missing the app will fall back to gTTS for doctor voice output.

## MySQL Persistence

The app now logs patient and doctor messages to a MySQL database named `Optiwell`.

Environment variables control the connection:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
```

On first launch the code will:
1. Create the database `Optiwell` if it does not exist.
2. Create tables `sessions` and `messages`.
3. Generate a session UUID per Gradio app instance and store each patient/doctor exchange.

Schema overview:
```
sessions(id PK, session_uuid UNIQUE, created_at)
messages(id PK, session_uuid FK->sessions.session_uuid, role ENUM('patient','doctor'), content TEXT, image_path VARCHAR(255), created_at)
```

Install MySQL (if not already):
Windows: Download installer from https://dev.mysql.com/downloads/mysql/ and follow setup (ensure you note the root password).
macOS (Homebrew): `brew install mysql` then `brew services start mysql`.
Linux (Debian/Ubuntu): `sudo apt update && sudo apt install mysql-server`.

Test connectivity (PowerShell):
```powershell
python - <<'PY'
from src.ai_doctor.db import init_db, create_session, save_message
init_db()
sid = create_session()
save_message(sid, 'patient', 'Test symptoms', None)
save_message(sid, 'doctor', 'Test response', None)
print('Inserted sample messages for session', sid)
PY
```

If you see a connection error, verify that the MySQL service is running and credentials match the environment variables.

## Docker Usage

### Quick Local Build (App only)
```powershell
docker build -t optiwell-app .
docker run --rm -p 7860:7860 ^
   -e GROQ_API_KEY=$env:GROQ_API_KEY ^
   -e OPENAI_API_KEY=$env:OPENAI_API_KEY ^
   -e DB_HOST=$env:DB_HOST -e DB_PORT=$env:DB_PORT -e DB_USER=$env:DB_USER -e DB_PASSWORD=$env:DB_PASSWORD \
   optiwell-app
```

### Full Stack (App + MySQL)
Create an `.env` file (optional) with:
```
DB_PASSWORD=rootpassword
GROQ_API_KEY=your_groq
OPENAI_API_KEY=your_openai_optional
```
Then run:
```powershell
docker compose up --build
```
Access UI at http://localhost:7860

MySQL is exposed on `localhost:3306` (root / DB_PASSWORD). The database `Optiwell` and tables are auto-created at app start.

### Tear Down
```powershell
docker compose down
```

### Persisted Data
MySQL data stored in the named volume `mysql_data`. Remove it with:
```powershell
docker compose down -v
```

### Health Check
Compose file includes a simple MySQL healthcheck. App starts after container creation; initialization retries are handled in code.

### Rebuilding After Changes
```powershell
docker compose build app
docker compose up -d
```

### Using FastAPI Endpoint in Docker
Modify the app service command if you prefer the STT API only:
```yaml
      command: uvicorn src.ai_doctor.api:app --host 0.0.0.0 --port 8000
```
Then expose `8000:8000` in ports.

## Architecture

```
ai-doctor-2.0-voice-and-vision/
├─ gradio_app.py                # Thin wrapper; launches Blocks app from package
├─ src/
│  └─ ai_doctor/
│     ├─ __init__.py            # Re-exports public symbols
│     ├─ prompts.py             # System prompt constants
│     ├─ vision.py              # Image encoding + multimodal LLM calls
│     ├─ stt.py                 # Audio recording + Groq transcription
│     ├─ tts.py                 # OpenAI TTS with gTTS fallback
│     └─ ui.py                  # Gradio Blocks UI construction
├─ brain_of_the_doctor.py       # Deprecated shim -> src.ai_doctor.vision
├─ voice_of_the_patient.py      # Deprecated shim -> src.ai_doctor.stt
├─ voice_of_the_doctor.py       # Deprecated shim -> src.ai_doctor.tts
├─ assets/
│  └─ images/                   # (Optional) place example medical images
├─ requirements.txt / Pipfile   # Dependencies (openai, groq, gradio, etc.)
├─ README.md                    # This file
```

## Maintenance
Temp audio files auto-delete after ~5 minutes. Adjust logic in `ui.py` if needed.


