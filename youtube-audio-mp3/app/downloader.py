from pathlib import Path
from yt_dlp import YoutubeDL
from .config import YDL_BASE_OPTIONS

def download_audio_as_mp3(url : str, output_dir: Path) -> None:
    """Downloads audio from a YouTube video and saves it as an MP3 file."""

    if not url.strip():
        raise ValueError("L'URL ne peut pas être vide.")

    output_dir.mkdir(parents=True, exist_ok=True)

    options = {
        **YDL_BASE_OPTIONS,
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
    }

    with YoutubeDL(options) as ydl:
        ydl.download([url])
