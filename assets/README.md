# Assets Directory

Holds example media used for testing and demonstration.

## Subfolders
- `images/` – Medical sample images (e.g., `acne.jpg`, `skin_rash.jpg`). Use with the UI image input or encode via `encode_image`.
- `audio/` – Sample audio clip(s) for STT testing.

## Usage Examples
Image encode:
```python
from src.ai_doctor.vision import encode_image
b64 = encode_image("assets/images/acne.jpg")
```

Audio transcription test:
```powershell
curl -X POST http://127.0.0.1:8000/transcribe -F "file=@assets/audio/127389__acclivity__thetimehascome.wav"
```

## Guidelines
- Keep only lightweight, non-sensitive sample data.
- Prefer anonymized images.
- Large test audio: preprocess or chunk before uploading to Groq.
