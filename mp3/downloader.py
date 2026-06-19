from pathlib import Path

from yt_dlp import YoutubeDL


def download_audio_as_mp3(url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
    }
    with YoutubeDL(options) as ydl:
        ydl.download([url])