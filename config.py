import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = ROOT / "config.json"

CFG = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

def save():
    CONFIG_FILE.write_text(json.dumps(CFG, indent=2, ensure_ascii=False), encoding="utf-8")
