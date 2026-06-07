from pathlib import Path
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
    "noplaylist": True,
    "ffmpeg_location": FFMPEG_PATH,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}