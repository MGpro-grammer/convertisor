"""
Téléchargement de la piste audio d'une vidéo YouTube au format MP3.
"""

from pathlib import Path

from yt_dlp import YoutubeDL

from core.ytdlp import base_options


def download_audio_as_mp3(url: str, output_dir: Path) -> None:
    """
    Télécharge l'audio d'une vidéo YouTube et l'encode en MP3 192 kbit/s.

    Le nom du fichier produit est le titre de la vidéo. Un fichier
    portant déjà ce nom est écrasé par yt-dlp.

    :param url: URL de la vidéo YouTube.
    :param output_dir: Dossier de destination, créé s'il n'existe pas.
    :raises yt_dlp.utils.DownloadError: URL invalide, vidéo
        indisponible, ou absence de connexion réseau.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        **base_options(),
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
    with YoutubeDL(options) as ydl:
        ydl.download([url])