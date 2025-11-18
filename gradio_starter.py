import os
from pathlib import Path

env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
	for line in env_path.read_text(encoding="utf-8").splitlines():
		line = line.strip()
		if not line or line.startswith("#"):
			continue
		if "=" in line:
			key, val = line.split("=", 1)
			os.environ.setdefault(key.strip(), val.strip())

from src.ai_doctor import create_app

demo = create_app()
demo.launch(debug=True)