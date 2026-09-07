"""
Téléchargement d'une vidéo YouTube au format MP4.
"""

from pathlib import Path

from yt_dlp import YoutubeDL

from core.ffmpeg import get_ffmpeg_path


def download_video_as_mp4(url: str, output_dir: Path) -> None:
    """
    Télécharge une vidéo YouTube en MP4, à la meilleure qualité.

    yt-dlp récupère séparément le meilleur flux vidéo et le meilleur
    flux audio, puis FFmpeg les fusionne en un unique fichier MP4.

    :param url: URL de la vidéo YouTube.
    :param output_dir: Dossier de destination, créé s'il n'existe pas.
    :raises yt_dlp.utils.DownloadError: URL invalide, vidéo
        indisponible, ou absence de connexion réseau.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "ffmpeg_location": get_ffmpeg_path(),
    }
    with YoutubeDL(options) as ydl:
        ydl.download([url])