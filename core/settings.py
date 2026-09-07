"""
Lecture et écriture des préférences utilisateur.

Les préférences sont stockées en JSON dans un fichier dont
l'emplacement dépend du mode d'exécution (voir
``core.config.SETTINGS_FILE``). Un fichier absent ou illisible n'est
jamais une erreur : les valeurs par défaut prennent alors le relais.
"""

import json

from core.config import SETTINGS_FILE
from core.constants import DEFAULT_APPEARANCE

DEFAULTS = {
    "confirm_delete": True,  # Confirmation avant suppression
    "appearance_mode": DEFAULT_APPEARANCE,
}

def load_settings() -> dict:
    """Charge les paramètres depuis settings.json."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Fusionne avec les défauts pour les nouvelles clés futures
                return {**DEFAULTS, **data}
        except Exception:
            pass
    return DEFAULTS.copy()

def save_settings(settings: dict) -> None:
    """Sauvegarde les paramètres dans settings.json."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)