from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_MP3 = DOWNLOADS_DIR
DOWNLOADS_MP4 = DOWNLOADS_DIR
SETTINGS_FILE = BASE_DIR / "settings.json"
VERSION_FILE = BASE_DIR / "version.txt"