"""
Onglet « Convertir MP3 » : téléchargement de l'audio d'une vidéo YouTube.
"""

from pathlib import Path

from core.config import DOWNLOADS_MP3
from mp3.downloader import download_audio_as_mp3
from .base_download_tab import BaseDownloadTab


class TabConvert(BaseDownloadTab):
    """Onglet de téléchargement au format MP3."""

    TITLE = "🎵 YouTube to MP3 Converter"
    SUBTITLE = "Télécharge l'audio d'une vidéo YouTube en MP3"
    BUTTON_TEXT = "Télécharger MP3"
    SUCCESS_MESSAGE = "Le fichier MP3 a été téléchargé !\n {path}"
    DEFAULT_OUTPUT_DIR = DOWNLOADS_MP3

    def download(self, url: str, output_dir: Path) -> None:
        """Télécharge l'audio de la vidéo et l'encode en MP3."""
        download_audio_as_mp3(url, output_dir)