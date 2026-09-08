"""
Onglet « Fichiers » : liste et suppression des fichiers téléchargés.
"""

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core.config import DOWNLOADS_GIF, DOWNLOADS_MP3, DOWNLOADS_MP4
from core.constants import (
    BUTTON_HEIGHT_MD, BUTTON_WIDTH_MD,
    FONT_BODY_SIZE, FONT_SMALL_SIZE, FILE_ROW_HEIGHT, PAD_SECTION, PAD_ITEM
)


class TabFiles(ctk.CTkFrame):
    """
    Liste les fichiers produits par l'application et permet de les supprimer.

    La liste est reconstruite à chaque appel de :meth:`refresh`, appelé
    à l'ouverture et après chaque téléchargement réussi.
    """

    #: Extensions listées, associées à l'icône affichée devant le nom.
    FILE_ICONS = {
        ".mp3": "🎵",
        ".mp4": "🎬",
        ".gif": "🎞",
    }

    #: Dossiers parcourus. Les doublons sont éliminés au parcours,
    #: plusieurs formats pouvant partager un même dossier de sortie.
    SEARCH_DIRS = (DOWNLOADS_MP3, DOWNLOADS_MP4, DOWNLOADS_GIF)

    def __init__(self, parent, settings: dict):
        """
        :param parent: Conteneur parent, typiquement un onglet du CTkTabview.
        :param settings: Préférences utilisateur, lues pour ``confirm_delete``.
        """
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self._selected_file = None
        self._file_buttons = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()

    def _build(self):
        """Assemble la barre d'outils et la zone de liste défilante."""
        # Barre d'outils
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, pady=(PAD_SECTION, PAD_SECTION), sticky="ew")
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            toolbar,
            text="Actualiser",
            width=BUTTON_WIDTH_MD,
            height=BUTTON_HEIGHT_MD,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            command=self.refresh
        ).grid(row=0, column=0, padx=(0, PAD_SECTION))

        ctk.CTkLabel(
            toolbar,
            text="Fichiers téléchargés",
            font=ctk.CTkFont(size=FONT_BODY_SIZE, weight="bold")
        ).grid(row=0, column=1, sticky="w")

        self.delete_btn = ctk.CTkButton(
            toolbar,
            text="🗑 Supprimer",
            width=BUTTON_WIDTH_MD,
            height=BUTTON_HEIGHT_MD,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            state="disabled",
            command=self._delete_selected
        )
        self.delete_btn.grid(row=0, column=2)

        # Liste
        self.file_listbox = ctk.CTkScrollableFrame(self)
        self.file_listbox.grid(row=1, column=0, pady=(0, PAD_SECTION), sticky="nsew")
        self.file_listbox.grid_columnconfigure(0, weight=1)

        self.refresh()

    def _collect_files(self) -> list[Path]:
        """
        Rassemble les fichiers présents dans les dossiers surveillés.

        Les fichiers sont groupés par extension, dans l'ordre de
        :attr:`FILE_ICONS`, et triés par nom à l'intérieur de chaque groupe.

        :return: Liste des fichiers trouvés, éventuellement vide.
        """
        files: list[Path] = []
        # dict.fromkeys conserve l'ordre tout en supprimant les doublons.
        directories = list(dict.fromkeys(self.SEARCH_DIRS))
        for suffix in self.FILE_ICONS:
            for directory in directories:
                if directory.exists():
                    files.extend(sorted(directory.glob(f"*{suffix}")))
        return files

    def refresh(self):
        """Reconstruit entièrement la liste et annule la sélection en cours."""
        for widget in self.file_listbox.winfo_children():
            widget.destroy()
        self._file_buttons = []
        self._selected_file = None
        self.delete_btn.configure(state="disabled")

        all_files = self._collect_files()

        if not all_files:
            ctk.CTkLabel(
                self.file_listbox,
                text="Aucun fichier trouvé.",
                text_color="gray",
                font=ctk.CTkFont(size=FONT_SMALL_SIZE)
            ).grid(row=0, column=0, pady=20)
            return

        for i, f in enumerate(all_files):
            icon = self.FILE_ICONS.get(f.suffix, "📄")
            btn = ctk.CTkButton(
                self.file_listbox,
                text=f"{icon}  {f.name}",
                font=ctk.CTkFont(size=FONT_SMALL_SIZE),
                anchor="w",
                height=FILE_ROW_HEIGHT,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda file=f: self._select_file(file)
            )
            btn.grid(row=i, column=0, pady=PAD_ITEM, sticky="ew")
            self._file_buttons.append((btn, f))

    def _select_file(self, file: Path):
        """
        Sélectionne un fichier et active le bouton de suppression.

        :param file: Fichier correspondant au bouton cliqué.
        """
        self._selected_file = file
        self.delete_btn.configure(state="normal")
        for btn, f in self._file_buttons:
            btn.configure(
                fg_color=("gray75", "gray35") if f == file else "transparent"
            )

    def _delete_selected(self):
        """
        Supprime le fichier sélectionné, après confirmation si demandée.

        La confirmation dépend de la préférence ``confirm_delete``. La
        suppression est définitive : le fichier ne passe pas par la
        corbeille.
        """
        if not self._selected_file:
            return
        if self.settings.get("confirm_delete", True):
            if not messagebox.askyesno(
                "Confirmation",
                f"Supprimer ce fichier ?\n\n{self._selected_file.name}"
            ):
                return
        try:
            self._selected_file.unlink()
            self.refresh()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")