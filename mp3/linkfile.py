"""
Lecture d'un fichier texte contenant des liens YouTube.

Le fichier est analysé ligne par ligne. Chaque ligne doit contenir une
URL de vidéo YouTube ; les lignes vides et celles commençant par « # »
sont ignorées sans être signalées, ce qui permet de commenter une
liste.

Plutôt qu'une expression régulière couvrant toutes les formes d'URL de
YouTube, l'adresse est décomposée avec ``urllib.parse`` : c'est plus
lisible, et plus sûr face aux paramètres additionnels (« &t=42 ») ou
aux sous-domaines (« m. », « music. »).

Aucun accès réseau n'a lieu ici : une ligne retenue est syntaxiquement
valide, ce qui ne garantit pas que la vidéo existe.
"""

import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

#: Un identifiant de vidéo YouTube fait exactement onze caractères.
_VIDEO_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{11}")

#: Hôtes reconnus, une fois les sous-domaines retirés.
_YOUTUBE_HOSTS = ("youtube.com", "youtube-nocookie.com")

#: Sous-domaines sans incidence sur la nature du lien.
_IGNORED_SUBDOMAINS = ("www.", "m.", "music.")

#: Chemins qui portent l'identifiant juste après le préfixe.
_DIRECT_PATHS = ("/shorts/", "/embed/", "/live/", "/v/")

#: Préfixe marquant une ligne de commentaire.
COMMENT_PREFIX = "#"

#: Encodages essayés à la lecture, dans l'ordre. « utf-8-sig » absorbe
#: le BOM que PowerShell place en tête des fichiers qu'il produit.
_ENCODINGS = ("utf-8-sig", "cp1252")


@dataclass(frozen=True)
class DetectedLink:
    """
    Lien YouTube reconnu dans le fichier.

    :param line: Numéro de ligne, à partir de 1.
    :param url: Adresse telle qu'écrite dans le fichier.
    :param video_id: Identifiant de la vidéo, onze caractères.
    """

    line: int
    url: str
    video_id: str


@dataclass(frozen=True)
class InvalidLine:
    """
    Ligne qui n'a pas pu être interprétée comme un lien YouTube.

    :param line: Numéro de ligne, à partir de 1.
    :param content: Contenu de la ligne, espaces de bord retirés.
    """

    line: int
    content: str


@dataclass(frozen=True)
class LinkFileReport:
    """
    Résultat de l'analyse d'un fichier de liens.

    :param links: Liens retenus, dans l'ordre du fichier, sans doublon.
    :param failures: Lignes non reconnues.
    :param duplicates: Liens déjà rencontrés plus haut dans le fichier.
    """

    links: list[DetectedLink]
    failures: list[InvalidLine]
    duplicates: list[DetectedLink]

    @property
    def is_empty(self) -> bool:
        """Indique qu'aucun lien exploitable n'a été trouvé."""
        return not self.links


def extract_video_id(text: str) -> str | None:
    """
    Extrait l'identifiant de vidéo d'une adresse YouTube.

    Reconnaît les formes ``watch?v=``, ``youtu.be/``, ``shorts/``,
    ``embed/``, ``live/`` et ``v/``, avec ou sans protocole, et quels
    que soient les paramètres additionnels.

    :param text: Adresse à analyser.
    :return: L'identifiant à onze caractères, ou ``None`` si l'adresse
        n'est pas un lien de vidéo YouTube.
    """
    candidate = text.strip()
    if not candidate:
        return None

    # urlparse a besoin d'un protocole pour isoler correctement l'hôte.
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    try:
        parsed = urllib.parse.urlparse(candidate)
    except ValueError:
        return None

    host = parsed.netloc.lower()
    for subdomain in _IGNORED_SUBDOMAINS:
        host = host.removeprefix(subdomain)

    if host == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/", 1)[0]
    elif host in _YOUTUBE_HOSTS:
        video_id = _video_id_from_youtube_path(parsed)
    else:
        return None

    return video_id if _VIDEO_ID_PATTERN.fullmatch(video_id) else None


def _video_id_from_youtube_path(parsed: urllib.parse.ParseResult) -> str:
    """
    Retourne l'identifiant porté par une adresse « youtube.com ».

    :param parsed: Adresse déjà décomposée.
    :return: L'identifiant trouvé, ou une chaîne vide.
    """
    path = parsed.path

    if path == "/watch":
        values = urllib.parse.parse_qs(parsed.query).get("v")
        return values[0] if values else ""

    for prefix in _DIRECT_PATHS:
        if path.startswith(prefix):
            return path[len(prefix):].split("/", 1)[0]

    return ""


def _read_lines(path: Path) -> list[str]:
    """
    Lit le fichier en essayant plusieurs encodages.

    :param path: Fichier à lire.
    :return: Les lignes du fichier, sans caractère de fin de ligne.
    :raises ValueError: Si aucun encodage ne convient.
    :raises OSError: Si le fichier est illisible.
    """
    for encoding in _ENCODINGS:
        try:
            return path.read_text(encoding=encoding).splitlines()
        except UnicodeDecodeError:
            continue
    raise ValueError(
        "Impossible de lire ce fichier : son encodage n'est pas reconnu. "
        "Enregistre-le en UTF-8."
    )


def read_link_file(path: Path) -> LinkFileReport:
    """
    Analyse un fichier texte contenant un lien YouTube par ligne.

    Les lignes vides et les commentaires sont ignorés sans apparaître
    dans le rapport. Les lignes restantes sont soit retenues, soit
    signalées avec leur numéro, afin que l'utilisateur sache exactement
    quoi corriger.

    :param path: Fichier à analyser.
    :return: Le rapport d'analyse.
    :raises ValueError: Si l'encodage du fichier n'est pas reconnu.
    :raises OSError: Si le fichier est introuvable ou illisible.
    """
    links: list[DetectedLink] = []
    failures: list[InvalidLine] = []
    duplicates: list[DetectedLink] = []
    seen: set[str] = set()

    for number, raw_line in enumerate(_read_lines(path), start=1):
        content = raw_line.strip()
        if not content or content.startswith(COMMENT_PREFIX):
            continue

        video_id = extract_video_id(content)
        if video_id is None:
            failures.append(InvalidLine(line=number, content=content))
            continue

        detected = DetectedLink(line=number, url=content, video_id=video_id)
        if video_id in seen:
            duplicates.append(detected)
        else:
            seen.add(video_id)
            links.append(detected)

    return LinkFileReport(links=links, failures=failures, duplicates=duplicates)