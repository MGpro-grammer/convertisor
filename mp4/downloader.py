from pathlib import Path

import imageio_ffmpeg
from yt_dlp import YoutubeDL


def _get_ffmepg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()

def download_video_as_mp4(url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "ffmpeg_location": _get_ffmepg_path(),
    }
    with YoutubeDL(options) as ydl:
        ydl.download([url])