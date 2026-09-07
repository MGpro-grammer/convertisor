"""
Emplacements de fichiers de l'application Convertisor.

Ce module est la source unique de vérité pour tous les chemins. Il
distingue trois emplacements, car ils n'ont pas les mêmes contraintes
selon que l'application tourne depuis les sources ou depuis
l'exécutable produit par PyInstaller.

RESOURCE_DIR
    Ressources embarquées, en lecture seule (version.txt). En mode
    exécutable « onefile », PyInstaller extrait ces fichiers dans un
    dossier temporaire exposé par ``sys._MEIPASS``, supprimé à la
    fermeture de l'application.

USER_DATA_DIR
    Données inscriptibles et persistantes (settings.json). En mode
    exécutable, l'application est installée dans Program Files, dossier
    non inscriptible sans élévation de privilèges : les données vont
    donc dans %APPDATA%\\Convertisor.

DOWNLOADS_DIR
    Fichiers produits par l'utilisateur. En mode exécutable, un
    sous-dossier Convertisor du dossier Téléchargements de l'utilisateur.

En mode développement, les trois pointent vers la racine du projet (ou
son sous-dossier downloads/), ce qui conserve le comportement actuel.
"""

import os
import sys
from pathlib import Path

#—— Identité de l'application —————————————————————————————————————————————————————
APP_NAME = "Convertisor"

#—— Mode d'exécution ——————————————————————————————————————————————————————————————
IS_FROZEN: bool = getattr(sys, "frozen", False)

#—— Racine du projet (mode développement) —————————————————————————————————————————
BASE_DIR = Path(__file__).resolve().parent.parent


def _resource_dir() -> Path:
    """Retourne le dossier des ressources embarquées, en lecture seule."""
    if not IS_FROZEN:
        return BASE_DIR
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(sys.executable).resolve().parent


def _user_data_dir() -> Path:
    """Retourne le dossier de données utilisateur, inscriptible et persistant."""
    if not IS_FROZEN:
        return BASE_DIR
    appdata = os.environ.get("APPDATA")
    root = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return root / APP_NAME


def _downloads_dir() -> Path:
    """
    Retourne le dossier de sortie des fichiers téléchargés.

    En mode exécutable, utilise le dossier Téléchargements de
    l'utilisateur s'il existe, sinon se rabat sur USER_DATA_DIR.
    """
    if not IS_FROZEN:
        return BASE_DIR / "downloads"
    user_downloads = Path.home() / "Downloads"
    if user_downloads.is_dir():
        return user_downloads / APP_NAME
    return USER_DATA_DIR / "downloads"


#—— Dossiers ——————————————————————————————————————————————————————————————————————
RESOURCE_DIR = _resource_dir()
USER_DATA_DIR = _user_data_dir()
DOWNLOADS_DIR = _downloads_dir()

#—— Dossiers de sortie par format —————————————————————————————————————————————————
DOWNLOADS_MP3 = DOWNLOADS_DIR
DOWNLOADS_MP4 = DOWNLOADS_DIR
DOWNLOADS_GIF = DOWNLOADS_DIR

#—— Fichiers ——————————————————————————————————————————————————————————————————————
SETTINGS_FILE = USER_DATA_DIR / "settings.json"
VERSION_FILE = RESOURCE_DIR / "version.txt"