import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from mp3.downloader import download_audio_as_mp3
from core.config import DOWNLOADS_MP3
from core.constants import (
    ENTRY_HEIGHT, BUTTON_HEIGHT_LG, BUTTON_WIDTH_SM,
    FONT_TITLE_SIZE, FONT_BODY_SIZE, FONT_SMALL_SIZE,
    PAD_ITEM, PAD_SECTION, PROGRESS_HEIGHT, SUCCESS_RESET_DELAY
)


class TabConvert(ctk.CTkFrame):
    def __init__(self, parent, status_var: ctk.StringVar):
        super().__init__(parent, fg_color="transparent")
        self.output_dir = DOWNLOADS_MP3
        self.status_var = status_var
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text="🎵 YouTube to MP3 Converter",
            font=ctk.CTkFont(size=FONT_TITLE_SIZE, weight="bold")
        ).grid(row=0, column=0, pady=(PAD_SECTION, 2), sticky="w")

        ctk.CTkLabel(
            self,
            text="Télécharge l'audio d'une vidéo YouTube en MP3",
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            text_color="gray"
        ).grid(row=1, column=0, pady=(0, PAD_SECTION * 2), sticky="w")

        # URL
        ctk.CTkLabel(
            self,
            text="URL de la vidéo YouTube :",
            font=ctk.CTkFont(size=FONT_BODY_SIZE)
        ).grid(row=2, column=0, sticky="w")

        self.url_var = ctk.StringVar()
        ctk.CTkEntry(
            self,
            textvariable=self.url_var,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=ENTRY_HEIGHT,
            font=ctk.CTkFont(size=FONT_BODY_SIZE)
        ).grid(row=3, column=0, pady=(PAD_ITEM, PAD_SECTION * 2), sticky="ew")

        # Dossier
        ctk.CTkLabel(
            self,
            text="Dossier de sortie :",
            font=ctk.CTkFont(size=FONT_BODY_SIZE)
        ).grid(row=4, column=0, sticky="w")

        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.grid(
            row=5, column=0,
            pady=(PAD_ITEM, PAD_SECTION * 2), sticky="ew"
        )
        folder_frame.grid_columnconfigure(0, weight=1)

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

        # Bouton télécharger
        self.btn = ctk.CTkButton(
            self,
            text="Télécharger MP3",
            height=BUTTON_HEIGHT_LG,
            font=ctk.CTkFont(size=FONT_BODY_SIZE, weight="bold"),
            command=self._start_download
        )
        self.btn.grid(row=6, column=0, pady=(0, FONT_SMALL_SIZE), sticky="ew")

        # Progression
        self.progress = ctk.CTkProgressBar(self, height=PROGRESS_HEIGHT)
        self.progress.set(0)
        self.progress.grid(row=7, column=0, pady=(0, PAD_SECTION), sticky="ew")

        # Statut
        ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            text_color="gray"
        ).grid(row=8, column=0, sticky="w")

    def _choose_folder(self):
        folder = filedialog.askdirectory(
            title="Sélectionner un dossier",
            initialdir=str(self.output_dir)
        )
        if folder:
            self.output_dir = Path(folder)
            self.dir_var.set(folder)

    def _start_download(self):
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
        try:
            download_audio_as_mp3(url, self.output_dir)
            self.after(0, self._on_success)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_success(self):
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
            f"Le fichier MP3 a été téléchargé !\n {self.output_dir}"
        )
        self.after(SUCCESS_RESET_DELAY, lambda: self.progress.set(0))

    def _on_error(self, message: str):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.btn.configure(state="normal")
        self.status_var.set("Une erreur est survenue.")
        messagebox.showerror("Erreur", f"Une erreur est survenue :\n{message}")

    # Callback optionnel appelé après un téléchargement réussi
    on_download_success = None