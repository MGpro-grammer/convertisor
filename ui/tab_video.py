"""
Onglet « Convertir MP4 » : téléchargement d'une vidéo YouTube.
"""

from pathlib import Path

from core.config import DOWNLOADS_MP4
from mp4.downloader import download_video_as_mp4
from .base_download_tab import BaseDownloadTab


class TabVideo(BaseDownloadTab):
    """Onglet de téléchargement au format MP4."""

    TITLE = "🎬 YouTube to MP4 Converter"
    SUBTITLE = "Télécharge une vidéo YouTube en MP4 (meilleure qualité)"
    BUTTON_TEXT = "Télécharger MP4"
    SUCCESS_MESSAGE = "La vidéo MP4 a été téléchargée !\n {path}"
    ACCENT_COLOR = "#c0392b"
    ACCENT_HOVER_COLOR = "#962d22"
    DEFAULT_OUTPUT_DIR = DOWNLOADS_MP4

    def download(self, url: str, output_dir: Path) -> None:
        """Télécharge la vidéo au format MP4."""
        download_video_as_mp4(url, output_dir)