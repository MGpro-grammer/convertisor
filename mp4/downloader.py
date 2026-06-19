from pathlib import Path

from yt_dlp import YoutubeDL


def download_video_as_mp4(url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
    }
    with YoutubeDL(options) as ydl:
        ydl.download([url])