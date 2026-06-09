import sys
import os
import subprocess
import threading
import urllib.request
import json
from pathlib import Path

GITHUB_USER = "MGpro-grammer"
GITHUB_REPO = "convertisor"
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

def get_current_version() -> str:
    """Reads the current version from the version.txt file."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    version_file = base / "version.txt"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0.0"

def check_for_update() -> dict | None:
    """
    Return a dict {"version": "x.x.x", "download_url": "..."}
    if an update is available, otherwise None.
    """
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": "Convertisor-App"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())

        latest_version = data["tag_name"].lstrip("v")
        current_version = get_current_version()

        if latest_version != current_version:
            # Search for the .exe asset in the release assets
            download_url = None
            for asset in data.get("assets", []):
                if asset["name"].endswith(".exe"):
                    download_url = asset["browser_download_url"]
                    break

            if download_url:
                return {"version": latest_version, "download_url": download_url}

    except Exception :
        pass  # Silently ignore errors (e.g., network issues)

    return None

def download_and_install(download_url: str, on_progress, on_done, on_error):
    """Downloads the setup and run in a separate thread."""
    def task():
        try:
            if getattr(sys, "frozen", False):
                tmp_dir = Path(sys.executable).parent
            else:
                tmp_dir = Path(__file__).resolve().parent.parent

            installer_path = tmp_dir / "Convertisor-Setup.exe"
            on_progress("Téléchargement en cours...")

            urllib.request.urlretrieve(download_url, installer_path)

            on_progress("Lancement du l'installateur...")
            subprocess.Popen([str(installer_path)])
            on_done()

        except Exception as exc:
            on_error(str(exc))

    threading.Thread(target=task, daemon=True).start()