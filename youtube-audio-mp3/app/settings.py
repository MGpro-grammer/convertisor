import json
from .config import SETTINGS_FILE

DEFAULTS = {
    "confirm_delete": True,  # Confirmation avant suppression
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
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)