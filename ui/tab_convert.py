"""
Onglet « Convertir MP3 » : téléchargement de l'audio de vidéos YouTube.

L'onglet fonctionne dans deux modes, choisis par un interrupteur. En
mode simple, il télécharge l'unique lien saisi. En mode liste, il lit
un fichier texte contenant un lien par ligne, en rend compte — nombre
de liens reconnus, numéros des lignes qui ne l'ont pas été — puis
télécharge la série, un titre après l'autre.
"""

import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.config import DOWNLOADS_MP3
from core.constants import (
    BUTTON_HEIGHT_MD, BUTTON_WIDTH_MD, BUTTON_WIDTH_SM,
    FONT_SMALL_SIZE, PAD_ITEM, PAD_SECTION, SUCCESS_RESET_DELAY
)
from mp3.batch import BatchResult, download_links_as_mp3
from mp3.downloader import download_audio_as_mp3
from mp3.linkfile import LinkFileReport, read_link_file
from .base_download_tab import BaseDownloadTab


class TabConvert(BaseDownloadTab):
    """
    Onglet de téléchargement au format MP3, à l'unité ou par liste.

    Le mode liste réutilise le socle commun : seule la nature du
    travail change, pas la mécanique de verrouillage de l'interface ni
    la gestion du thread.
    """

    TITLE = "🎵 YouTube to MP3 Converter"
    SUBTITLE = "Télécharge l'audio d'une ou plusieurs vidéos YouTube en MP3"
    BUTTON_TEXT = "Télécharger MP3"
    SUCCESS_MESSAGE = "Le fichier MP3 a été téléchargé !\n {path}"
    DEFAULT_OUTPUT_DIR = DOWNLOADS_MP3

    #: Libellé du bouton principal lorsque le mode liste est actif.
    BATCH_BUTTON_TEXT = "Télécharger la liste"

    #: Nombre maximal de numéros de ligne détaillés dans un message ;
    #: au-delà, seul le total est indiqué.
    MAX_LISTED_LINES = 12

    def __init__(self, parent, status_var: ctk.StringVar):
        """
        :param parent: Conteneur parent, typiquement un onglet du CTkTabview.
        :param status_var: Variable de statut partagée avec la fenêtre.
        """
        # Ces attributs doivent exister avant super().__init__(), qui
        # construit l'interface et appelle donc build_extra_options().
        self._report: LinkFileReport | None = None
        self._stop_event = threading.Event()
        super().__init__(parent, status_var)

    # ================================================================== #
    #  Mode simple                                                       #
    # ================================================================== #

    def download(self, url: str, output_dir: Path) -> None:
        """Télécharge l'audio d'une vidéo et l'encode en MP3."""
        download_audio_as_mp3(url, output_dir)

    # ================================================================== #
    #  Construction du mode liste                                        #
    # ================================================================== #

    def build_extra_options(self, row: int) -> int:
        """
        Insère l'interrupteur de mode et le cadre du mode liste.

        Le cadre est construit puis retiré de la grille : il garde sa
        position et reparaît d'un simple ``grid()`` quand l'utilisateur
        bascule l'interrupteur.

        :param row: Première ligne de grille disponible.
        :return: Première ligne encore libre.
        """
        self.batch_var = ctk.BooleanVar(value=False)
        self.batch_switch = ctk.CTkSwitch(
            self,
            text="Plusieurs liens (fichier .txt)",
            variable=self.batch_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
        )
        self.batch_switch.grid(row=row, column=0, pady=(0, PAD_ITEM), sticky="w")
        row += 1

        self.batch_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.batch_frame.grid(
            row=row, column=0, pady=(0, PAD_SECTION), sticky="ew"
        )
        self.batch_frame.grid_columnconfigure(1, weight=1)
        row += 1

        self.choose_btn = ctk.CTkButton(
            self.batch_frame,
            text="Choisir le fichier...",
            width=BUTTON_WIDTH_MD,
            height=BUTTON_HEIGHT_MD,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            command=self._choose_link_file,
        )
        self.choose_btn.grid(row=0, column=0, padx=(0, PAD_SECTION))

        self.file_var = ctk.StringVar(value="Aucun fichier choisi.")
        ctk.CTkLabel(
            self.batch_frame,
            textvariable=self.file_var,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew")

        self.cancel_btn = ctk.CTkButton(
            self.batch_frame,
            text="Annuler",
            width=BUTTON_WIDTH_SM,
            height=BUTTON_HEIGHT_MD,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            state="disabled",
            command=self._request_stop,
        )
        self.cancel_btn.grid(row=0, column=2, padx=(PAD_SECTION, 0))

        self.summary_var = ctk.StringVar(value="")
        self.summary_label = ctk.CTkLabel(
            self.batch_frame,
            textvariable=self.summary_var,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            text_color="gray",
            anchor="w",
            justify="left",
            wraplength=480,
        )
        self.summary_label.grid(
            row=1, column=0, columnspan=3, pady=(PAD_ITEM, 0), sticky="w"
        )

        self.batch_frame.grid_remove()
        return row

    def _on_mode_change(self):
        """Affiche ou masque le mode liste, et adapte le reste de l'onglet."""
        if self.batch_var.get():
            self.batch_frame.grid()
            self.url_entry.configure(state="disabled")
            self.btn.configure(text=self.BATCH_BUTTON_TEXT)
        else:
            self.batch_frame.grid_remove()
            self.url_entry.configure(state="normal")
            self.btn.configure(text=self.BUTTON_TEXT)

    # ================================================================== #
    #  Lecture du fichier de liens                                       #
    # ================================================================== #

    def _choose_link_file(self):
        """Ouvre le sélecteur de fichier et analyse le fichier retenu."""
        path = filedialog.askopenfilename(
            title="Choisir un fichier de liens",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
        )
        if path:
            self._analyze_link_file(Path(path))

    def _analyze_link_file(self, path: Path):
        """
        Analyse le fichier choisi et affiche le compte rendu.

        :param path: Fichier de liens sélectionné par l'utilisateur.
        """
        try:
            report = read_link_file(path)
        except (OSError, ValueError) as error:
            self._report = None
            self.file_var.set("Aucun fichier choisi.")
            self.summary_var.set("")
            messagebox.showerror(
                "Erreur", f"Impossible de lire ce fichier :\n{error}"
            )
            return

        self._report = report
        self.file_var.set(path.name)
        self.summary_var.set(self._format_report(report))
        self.summary_label.configure(
            text_color="gray" if report.links else ("#c0392b", "#e74c3c")
        )

    def _format_report(self, report: LinkFileReport) -> str:
        """
        Met en phrase le résultat de l'analyse.

        Les numéros des lignes non reconnues sont donnés explicitement :
        c'est ce qui permet à l'utilisateur de corriger son fichier sans
        le relire en entier.

        :param report: Rapport d'analyse.
        :return: Le compte rendu, sur une ou deux phrases.
        """
        if report.is_empty and not report.failures:
            return "Ce fichier ne contient aucun lien."

        parts = [f"{len(report.links)} lien(s) YouTube détecté(s)."]

        if report.duplicates:
            parts.append(f"{len(report.duplicates)} doublon(s) ignoré(s).")

        if report.failures:
            numbers = [str(failure.line) for failure in report.failures]
            shown = ", ".join(numbers[:self.MAX_LISTED_LINES])
            if len(numbers) > self.MAX_LISTED_LINES:
                shown += f", … (+{len(numbers) - self.MAX_LISTED_LINES})"
            parts.append(f"{len(numbers)} ligne(s) non reconnue(s) : {shown}.")

        return " ".join(parts)

    # ================================================================== #
    #  Téléchargement de la liste                                        #
    # ================================================================== #

    def _prepare_progress(self):
        """Choisit une barre chiffrée en mode liste, animée sinon."""
        if self.batch_var.get():
            self.progress.configure(mode="determinate")
            self.progress.set(0)
        else:
            super()._prepare_progress()

    def _start_download(self):
        """Aiguille vers le téléchargement simple ou le téléchargement en lot."""
        if not self.batch_var.get():
            super()._start_download()
            return

        if self._report is None:
            messagebox.showwarning(
                "Attention", "Choisis d'abord un fichier de liens."
            )
            return

        if self._report.is_empty:
            messagebox.showwarning(
                "Attention", "Ce fichier ne contient aucun lien exploitable."
            )
            return

        self._stop_event.clear()
        self.cancel_btn.configure(state="normal")
        self.choose_btn.configure(state="disabled")
        self.batch_switch.configure(state="disabled")
        self.status_var.set(
            f"Téléchargement de {len(self._report.links)} vidéo(s)..."
        )
        self._begin(self._batch_task, self._report.links, self.output_dir)

    def _batch_task(self, links, output_dir: Path):
        """Déroule le lot dans le thread de travail."""
        result = download_links_as_mp3(
            links,
            output_dir,
            on_progress=self._on_item_started,
            should_stop=self._stop_event.is_set,
        )
        self.after(0, self._on_batch_finished, result)

    def _on_item_started(self, index: int, total: int, link):
        """Relaie l'avancement vers le thread graphique."""
        self.after(0, self._show_item_progress, index, total)

    def _show_item_progress(self, index: int, total: int):
        """
        Affiche le rang du lien en cours.

        La barre indique la proportion déjà terminée, soit ``index - 1``
        titres sur le total : le lien annoncé commence tout juste.
        """
        self.status_var.set(f"Téléchargement {index}/{total}...")
        self.progress.set((index - 1) / total)

    def _request_stop(self):
        """Demande l'arrêt du lot après le téléchargement en cours."""
        self._stop_event.set()
        self.cancel_btn.configure(state="disabled")
        self.status_var.set("Arrêt après le téléchargement en cours...")

    def _on_batch_finished(self, result: BatchResult):
        """
        Rend l'interface et présente le bilan du lot.

        :param result: Bilan renvoyé par
            :func:`mp3.batch.download_links_as_mp3`.
        """
        self.progress.configure(mode="determinate")
        self.progress.set(0 if result.stopped else 1)
        self.btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.choose_btn.configure(state="normal")
        self.batch_switch.configure(state="normal")

        if self.on_download_success:
            self.on_download_success()

        self.status_var.set(
            f"{len(result.succeeded)} fichier(s) téléchargé(s)."
        )
        self._show_batch_summary(result)
        self.after(SUCCESS_RESET_DELAY, lambda: self.progress.set(0))

    def _show_batch_summary(self, result: BatchResult):
        """
        Affiche le bilan détaillé dans une fenêtre.

        Chaque échec est rattaché à son numéro de ligne d'origine, afin
        que l'utilisateur retrouve le lien fautif dans son fichier.
        """
        lines = [f"{len(result.succeeded)} fichier(s) téléchargé(s) dans :",
                 str(self.output_dir)]

        if result.failed:
            lines.append("")
            lines.append(f"{len(result.failed)} échec(s) :")
            for failure in result.failed[:self.MAX_LISTED_LINES]:
                lines.append(f"  ligne {failure.link.line} : {failure.reason}")
            remaining = len(result.failed) - self.MAX_LISTED_LINES
            if remaining > 0:
                lines.append(f"  … et {remaining} autre(s).")

        if result.stopped:
            lines.append("")
            lines.append("Lot interrompu : les liens restants n'ont pas été traités.")

        message = "\n".join(lines)
        if result.failed or result.stopped:
            messagebox.showwarning("Lot terminé", message)
        else:
            messagebox.showinfo("Lot terminé", message)