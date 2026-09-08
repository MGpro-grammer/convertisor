"""
Onglet « Créer un GIF » : conversion d'un extrait de vidéo YouTube.

Le déroulement diffère des onglets MP3 et MP4 : l'utilisateur doit
d'abord faire analyser la vidéo, ce qui en révèle le titre, la durée et
la miniature, puis désigner la plage à convertir. Sans cette étape,
aucune borne ne serait vérifiable.
"""

import threading
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core.config import DOWNLOADS_GIF
from core.constants import (
    BUTTON_HEIGHT_MD, FONT_SMALL_SIZE, PAD_ITEM, PAD_SECTION
)
from core.youtube import fetch_video_info
from gif.converter import convert_youtube_to_gif
from .base_download_tab import BaseDownloadTab
from .player_frame import PlayerFrame


class TabGif(BaseDownloadTab):
    """
    Onglet de conversion en GIF animé.

    Ajoute au socle commun un bouton d'analyse et un
    :class:`~ui.player_frame.PlayerFrame`, et vérifie la plage demandée
    avant de lancer le moindre téléchargement.
    """

    TITLE = "🎞 YouTube to GIF Converter"
    SUBTITLE = "Convertit un extrait de vidéo YouTube en GIF animé"
    BUTTON_TEXT = "Créer le GIF"
    SUCCESS_MESSAGE = "Le GIF a été créé !\n {path}"
    ACCENT_COLOR = "#8e44ad"
    ACCENT_HOVER_COLOR = "#71368a"
    DEFAULT_OUTPUT_DIR = DOWNLOADS_GIF

    #: Réglages relevés au moment du clic, transmis au thread de travail.
    #: Les widgets ne doivent pas être interrogés depuis un autre thread.
    _settings = None

    # ================================================================== #
    #  Interface propre à l'onglet                                       #
    # ================================================================== #

    def build_extra_options(self, row: int) -> int:
        """
        Insère le bouton d'analyse et le sélecteur de plage.

        :param row: Première ligne de grille disponible.
        :return: Première ligne encore libre.
        """
        self.analyze_btn = ctk.CTkButton(
            self,
            text="Analyser la vidéo",
            height=BUTTON_HEIGHT_MD,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            command=self._analyze,
        )
        self.analyze_btn.grid(row=row, column=0, pady=(0, PAD_ITEM), sticky="ew")
        row += 1

        self.player = PlayerFrame(self)
        self.player.grid(row=row, column=0, pady=(0, PAD_SECTION), sticky="ew")
        row += 1

        return row

    # ================================================================== #
    #  Analyse de la vidéo                                               #
    # ================================================================== #

    def _analyze(self):
        """Lance la récupération des métadonnées, sans bloquer la fenêtre."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Attention", "Colle une URL YouTube.")
            return

        self.analyze_btn.configure(state="disabled", text="Analyse en cours...")
        self.status_var.set("Analyse de la vidéo...")
        threading.Thread(
            target=self._analyze_task, args=(url,), daemon=True
        ).start()

    def _analyze_task(self, url: str):
        """Interroge YouTube depuis le thread de travail."""
        try:
            info = fetch_video_info(url)
        except Exception as exc:
            self.after(0, self._on_analyze_error, str(exc))
            return
        self.after(0, self._on_analyze_success, info)

    def _on_analyze_success(self, info):
        """Affiche la vidéo analysée et réactive le bouton."""
        self.analyze_btn.configure(state="normal", text="Analyser la vidéo")
        self.status_var.set("Vidéo analysée. Choisis la plage à convertir.")
        self.player.set_video_info(info)

    def _on_analyze_error(self, message: str):
        """Signale l'échec de l'analyse et remet l'onglet à zéro."""
        self.analyze_btn.configure(state="normal", text="Analyser la vidéo")
        self.status_var.set("L'analyse a échoué.")
        self.player.clear()
        messagebox.showerror(
            "Erreur", f"Impossible d'analyser cette vidéo :\n{message}"
        )

    # ================================================================== #
    #  Conversion                                                        #
    # ================================================================== #

    def _start_download(self):
        """
        Vérifie les réglages, puis délègue au socle commun.

        Cette lecture se fait sur le thread graphique, seul autorisé à
        interroger les widgets. Les valeurs relevées sont mises de côté
        pour :meth:`download`, qui s'exécutera ailleurs.
        """
        if self.player.video_info is None:
            messagebox.showwarning(
                "Attention", "Analyse d'abord la vidéo avant de créer le GIF."
            )
            return

        try:
            start, end = self.player.get_range()
        except ValueError as error:
            messagebox.showwarning("Plage invalide", str(error))
            return

        self._settings = (start, end, self.player.get_fps(), self.player.get_width())
        super()._start_download()

    def download(self, url: str, output_dir: Path) -> None:
        """
        Convertit l'extrait sélectionné en GIF.

        :param url: URL de la vidéo YouTube.
        :param output_dir: Dossier de destination.
        """
        start, end, fps, width = self._settings
        convert_youtube_to_gif(
            url,
            output_dir,
            start=start,
            end=end,
            fps=fps,
            width=width,
            on_progress=self._report_progress,
        )

    def _report_progress(self, message: str):
        """Affiche un message d'avancement, depuis le thread de travail."""
        self.after(0, self.status_var.set, message)