"""
Pytest konfiguracija — mock config.json pre importa.
"""
import json
import sys
from pathlib import Path

import pytest

# Dodaj root folder u path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Napravi testni config.json ako ne postoji
CONFIG_FILE = ROOT / "config.json"
if not CONFIG_FILE.exists():
    CONFIG_FILE.write_text(
        json.dumps({
            "ollama": {
                "url": "http://127.0.0.1:11434",
                "model": "llama3.2:latest",
                "timeout": 120,
                "system_prompt": "Ti si DrazenAI, test.",
            }
        }, indent=2),
        encoding="utf-8",
    )
