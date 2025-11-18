from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from src.ai_doctor import create_app

def _mask(v: str | None) -> str:
	if not v:
		return "<missing>"
	if len(v) <= 12:
		return v
	return v[:8] + "..." + v[-4:]

env_path = Path(__file__).resolve().parents[1] / ".env"
loaded = False
if env_path.exists():
	load_dotenv(dotenv_path=str(env_path), override=True)
	loaded = True
else:
	alt = find_dotenv()
	if alt:
		load_dotenv(alt, override=True)
		loaded = True


demo = create_app()
demo.launch(debug=True)