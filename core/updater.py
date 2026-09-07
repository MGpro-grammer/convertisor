"""
Vérification et installation des mises à jour de l'application.

Les mises à jour sont publiées comme « releases » du dépôt GitHub du
projet. Le module interroge l'API GitHub, compare la version publiée à
la version locale, puis télécharge et lance l'installateur.
"""

import json
import re
import subprocess
import tempfile
import threading
import urllib.request
from pathlib import Path

from core.config import VERSION_FILE

#—— Dépôt de référence ————————————————————————————————————————————————————————————
GITHUB_USER = "MGpro-grammer"
GITHUB_REPO = "convertisor"
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

# Tout installateur téléchargé doit provenir de cette adresse : l'URL
# fournie par l'API n'est pas exécutée sans cette vérification.
RELEASE_URL_PREFIX = (
    f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/download/"
)

#—— Délai réseau (secondes) ———————————————————————————————————————————————————————
REQUEST_TIMEOUT = 5


def get_current_version() -> str:
    """
    Retourne la version courante de l'application.

    La version est lue depuis le fichier version.txt embarqué
    (voir ``core.config.VERSION_FILE``). Retourne "0.0.0" si le
    fichier est absent ou illisible.
    """
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        pass
    return "0.0.0"


def _version_tuple(version: str) -> tuple[int, ...]:
    """
    Convertit une version « x.y.z » en tuple d'entiers comparable.

    Le préfixe « v » éventuel est retiré et la lecture s'arrête au
    premier composant non numérique, ce qui rend la conversion robuste
    aux suffixes de pré-version (« 2.1.0-beta » donne (2, 1, 0)).

    :param version: Version sous forme de chaîne.
    :return: Tuple d'entiers, vide si aucun composant n'est lisible.
    """
    parts: list[int] = []
    for chunk in version.strip().lstrip("vV").split("."):
        match = re.match(r"\d+", chunk)
        if not match:
            break
        parts.append(int(match.group()))
    return tuple(parts)


def is_newer(candidate: str, current: str) -> bool:
    """
    Indique si ``candidate`` est strictement postérieure à ``current``.

    Retourne False si l'une des deux versions est illisible : sans
    certitude, aucune mise à jour n'est proposée.

    :param candidate: Version publiée sur GitHub.
    :param current: Version installée localement.
    """
    candidate_parts = _version_tuple(candidate)
    current_parts = _version_tuple(current)
    if not candidate_parts or not current_parts:
        return False
    return candidate_parts > current_parts


def check_for_update() -> dict | None:
    """
    Interroge GitHub et retourne la mise à jour disponible, s'il y en a une.

    :return: ``{"version": "x.y.z", "download_url": "..."}`` si une
        version strictement plus récente est publiée et qu'un
        installateur .exe légitime y est attaché, sinon ``None``.
    """
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": "Convertisor-App"}
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read())

        latest_version = data["tag_name"].lstrip("v")

        if not is_newer(latest_version, get_current_version()):
            return None

        # Recherche de l'installateur parmi les fichiers joints à la release.
        for asset in data.get("assets", []):
            url = asset.get("browser_download_url", "")
            if asset.get("name", "").endswith(".exe") and url.startswith(RELEASE_URL_PREFIX):
                return {"version": latest_version, "download_url": url}

    except Exception:
        # Absence de réseau, API indisponible, réponse inattendue :
        # la vérification est silencieuse, elle ne doit jamais
        # interrompre le démarrage de l'application.
        pass

    return None


def download_and_install(download_url: str, on_progress, on_done, on_error):
    """
    Télécharge l'installateur et le lance, dans un thread séparé.

    L'interface reste réactive pendant l'opération. Les trois callbacks
    sont appelés depuis ce thread : l'appelant est responsable de les
    replanifier sur le thread graphique.

    :param download_url: URL de l'installateur, validée par
        :func:`check_for_update`.
    :param on_progress: Appelé avec un message d'avancement (str).
    :param on_done: Appelé sans argument une fois l'installateur lancé.
    :param on_error: Appelé avec le message d'erreur (str) en cas d'échec.
    """

    def task():
        try:
            if not download_url.startswith(RELEASE_URL_PREFIX):
                raise ValueError("Origine du téléchargement non reconnue.")

            installer_path = Path(tempfile.gettempdir()) / "Convertisor-Setup.exe"
            on_progress("Téléchargement en cours...")

            urllib.request.urlretrieve(download_url, installer_path)

            on_progress("Lancement de l'installateur...")
            subprocess.Popen([str(installer_path)])
            on_done()

        except Exception as exc:
            on_error(str(exc))

    threading.Thread(target=task, daemon=True).start()