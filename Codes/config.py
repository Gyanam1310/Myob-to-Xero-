# config.py  (save in the same folder as config.json)
import json
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"

# Load once at import time
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    _CFG = json.load(f)

def get_file(key: str) -> str:
    """
    Return an absolute path for the file mapped to *key* in config.json.
    Raise KeyError if the key is missing.
    """
    try:
        value = _CFG["files"][key]
    except KeyError:
        raise KeyError(f"Key '{key}' not found in config.json['files']")

    p = Path(value)
    if not p.is_absolute():
        p = BASE_DIR / p      # make relative paths project‑local
    return p
