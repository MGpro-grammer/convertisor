"""
Fenêtre principale de l'application Convertisor.

Assemble les onglets dans un ``CTkTabview``, partage entre eux une
variable de statut, et gère la recherche de mises à jour affichée dans
la barre du bas.
"""

import threading
from tkinter import messagebox

import customtkinter as ctk

from core.constants import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    DEFAULT_COLOR_THEME,
    BUTTON_HEIGHT_SM, BUTTON_WIDTH_UPDATE,
    FONT_TINY_SIZE, FONT_SMALL_SIZE,
    PAD_OUTER, PAD_TABS, PAD_SECTION,
    UPDATE_BTN_DELAY
)
from core.settings import load_settings
from core.updater import check_for_update, download_and_install, get_current_version
from .tab_convert import TabConvert
from .tab_files import TabFiles
from .tab_gif import TabGif
from .tab_settings import TabSettings
from .tab_video import TabVideo

ctk.set_default_color_theme(DEFAULT_COLOR_THEME)


class App(ctk.CTk):
    """
    Fenêtre principale de l'application.

    Charge les préférences utilisateur, construit l'interface, puis
    lance en arrière-plan une vérification des mises à jour afin de ne
    pas retarder l'affichage de la fenêtre.
    """

    def __init__(self):
        """Initialise la fenêtre, applique le thème et construit l'interface."""
        super().__init__()
        self.settings = load_settings()

        # Applique le thème sauvegardé
        ctk.set_appearance_mode(
            self.settings.get("appearance_mode", "Dark")
        )

        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resizable(True, True)

        self._center_window()
        self._build_ui()

        threading.Thread(
            target=self._check_update_on_start, daemon=True
        ).start()

    def _center_window(self):
        """Positionne la fenêtre au centre de l'écran principal."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
        y = (self.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

    def _build_ui(self):
        """
        Construit les onglets et la barre du bas.

        La variable ``status_var`` est partagée entre les onglets de
        téléchargement : chacun y écrit son avancement, ce qui évite
        de dupliquer un libellé de statut par onglet.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Onglets
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(
            row=0, column=0,
            padx=PAD_TABS, pady=(PAD_SECTION, 0), sticky="nsew"
        )
        self.tabs.add("🎵  Convertir MP3")
        self.tabs.add("📽️  Convertir MP4")
        self.tabs.add("🎞  Créer un GIF")
        self.tabs.add("🗑  Fichiers")
        self.tabs.add("⚙  Paramètres")

        for tab_name in [
            "🎵  Convertir MP3", "📽️  Convertir MP4", "🎞  Créer un GIF",
            "🗑  Fichiers", "⚙  Paramètres",
        ]:
            self.tabs.tab(tab_name).grid_columnconfigure(0, weight=1)
            self.tabs.tab(tab_name).grid_rowconfigure(0, weight=1)

        # Statut partagé entre onglets
        self.status_var = ctk.StringVar(value="En attente...")

        # Instanciation des onglets
        self.tab_convert = TabConvert(
            self.tabs.tab("🎵  Convertir MP3"),
            self.status_var
        )
        self.tab_convert.grid(row=0, column=0, sticky="nsew")
        self.tab_convert.on_download_success = self._on_download_success

        self.tab_video = TabVideo(
            self.tabs.tab("📽️  Convertir MP4"),
            self.status_var
        )
        self.tab_video.grid(row=0, column=0, sticky="nsew")
        self.tab_video.on_download_success = self._on_download_success

        self.tab_gif = TabGif(
            self.tabs.tab("🎞  Créer un GIF"),
            self.status_var
        )
        self.tab_gif.grid(row=0, column=0, sticky="nsew")
        self.tab_gif.on_download_success = self._on_download_success

        self.tab_files = TabFiles(
            self.tabs.tab("🗑  Fichiers"),
            self.settings
        )
        self.tab_files.grid(row=0, column=0, sticky="nsew")

        self.tab_settings = TabSettings(
            self.tabs.tab("⚙  Paramètres"),
            self.settings,
            on_appearance_change=None  # pas de callback nécessaire
        )
        self.tab_settings.grid(row=0, column=0, sticky="nsew")

        # Barre du bas
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(
            row=1, column=0,
            padx=PAD_OUTER, pady=(PAD_SECTION // 2, PAD_SECTION),
            sticky="ew"
        )
        bottom.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            bottom,
            text=f"Version {get_current_version()}",
            font=ctk.CTkFont(size=FONT_TINY_SIZE),
            text_color="gray"
        ).grid(row=0, column=0, sticky="w")

        self.update_btn = ctk.CTkButton(
            bottom,
            text="Rechercher les mises à jour",
            width=BUTTON_WIDTH_UPDATE,
            height=BUTTON_HEIGHT_SM,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray80"),
            command=self._check_update_manual
        )
        self.update_btn.grid(row=0, column=1, sticky="e")

    def _on_download_success(self):
        """Rafraîchit l'onglet Fichiers après un téléchargement."""
        self.tab_files.refresh()

    # ================================================================== #
    #  Auto-updater                                                      #
    # ================================================================== #

    def _check_update_on_start(self):
        """
        Vérifie les mises à jour au démarrage, sans bloquer l'affichage.

        Exécutée dans un thread : le résultat est remis sur le thread
        graphique via ``after``, seul autorisé à toucher aux widgets.
        """
        update = check_for_update()
        if update:
            self.after(0, self._show_update_available, update)

    def _check_update_manual(self):
        """Lance une vérification déclenchée par le bouton de la barre du bas."""
        self.update_btn.configure(state="disabled", text="Vérification...")
        threading.Thread(
            target=self._check_update_task, daemon=True
        ).start()

    def _check_update_task(self):
        """Effectue la vérification manuelle et met à jour le bouton."""
        update = check_for_update()
        if update:
            self.after(0, self._show_update_available, update)
        else:
            self.after(0, self._show_up_to_date)

    def _show_update_available(self, update: dict):
        """
        Transforme le bouton en invitation à installer la mise à jour.

        :param update: Dictionnaire renvoyé par
            :func:`core.updater.check_for_update`.
        """
        self.update_btn.configure(
            state="normal",
            text=f"⬆ Mise à jour v{update['version']} disponible !",
            fg_color=("green", "darkgreen"),
            text_color="white",
            command=lambda: self._install_update(update)
        )

    def _show_up_to_date(self):
        """Confirme que l'application est à jour, puis restaure le bouton."""
        self.update_btn.configure(state="normal", text="Application à jour")
        self.after(UPDATE_BTN_DELAY, lambda: self.update_btn.configure(
            text="Rechercher les mises à jour",
            command=self._check_update_manual
        ))

    def _install_update(self, update: dict):
        """
        Demande confirmation, puis télécharge et lance l'installateur.

        L'application se ferme une fois l'installateur démarré : il ne
        peut pas remplacer un exécutable en cours d'exécution.

        :param update: Dictionnaire renvoyé par
            :func:`core.updater.check_for_update`.
        """
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