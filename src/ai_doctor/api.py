from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
from .stt import groq_transcribe

app = FastAPI(title="AI Doctor STT API")


@app.post("/transcribe")
async def transcribe(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    model: str = Form("whisper-large-v3-turbo"),
    response_format: str = Form("json"),
):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="GROQ_API_KEY not set in environment")

    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either file upload or url.")

    file_path = None
    if file:
        contents = await file.read()
        tmp_path = f"temp_upload_{file.filename}"
        with open(tmp_path, "wb") as fh:
            fh.write(contents)
        file_path = tmp_path

    try:
        text, lang = groq_transcribe(file_path=file_path, url=url, model=model, api_key=api_key, response_format=response_format)
        return JSONResponse({"text": text, "language": lang})
    finally:
        if file and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


def ensure_session_media_dirs(session_id: str) -> dict:
    # Base path inside the project assets directory.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    assets_root = os.path.join(project_root, "assets")
    base_dir = os.path.join(assets_root, session_id)
    images_dir = os.path.join(base_dir, "images")
    audio_dir = os.path.join(base_dir, "audio")
    for d in (base_dir, images_dir, audio_dir):
        os.makedirs(d, exist_ok=True)
    return {"base": base_dir, "images": images_dir, "audio": audio_dir}


def _classify_media(filename: str) -> str:
    name = filename.lower()
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".wma"}
    _, ext = os.path.splitext(name)
    if ext in image_exts:
        return "image"
    if ext in audio_exts:
        return "audio"
    return "other"


@app.post("/upload-media")
async def upload_media(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...),
):
    if not session_id.strip():
        raise HTTPException(status_code=400, detail="session_id cannot be empty")
    if not files:
        raise HTTPException(status_code=400, detail="At least one file must be provided")

    dirs = ensure_session_media_dirs(session_id)
    stored = []
    for f in files:
        kind = _classify_media(f.filename)
        if kind == "other":
            # Skip unsupported file types but report
            stored.append({"filename": f.filename, "stored": False, "reason": "unsupported type"})
            continue
        target_dir = dirs["images"] if kind == "image" else dirs["audio"]
        # Prevent path traversal
        safe_name = os.path.basename(f.filename)
        target_path = os.path.join(target_dir, safe_name)
        try:
            contents = await f.read()
            with open(target_path, "wb") as out:
                out.write(contents)
            stored.append({"filename": safe_name, "stored": True, "kind": kind, "path": target_path})
        except Exception as e:
            stored.append({"filename": safe_name, "stored": False, "error": str(e)})

    return JSONResponse({"session_id": session_id, "directories": dirs, "files": stored})
