"""
Interrogation des métadonnées d'une vidéo YouTube.

yt-dlp sait décrire une vidéo sans en télécharger le contenu : titre,
durée et miniature sont obtenus en une seule requête. L'onglet GIF s'en
sert pour valider la plage saisie avant de lancer quoi que ce soit.
"""

from dataclasses import dataclass

from yt_dlp import YoutubeDL

from core.ytdlp import base_options


@dataclass(frozen=True)
class VideoInfo:
    """
    Description d'une vidéo YouTube, sans son contenu.

    :param title: Titre de la vidéo.
    :param duration: Durée totale, en secondes.
    :param thumbnail_url: Adresse de la miniature, ou chaîne vide.
    """

    title: str
    duration: float
    thumbnail_url: str


def fetch_video_info(url: str) -> VideoInfo:
    """
    Récupère les métadonnées d'une vidéo sans la télécharger.

    :param url: URL de la vidéo YouTube.
    :return: Les métadonnées de la vidéo.
    :raises ValueError: La vidéo n'expose pas de durée exploitable,
        ce qui est le cas des diffusions en direct.
    :raises yt_dlp.utils.DownloadError: URL invalide, vidéo
        indisponible, ou absence de connexion réseau.
    """
    options = {
        **base_options(),
        "skip_download": True,
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    duration = info.get("duration")
    if not duration:
        raise ValueError(
            "Cette vidéo n'expose pas de durée : "
            "s'agit-il d'une diffusion en direct ?"
        )

    return VideoInfo(
        title=info.get("title") or "Sans titre",
        duration=float(duration),
        thumbnail_url=info.get("thumbnail") or "",
    )