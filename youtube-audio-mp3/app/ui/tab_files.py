import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from ..constants import (
    BUTTON_HEIGHT_MD, BUTTON_WIDTH_MD,
    FONT_BODY_SIZE, FONT_SMALL_SIZE, FILE_ROW_HEIGHT, PAD_SECTION, PAD_ITEM
)


class TabFiles(ctk.CTkFrame):
    def __init__(self, parent, output_dir: Path, settings: dict):
        super().__init__(parent, fg_color="transparent")
        self.output_dir = output_dir
        self.settings = settings
        self._selected_file = None
        self._file_buttons = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()

    def _build(self):
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
            text="Fichiers MP3 téléchargés",
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

    def refresh(self):
        """Recharge la liste des fichiers MP3."""
        for widget in self.file_listbox.winfo_children():
            widget.destroy()
        self._file_buttons = []
        self._selected_file = None
        self.delete_btn.configure(state="disabled")

        mp3_files = sorted(self.output_dir.glob("*.mp3")) \
            if self.output_dir.exists() else []

        if not mp3_files:
            ctk.CTkLabel(
                self.file_listbox,
                text="Aucun fichier MP3 trouvé.",
                text_color="gray",
                font=ctk.CTkFont(size=FONT_SMALL_SIZE)
            ).grid(row=0, column=0, pady=20)
            return

        for i, f in enumerate(mp3_files):
            btn = ctk.CTkButton(
                self.file_listbox,
                text=f"🎵  {f.name}",
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
        self._selected_file = file
        self.delete_btn.configure(state="normal")
        for btn, f in self._file_buttons:
            btn.configure(
                fg_color=("gray75", "gray35") if f == file else "transparent"
            )

    def _delete_selected(self):
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