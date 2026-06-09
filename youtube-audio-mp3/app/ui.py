import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from .downloader import download_audio_as_mp3
from .config import BASE_DIR
from .updater import check_for_update, download_and_install, get_current_version

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Convertisor")
        self.resizable(False, False)
        self.output_dir = BASE_DIR / "downloads"
        self._build_ui()
        threading.Thread(target=self._check_update_on_start, daemon=True).start()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.grid()

        #Titre
        ttk.Label(
            frame,
            text="YouTube video to MP3 Converter",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, pady=(0, 16))

        #Champ URL
        ttk.Label(
            frame,
            text="YouTube Video URL:",
        ).grid(row=1, column=0, sticky="w")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(
            frame,
            textvariable=self.url_var,
            width=45
        )
        self.url_entry.grid(row=2, column=0, columnspan=2, pady=(4, 12))

        # Sélection du dossier de téléchargement
        ttk.Label(
            frame,
            text="Dossier de sortie :"
        ).grid(row=3, column=0, columnspan=3, sticky="w")
        self.dir_var = tk.StringVar(value=str(self.output_dir))
        ttk.Entry(
            frame,
            textvariable=self.dir_var,
            width=36,
            state="readonly"
        ).grid(row=4, column=0, columnspan=2, pady=(4, 12), sticky="w")
        ttk.Button(
            frame,
            text="Choose your own folder",
            command=self._choose_folder
        ).grid(row=4, column=2, padx=(6, 0), pady=(4, 12))

        #Bouton de téléchargement
        self.btn = ttk.Button(
            frame,
            text="Download MP3",
            command=self._start_download
        )
        self.btn.grid(row=5, column=0, columnspan=3, pady=(4, 0))

        # Barre de progression
        self.progress = ttk.Progressbar(
            frame,
            mode="indeterminate",
            length=300
        )
        self.progress.grid(row=6, column=0, columnspan=3, pady=(12,8))

        #Statut
        self.status_var = tk.StringVar(value="En attente...")
        ttk.Label(
            frame,
            textvariable=self.status_var
        ).grid(row=7, column=0, columnspan=3)

        # Séparateur
        ttk.Separator(
            frame,
            orient="horizontal"
        ).grid(row=8, column=0, columnspan=3, sticky="ew", pady=(16, 8))

        # Version + bouton mise à jour
        self.version_label = ttk.Label(
            frame,
            text=f"Version: {get_current_version()}",
            foreground="gray"
        )
        self.version_label.grid(row=9, column=0, sticky="w")

        self.update_btn = ttk.Button(
            frame,
            text="Check for updates",
            command=self._check_update_manual
        )
        self.update_btn.grid(row=9, column=1, columnspan=2, sticky="e")

    def _choose_folder(self):
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=str(self.output_dir)
        )
        if folder:
            self.output_dir = Path(folder)
            self.dir_var.set(folder)


    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Attention", "Paste a YouTube video URL.")
            return

        #Désactiver le bouton pendant le téléchargement
        self.btn.config(state="disabled")
        self.progress.start(10)
        self.status_var.set("Downloading...")

        #Lance dans un thread séparé pour ne pas bloquer l'interface
        thread = threading.Thread(target=self._download_task, args=(url,), daemon=True)
        thread.start()

    def _download_task(self, url: str):
        try:
            download_audio_as_mp3(url, self.output_dir)
            self.after(0, self._on_success)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _on_success(self):
        self.progress.stop()
        self.btn.config(state="normal")
        self.url_var.set("")
        self.status_var.set(f"Download completed successfully! Check {self.output_dir} folder.")
        messagebox.showinfo("Success", f"The MP3 file has been downloaded successfully! Check the {self.output_dir} folder.")

    def _on_error(self, message: str):
        self.progress.stop()
        self.btn.config(state="normal")
        self.status_var.set("An error occurred during download.")
        messagebox.showerror("Error", f"An error occurred: {message}")

    def _check_update_on_start(self):
        """Check quietly for updates when the app starts."""
        update = check_for_update()
        if update:
            self.after(0, self._show_update_available, update)

    def _check_update_manual(self):
        """Manually triggered update check."""
        self.update_btn.config(state="disabled", text="Checking...")
        threading.Thread(target=self._check_update_task, daemon=True).start()

    def _check_update_task(self):
        update = check_for_update()
        if update:
            self.after(0, self._show_update_available, update)
        else:
            self.after(0, self._show_up_to_date)

    def _show_update_available(self, update: dict):
        self.update_btn.config(
            state="normal",
            text=f"Update Available: {update['version']}",
            command=lambda: self._install_update(update)
        )

    def _show_up_to_date(self):
        self.update_btn.config(state="normal", text="App is up to date")
        # Remet le bouton normal après 3 secondes
        self.after(3000, lambda: self.update_btn.config(
            text="Check for updates",
            command=self._check_update_manual
        ))

    def _install_update(self, update: dict):
        from tkinter import messagebox
        if messagebox.askyesno(
            "Update Available",
            f"Version {update['version']} is available. \n"
            "Do you want to download and install it now?"
        ):
            self.update_btn.config(state="disabled", text="Downloading update...")
            download_and_install(
                update["download_url"],
                on_progress=lambda msg: self.after(0, self.status_var.set, msg),
                on_done=lambda: self.after(0, self.destroy),
                on_error=lambda err: self.after(0, messagebox.showerror, "Erreur", err)
            )