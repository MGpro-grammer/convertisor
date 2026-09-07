"""
Socle commun aux onglets de téléchargement.

Les onglets MP3, MP4 et GIF partagent la même structure : un champ
d'URL, un sélecteur de dossier, un bouton, une barre de progression et
une ligne de statut. Seuls changent les libellés, la couleur d'accent,
le dossier par défaut et la fonction de téléchargement appelée.

Une sous-classe se limite donc à quelques attributs de classe et à
l'implémentation de :meth:`BaseDownloadTab.download`.
"""

import threading
from pathlib import Path
from tkinter import messagebox, filedialog

import customtkinter as ctk

from core.constants import (
    ENTRY_HEIGHT, BUTTON_HEIGHT_LG, BUTTON_WIDTH_SM,
    FONT_TITLE_SIZE, FONT_BODY_SIZE, FONT_SMALL_SIZE,
    PAD_ITEM, PAD_SECTION, PROGRESS_HEIGHT, SUCCESS_RESET_DELAY
)


class BaseDownloadTab(ctk.CTkFrame):
    """
    Onglet de téléchargement générique.

    Une sous-classe définit les attributs de classe ci-dessous et
    implémente :meth:`download`. Elle peut surcharger
    :meth:`build_extra_options` pour insérer ses propres réglages entre
    le sélecteur de dossier et le bouton de téléchargement.

    Le téléchargement s'exécute dans un thread afin que la fenêtre
    reste réactive ; les retours à l'interface passent tous par
    ``after``, seul moyen sûr de toucher aux widgets depuis un thread.
    """

    #: Titre affiché en haut de l'onglet.
    TITLE = ""
    #: Ligne d'explication affichée sous le titre.
    SUBTITLE = ""
    #: Libellé du bouton de téléchargement.
    BUTTON_TEXT = "Télécharger"
    #: Message de la fenêtre de succès. « {path} » y est remplacé par
    #: le dossier de destination.
    SUCCESS_MESSAGE = "Le fichier a été téléchargé !\n {path}"
    #: Couleur d'accent du bouton et de la barre de progression.
    #: ``None`` laisse la couleur du thème s'appliquer.
    ACCENT_COLOR = None
    #: Couleur du bouton au survol. Ignorée si ACCENT_COLOR vaut None.
    ACCENT_HOVER_COLOR = None
    #: Dossier de destination proposé au premier affichage.
    DEFAULT_OUTPUT_DIR: Path = None

    #: Callback optionnel, appelé après un téléchargement réussi.
    on_download_success = None

    def __init__(self, parent, status_var: ctk.StringVar):
        """
        :param parent: Conteneur parent, typiquement un onglet du CTkTabview.
        :param status_var: Variable de statut partagée avec la fenêtre principale.
        """
        super().__init__(parent, fg_color="transparent")
        self.output_dir = self.DEFAULT_OUTPUT_DIR
        self.status_var = status_var
        self.grid_columnconfigure(0, weight=1)
        self._build()

    # ================================================================== #
    #  Construction de l'interface                                       #
    # ================================================================== #

    def _build(self):
        """Assemble les widgets de l'onglet, de haut en bas."""
        row = 0

        ctk.CTkLabel(
            self,
            text=self.TITLE,
            font=ctk.CTkFont(size=FONT_TITLE_SIZE, weight="bold")
        ).grid(row=row, column=0, pady=(PAD_SECTION, 2), sticky="w")
        row += 1

        ctk.CTkLabel(
            self,
            text=self.SUBTITLE,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            text_color="gray"
        ).grid(row=row, column=0, pady=(0, PAD_SECTION * 2), sticky="w")
        row += 1

        # URL
        ctk.CTkLabel(
            self,
            text="URL de la vidéo YouTube :",
            font=ctk.CTkFont(size=FONT_BODY_SIZE)
        ).grid(row=row, column=0, sticky="w")
        row += 1

        self.url_var = ctk.StringVar()
        ctk.CTkEntry(
            self,
            textvariable=self.url_var,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=ENTRY_HEIGHT,
            font=ctk.CTkFont(size=FONT_BODY_SIZE)
        ).grid(row=row, column=0, pady=(PAD_ITEM, PAD_SECTION * 2), sticky="ew")
        row += 1

        # Dossier
        ctk.CTkLabel(
            self,
            text="Dossier de sortie :",
            font=ctk.CTkFont(size=FONT_BODY_SIZE)
        ).grid(row=row, column=0, sticky="w")
        row += 1

        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.grid(
            row=row, column=0,
            pady=(PAD_ITEM, PAD_SECTION * 2), sticky="ew"
        )
        folder_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self.dir_var = ctk.StringVar(value=str(self.output_dir))
        ctk.CTkEntry(
            folder_frame,
            textvariable=self.dir_var,
            state="readonly",
            height=ENTRY_HEIGHT,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE)
        ).grid(row=0, column=0, sticky="ew", padx=(0, PAD_SECTION))

        ctk.CTkButton(
            folder_frame,
            text="Parcourir",
            width=BUTTON_WIDTH_SM,
            height=ENTRY_HEIGHT,
            command=self._choose_folder
        ).grid(row=0, column=1)

        # Réglages propres à la sous-classe, s'il y en a.
        row = self.build_extra_options(row)

        # Bouton de téléchargement
        button_kwargs = {}
        if self.ACCENT_COLOR:
            button_kwargs["fg_color"] = self.ACCENT_COLOR
            button_kwargs["hover_color"] = self.ACCENT_HOVER_COLOR

        self.btn = ctk.CTkButton(
            self,
            text=self.BUTTON_TEXT,
            height=BUTTON_HEIGHT_LG,
            font=ctk.CTkFont(size=FONT_BODY_SIZE, weight="bold"),
            command=self._start_download,
            **button_kwargs
        )
        self.btn.grid(row=row, column=0, pady=(0, FONT_SMALL_SIZE), sticky="ew")
        row += 1

        # Progression
        progress_kwargs = {}
        if self.ACCENT_COLOR:
            progress_kwargs["progress_color"] = self.ACCENT_COLOR

        self.progress = ctk.CTkProgressBar(
            self,
            height=PROGRESS_HEIGHT,
            **progress_kwargs
        )
        self.progress.set(0)
        self.progress.grid(row=row, column=0, pady=(0, PAD_SECTION), sticky="ew")
        row += 1

        # Statut
        ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            text_color="gray"
        ).grid(row=row, column=0, sticky="w")

    def build_extra_options(self, row: int) -> int:
        """
        Insère les réglages propres à l'onglet.

        Appelée entre le sélecteur de dossier et le bouton de
        téléchargement. La version de base n'ajoute rien.

        :param row: Première ligne de grille disponible.
        :return: Première ligne encore libre après les ajouts.
        """
        return row

    # ================================================================== #
    #  Téléchargement                                                    #
    # ================================================================== #

    def download(self, url: str, output_dir: Path) -> None:
        """
        Effectue le téléchargement proprement dit.

        Appelée depuis un thread de travail. À implémenter dans chaque
        sous-classe.

        :param url: URL de la vidéo YouTube.
        :param output_dir: Dossier de destination choisi par l'utilisateur.
        :raises NotImplementedError: Si la sous-classe ne la définit pas.
        """
        raise NotImplementedError(
            f"{type(self).__name__} doit implémenter download()."
        )

    def _choose_folder(self):
        """Ouvre le sélecteur de dossier et mémorise le choix."""
        folder = filedialog.askdirectory(
            title="Sélectionner un dossier",
            initialdir=str(self.output_dir)
        )
        if folder:
            self.output_dir = Path(folder)
            self.dir_var.set(folder)

    def _start_download(self):
        """Valide l'URL, verrouille le bouton et lance le thread de travail."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Attention", "Colle une URL YouTube.")
            return
        self.btn.configure(state="disabled")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.status_var.set("Téléchargement en cours...")
        threading.Thread(
            target=self._download_task, args=(url,), daemon=True
        ).start()

    def _download_task(self, url: str):
        """Exécute :meth:`download` dans le thread de travail."""
        try:
            self.download(url, self.output_dir)
            self.after(0, self._on_success)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_success(self):
        """Réinitialise l'interface et signale la réussite à l'utilisateur."""
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1)
        self.btn.configure(state="normal")
        self.url_var.set("")
        self.status_var.set(f"Téléchargement réussi ! → {self.output_dir}")
        if self.on_download_success:
            self.on_download_success()
        messagebox.showinfo(
            "Succès",
            self.SUCCESS_MESSAGE.format(path=self.output_dir)
        )
        self.after(SUCCESS_RESET_DELAY, lambda: self.progress.set(0))

    def _on_error(self, message: str):
        """Réinitialise l'interface et affiche l'erreur rencontrée."""
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.btn.configure(state="normal")
        self.status_var.set("Une erreur est survenue.")
        messagebox.showerror("Erreur", f"Une erreur est survenue :\n{message}")