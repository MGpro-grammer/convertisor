import sys
from pathlib import Path
import imageio_ffmpeg

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

YDL_BASE_OPTIONS = {
    "format": "bestaudio/best",
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