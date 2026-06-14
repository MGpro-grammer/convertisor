import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from .downloader import download_audio_as_mp3
from .config import BASE_DIR
from .updater import check_for_update, download_and_install, get_current_version
from .settings import load_settings, save_settings

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Convertisor")
        self.geometry("640x540")
        self.minsize(520, 460)
        self.resizable(True, True)
        self.output_dir = BASE_DIR / "downloads"
        self.settings = load_settings()
        self._center_window()
        self._build_ui()
        threading.Thread(
            target=self._check_update_on_start, daemon=True
        ).start()

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"600x500+{x}+{y}")

    # ================================================================== #
    #  UI principale                                                       #
    # ================================================================== #

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Onglets
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=0, column=0, padx=16, pady=(12, 0), sticky="nsew")

        self.tabs.add("🎵  Convertir")
        self.tabs.add("🗑  Fichiers")
        self.tabs.add("⚙  Paramètres")

        self._build_tab_convert(self.tabs.tab("🎵  Convertir"))
        self._build_tab_files(self.tabs.tab("🗑  Fichiers"))
        self._build_tab_settings(self.tabs.tab("⚙  Paramètres"))

        # Barre du bas (version + MAJ) commune à tous les onglets
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=1, column=0, padx=24, pady=(4, 12), sticky="ew")
        bottom.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            bottom,
            text=f"Version {get_current_version()}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=0, column=0, sticky="w")

        self.update_btn = ctk.CTkButton(
            bottom,
            text="Rechercher les mises à jour",
            width=220, height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            command=self._check_update_manual
        )
        self.update_btn.grid(row=0, column=1, sticky="e")

    # ================================================================== #
    #  Onglet 1 — Convertir                                               #
    # ================================================================== #

    def _build_tab_convert(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            parent,
            text="YouTube to MP3 Converter",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=(8, 2), sticky="w")

        ctk.CTkLabel(
            parent,
            text="Télécharge l'audio d'une vidéo YouTube en MP3",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, pady=(0, 16), sticky="w")

        # URL
        ctk.CTkLabel(
            parent,
            text="URL de la vidéo YouTube :",
            font=ctk.CTkFont(size=13)
        ).grid(row=2, column=0, sticky="w")

        self.url_var = ctk.StringVar()
        ctk.CTkEntry(
            parent,
            textvariable=self.url_var,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=38,
            font=ctk.CTkFont(size=13)
        ).grid(row=3, column=0, pady=(4, 16), sticky="ew")

        # Dossier
        ctk.CTkLabel(
            parent,
            text="Dossier de sortie :",
            font=ctk.CTkFont(size=13)
        ).grid(row=4, column=0, sticky="w")

        folder_frame = ctk.CTkFrame(parent, fg_color="transparent")
        folder_frame.grid(row=5, column=0, pady=(4, 16), sticky="ew")
        folder_frame.grid_columnconfigure(0, weight=1)

        self.dir_var = ctk.StringVar(value=str(self.output_dir))
        ctk.CTkEntry(
            folder_frame,
            textvariable=self.dir_var,
            state="readonly",
            height=38,
            font=ctk.CTkFont(size=12)
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            folder_frame,
            text="Parcourir",
            width=100, height=38,
            command=self._choose_folder
        ).grid(row=0, column=1)

        # Bouton télécharger
        self.btn = ctk.CTkButton(
            parent,
            text="Télécharger MP3",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_download
        )
        self.btn.grid(row=6, column=0, pady=(0, 12), sticky="ew")

        # Progression
        self.progress = ctk.CTkProgressBar(parent, height=8)
        self.progress.set(0)
        self.progress.grid(row=7, column=0, pady=(0, 8), sticky="ew")

        # Statut
        self.status_var = ctk.StringVar(value="En attente...")
        ctk.CTkLabel(
            parent,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=8, column=0, sticky="w")

    # ================================================================== #
    #  Onglet 2 — Fichiers                                                #
    # ================================================================== #

    def _build_tab_files(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        # Barre d'outils
        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, pady=(8, 8), sticky="ew")
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            toolbar,
            text="Actualiser",
            width=110, height=32,
            font=ctk.CTkFont(size=12),
            command=self._refresh_file_list
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkLabel(
            toolbar,
            text="Fichiers MP3 téléchargés",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=1, sticky="w")

        self.delete_btn = ctk.CTkButton(
            toolbar,
            text="🗑 Supprimer",
            width=110, height=32,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            state="disabled",
            command=self._delete_selected
        )
        self.delete_btn.grid(row=0, column=2)

        # Liste des fichiers
        self.file_listbox = ctk.CTkScrollableFrame(parent)
        self.file_listbox.grid(
            row=1, column=0, pady=(0, 8), sticky="nsew"
        )
        self.file_listbox.grid_columnconfigure(0, weight=1)

        self._selected_file = None
        self._file_buttons = []
        self._refresh_file_list()

    def _refresh_file_list(self):
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
                font=ctk.CTkFont(size=12)
            ).grid(row=0, column=0, pady=20)
            return

        for i, f in enumerate(mp3_files):
            btn = ctk.CTkButton(
                self.file_listbox,
                text=f"🎵  {f.name}",
                font=ctk.CTkFont(size=12),
                anchor="w",
                height=36,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda file=f, b=None: self._select_file(file)
            )
            btn.grid(row=i, column=0, pady=2, sticky="ew")
            self._file_buttons.append((btn, f))

    def _select_file(self, file: Path):
        """Sélectionne un fichier dans la liste."""
        self._selected_file = file
        self.delete_btn.configure(state="normal")

        for btn, f in self._file_buttons:
            if f == file:
                btn.configure(fg_color=("gray75", "gray35"))
            else:
                btn.configure(fg_color="transparent")

    def _delete_selected(self):
        """Supprime le fichier sélectionné."""
        if not self._selected_file:
            return

        if self.settings.get("confirm_delete", True):
            confirmed = messagebox.askyesno(
                "Confirmation",
                f"Supprimer ce fichier ?\n\n{self._selected_file.name}"
            )
            if not confirmed:
                return

        try:
            self._selected_file.unlink()
            self._refresh_file_list()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer :\n{e}")

    # ================================================================== #
    #  Onglet 3 — Paramètres                                              #
    # ================================================================== #

    def _build_tab_settings(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            parent,
            text="⚙ Paramètres",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=(8, 16), sticky="w")

        # Section Suppressions
        ctk.CTkLabel(
            parent,
            text="SUPPRESSIONS",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=1, column=0, pady=(0, 4), sticky="w")

        card = ctk.CTkFrame(parent)
        card.grid(row=2, column=0, pady=(0, 16), sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Demander confirmation avant de supprimer un fichier",
            font=ctk.CTkFont(size=13),
            anchor="w"
        ).grid(row=0, column=0, padx=16, pady=14, sticky="w")

        self.confirm_var = ctk.BooleanVar(
            value=self.settings.get("confirm_delete", True)
        )
        ctk.CTkSwitch(
            card,
            text="",
            variable=self.confirm_var,
            command=self._save_settings
        ).grid(row=0, column=1, padx=16, pady=14)

    def _save_settings(self):
        """Sauvegarde les paramètres et met à jour en mémoire."""
        self.settings["confirm_delete"] = self.confirm_var.get()
        save_settings(self.settings)

    # ================================================================== #
    #  Actions téléchargement                                             #
    # ================================================================== #

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
        self._refresh_file_list()
        messagebox.showinfo(
            "Succès",
            f"Le fichier MP3 a été téléchargé !\n {self.output_dir}"
        )
        self.after(3000, lambda: self.progress.set(0))

    def _on_error(self, message: str):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.btn.configure(state="normal")
        self.status_var.set("Une erreur est survenue.")
        messagebox.showerror("Erreur", f"Une erreur est survenue :\n{message}")

    # ================================================================== #
    #  Auto-updater                                                        #
    # ================================================================== #

    def _check_update_on_start(self):
        update = check_for_update()
        if update:
            self.after(0, self._show_update_available, update)

    def _check_update_manual(self):
        self.update_btn.configure(state="disabled", text="Vérification...")
        threading.Thread(
            target=self._check_update_task, daemon=True
        ).start()

    def _check_update_task(self):
        update = check_for_update()
        if update:
            self.after(0, self._show_update_available, update)
        else:
            self.after(0, self._show_up_to_date)

    def _show_update_available(self, update: dict):
        self.update_btn.configure(
            state="normal",
            text=f"Mise à jour v{update['version']} disponible !",
            fg_color=("green", "darkgreen"),
            text_color="white",
            command=lambda: self._install_update(update)
        )

    def _show_up_to_date(self):
        self.update_btn.configure(
            state="normal", text="Application à jour"
        )
        self.after(3000, lambda: self.update_btn.configure(
            text="Rechercher les mises à jour",
            command=self._check_update_manual
        ))

    def _install_update(self, update: dict):
        if messagebox.askyesno(
            "Mise à jour disponible",
            f"Version {update['version']} disponible.\n"
            "Télécharger et installer maintenant ?"
        ):
            self.update_btn.configure(
                state="disabled", text="⬇ Téléchargement..."
            )
            download_and_install(
                update["download_url"],
                on_progress=lambda msg: self.after(
                    0, self.status_var.set, msg
                ),
                on_done=lambda: self.after(0, self.destroy),
                on_error=lambda err: self.after(
                    0, messagebox.showerror, "Erreur", err
                )
            )