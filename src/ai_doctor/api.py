from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
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
