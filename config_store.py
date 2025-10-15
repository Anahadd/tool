"""Persistent configuration storage for web app"""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".tool_google"
CONFIG_FILE = CONFIG_DIR / "web_config.json"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_config(key: str, value: str):
    config = load_all_config()
    config[key] = value
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    os.environ[key] = value

def load_config(key: str, default: str = "") -> str:
    env_val = os.getenv(key)
    if env_val:
        return env_val
    config = load_all_config()
    return config.get(key, default)

def load_all_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except:
        return {}

for key, value in load_all_config().items():
    os.environ[key] = value

