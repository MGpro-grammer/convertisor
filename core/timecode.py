"""
Conversion entre secondes et codes temporels lisibles.

Les formats acceptés en entrée sont « ss », « mm:ss » et « hh:mm:ss ».
La sortie omet les heures tant que la durée reste inférieure à une heure.
"""


def parse_timecode(text: str) -> float:
    """
    Convertit un code temporel saisi par l'utilisateur en secondes.

    Accepte « 92 », « 1:32 » et « 0:01:32 », qui valent tous 92 secondes.

    :param text: Code temporel saisi.
    :return: Durée correspondante en secondes.
    :raises ValueError: Format non reconnu, valeur négative, ou
        minutes/secondes supérieures à 59.
    """
    parts = text.strip().split(":")
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"Format de temps non reconnu : « {text} »")

    try:
        values = [int(part) for part in parts]
    except ValueError:
        raise ValueError(f"Format de temps non reconnu : « {text} »") from None

    if any(value < 0 for value in values):
        raise ValueError("Un temps ne peut pas être négatif.")

    # Seul le premier champ peut dépasser 59 : « 90:00 » vaut 90 minutes.
    if len(values) > 1 and any(value > 59 for value in values[1:]):
        raise ValueError("Les minutes et les secondes doivent rester sous 60.")

    seconds = 0.0
    for value in values:
        seconds = seconds * 60 + value
    return seconds


def format_timecode(seconds: float) -> str:
    """
    Formate une durée en « mm:ss », ou « hh:mm:ss » au-delà d'une heure.

    :param seconds: Durée en secondes, arrondie à la seconde la plus proche.
    :return: Code temporel lisible.
    """
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"