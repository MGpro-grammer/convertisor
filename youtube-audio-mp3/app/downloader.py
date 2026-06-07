from yt_dlp import YoutubeDL
from .config import YDL_OPTIONS

def download_audio_as_mp3(url : str) -> None:
    """Downloads audio from a YouTube video and saves it as an MP3 file."""

    if not url.strip():
        raise ValueError("L'URL ne peut pas être vide.")

    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            raise RuntimeError(f"Erreur lors du téléchargement : {e}")
