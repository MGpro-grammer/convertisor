from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DOWNLOADS_MP3 = BASE_DIR / "downloads" / "mp3"
DOWNLOADS_MP4 = BASE_DIR / "downloads" / "mp4"
SETTINGS_FILE = BASE_DIR / "settings.json"
VERSION_FILE = BASE_DIR / "version.txt"