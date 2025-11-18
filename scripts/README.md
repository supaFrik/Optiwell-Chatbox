# scripts Directory

Currently empty placeholder for future maintenance or utility scripts.

Suggested additions:
- Audio batch preprocessing tool (wraps `preprocess_audio`).
- Chunking helper for large transcription jobs.
- Log cleanup or temp file inspection utility.

Example template:
```python
# scripts/preprocess_all.py
from pathlib import Path
from src.ai_doctor.stt import preprocess_audio
for p in Path("bulk_audio").glob("*.mp3"):
    out = p.with_suffix('.flac')
    preprocess_audio(str(p), str(out))
    print("Converted", p, "->", out)
```
