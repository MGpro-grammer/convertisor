import os
from pathlib import Path

import imageio_ffmpeg
from yt_dlp import YoutubeDL


def _get_ffmepg_path() -> str:
    return os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())


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
        "ffmpeg_location": _get_ffmepg_path(),
    }
    with YoutubeDL(options) as ydl:
        ydl.download([url])