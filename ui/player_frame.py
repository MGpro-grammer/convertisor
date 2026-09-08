"""
Sélection de la plage à convertir en GIF.

Composant affiché dans l'onglet GIF, entre le sélecteur de dossier et
le bouton de conversion. Il présente la vidéo — miniature, titre,
durée — puis recueille les bornes de l'extrait et les réglages de
qualité, en signalant immédiatement toute incohérence.

Tkinter ne sait pas lire de vidéo. La sélection se fait donc au code
temporel, validée contre la durée réelle obtenue auprès de YouTube :
l'utilisateur relève les temps sur YouTube et les recopie ici.

Le composant est passif : il n'effectue aucun appel réseau de son
propre chef, à l'exception du chargement de la miniature une fois
l'adresse connue. C'est l'onglet qui pilote la récupération des
métadonnées.
"""

import threading
from io import BytesIO

import customtkinter as ctk
from PIL import Image

from core.constants import (
    ENTRY_HEIGHT, FONT_BODY_SIZE, FONT_SMALL_SIZE,
    PAD_ITEM, PAD_SECTION, THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH
)
from core.timecode import format_timecode, parse_timecode
from core.youtube import VideoInfo, fetch_thumbnail
from gif.converter import (
    DEFAULT_FPS, DEFAULT_WIDTH, FPS_CHOICES, MAX_DURATION,
    MIN_DURATION, WIDTH_CHOICES, estimate_size_mb
)

#: Durée de l'extrait proposée par défaut, en secondes.
DEFAULT_CLIP_DURATION = 5.0

#: Message affiché tant qu'aucune vidéo n'a été analysée.
IDLE_MESSAGE = "Collez une URL puis cliquez sur « Analyser »."


class PlayerFrame(ctk.CTkFrame):
    """
    Sélecteur de plage et de qualité pour la conversion en GIF.

    Utilisation :

    1. l'onglet récupère les métadonnées et appelle :meth:`set_video_info` ;
    2. l'utilisateur ajuste les bornes et les réglages ;
    3. l'onglet lit :meth:`get_range`, :meth:`get_fps` et :meth:`get_width`.

    Tant qu'aucune vidéo n'est chargée, :meth:`get_range` refuse de
    répondre : sans durée connue, aucune borne n'est vérifiable.
    """

    def __init__(self, parent):
        """
        :param parent: Conteneur parent, typiquement l'onglet GIF.
        """
        super().__init__(parent)
        self.video_info: VideoInfo | None = None
        self._thumbnail_image = None  # Référence gardée : sinon Tk libère l'image.
        self.grid_columnconfigure(1, weight=1)
        self._build()

    # ================================================================== #
    #  Construction de l'interface                                       #
    # ================================================================== #

    def _build(self):
        """Assemble la vignette, les champs de plage et les réglages."""
        # Miniature
        self.thumbnail_label = ctk.CTkLabel(
            self,
            text="",
            width=THUMBNAIL_WIDTH,
            height=THUMBNAIL_HEIGHT,
            fg_color=("gray85", "gray25"),
            corner_radius=6,
        )
        self.thumbnail_label.grid(
            row=0, column=0, rowspan=2,
            padx=PAD_SECTION, pady=PAD_SECTION, sticky="nw"
        )

        # Titre et durée
        self.title_var = ctk.StringVar(value=IDLE_MESSAGE)
        ctk.CTkLabel(
            self,
            textvariable=self.title_var,
            font=ctk.CTkFont(size=FONT_BODY_SIZE, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=280,
        ).grid(row=0, column=1, padx=(0, PAD_SECTION), pady=(PAD_SECTION, 0), sticky="new")

        self.duration_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self,
            textvariable=self.duration_var,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            text_color="gray",
            anchor="w",
        ).grid(row=1, column=1, padx=(0, PAD_SECTION), sticky="nw")

        # Bornes de l'extrait
        range_frame = ctk.CTkFrame(self, fg_color="transparent")
        range_frame.grid(
            row=2, column=0, columnspan=2,
            padx=PAD_SECTION, pady=(PAD_SECTION, 0), sticky="ew"
        )

        ctk.CTkLabel(
            range_frame,
            text="Début",
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
        ).grid(row=0, column=0, padx=(0, PAD_ITEM))

        self.start_var = ctk.StringVar(value="0:00")
        ctk.CTkEntry(
            range_frame,
            textvariable=self.start_var,
            width=70,
            height=ENTRY_HEIGHT,
            justify="center",
            font=ctk.CTkFont(size=FONT_BODY_SIZE),
        ).grid(row=0, column=1, padx=(0, PAD_SECTION))

        ctk.CTkLabel(
            range_frame,
            text="Fin",
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
        ).grid(row=0, column=2, padx=(0, PAD_ITEM))

        self.end_var = ctk.StringVar(value=format_timecode(DEFAULT_CLIP_DURATION))
        ctk.CTkEntry(
            range_frame,
            textvariable=self.end_var,
            width=70,
            height=ENTRY_HEIGHT,
            justify="center",
            font=ctk.CTkFont(size=FONT_BODY_SIZE),
        ).grid(row=0, column=3)

        # Réglages de qualité
        quality_frame = ctk.CTkFrame(self, fg_color="transparent")
        quality_frame.grid(
            row=3, column=0, columnspan=2,
            padx=PAD_SECTION, pady=(PAD_ITEM, 0), sticky="ew"
        )

        ctk.CTkLabel(
            quality_frame,
            text="Images/s",
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
        ).grid(row=0, column=0, padx=(0, PAD_ITEM))

        self.fps_var = ctk.StringVar(value=str(DEFAULT_FPS))
        ctk.CTkOptionMenu(
            quality_frame,
            values=[str(value) for value in FPS_CHOICES],
            variable=self.fps_var,
            width=70,
            height=ENTRY_HEIGHT,
        ).grid(row=0, column=1, padx=(0, PAD_SECTION))

        ctk.CTkLabel(
            quality_frame,
            text="Largeur",
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
        ).grid(row=0, column=2, padx=(0, PAD_ITEM))

        self.width_var = ctk.StringVar(value=str(DEFAULT_WIDTH))
        ctk.CTkOptionMenu(
            quality_frame,
            values=[str(value) for value in WIDTH_CHOICES],
            variable=self.width_var,
            width=80,
            height=ENTRY_HEIGHT,
        ).grid(row=0, column=3)

        # Estimation et messages de validation
        self.estimate_var = ctk.StringVar(value="")
        self.estimate_label = ctk.CTkLabel(
            self,
            textvariable=self.estimate_var,
            font=ctk.CTkFont(size=FONT_SMALL_SIZE),
            text_color="gray",
            anchor="w",
        )
        self.estimate_label.grid(
            row=4, column=0, columnspan=2,
            padx=PAD_SECTION, pady=(PAD_ITEM, PAD_SECTION), sticky="w"
        )

        # Toute modification rafraîchit l'estimation.
        for variable in (self.start_var, self.end_var, self.fps_var, self.width_var):
            variable.trace_add("write", self._on_change)

    # ================================================================== #
    #  Chargement d'une vidéo                                            #
    # ================================================================== #

    def set_video_info(self, info: VideoInfo):
        """
        Affiche une vidéo et réinitialise les bornes.

        La plage proposée part de zéro et dure
        :data:`DEFAULT_CLIP_DURATION` secondes, sans dépasser la vidéo.
        La miniature est chargée en arrière-plan : son absence n'empêche
        rien.

        :param info: Métadonnées obtenues par
            :func:`core.youtube.fetch_video_info`.
        """
        self.video_info = info
        self.title_var.set(info.title)
        self.duration_var.set(f"Durée : {format_timecode(info.duration)}")

        self.start_var.set("0:00")
        self.end_var.set(
            format_timecode(min(DEFAULT_CLIP_DURATION, info.duration))
        )

        if info.thumbnail_url:
            threading.Thread(
                target=self._load_thumbnail,
                args=(info.thumbnail_url,),
                daemon=True,
            ).start()

        self._update_estimate()

    def clear(self):
        """Revient à l'état initial, sans vidéo chargée."""
        self.video_info = None
        self._thumbnail_image = None
        self.title_var.set(IDLE_MESSAGE)
        self.duration_var.set("")
        self.estimate_var.set("")
        self.thumbnail_label.configure(image=None, text="")

    def _load_thumbnail(self, url: str):
        """
        Télécharge et redimensionne la miniature, dans un thread.

        Un échec est ignoré : la miniature est un confort, pas une
        condition de fonctionnement.
        """
        try:
            data = fetch_thumbnail(url)
            image = Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            return
        self.after(0, self._show_thumbnail, image)

    def _show_thumbnail(self, image: Image.Image):
        """Affiche la miniature téléchargée, sur le thread graphique."""
        self._thumbnail_image = ctk.CTkImage(
            light_image=image,
            size=(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT),
        )
        self.thumbnail_label.configure(image=self._thumbnail_image, text="")

    # ================================================================== #
    #  Lecture des réglages                                              #
    # ================================================================== #

    def get_range(self) -> tuple[float, float]:
        """
        Retourne les bornes de l'extrait, en secondes.

        :return: Le couple (début, fin).
        :raises ValueError: Aucune vidéo chargée, code temporel
            illisible, bornes inversées, extrait trop court ou trop
            long, ou fin au-delà de la durée de la vidéo.
        """
        if self.video_info is None:
            raise ValueError("Analysez d'abord une vidéo.")

        start = parse_timecode(self.start_var.get())
        end = parse_timecode(self.end_var.get())

        if end > self.video_info.duration:
            raise ValueError(
                "La fin dépasse la durée de la vidéo "
                f"({format_timecode(self.video_info.duration)})."
            )

        duration = end - start
        if duration < MIN_DURATION:
            raise ValueError("La fin doit être postérieure au début.")
        if duration > MAX_DURATION:
            raise ValueError(
                f"L'extrait ne peut pas dépasser {MAX_DURATION:g} secondes."
            )

        return start, end

    def get_fps(self) -> int:
        """Retourne le nombre d'images par seconde choisi."""
        return int(self.fps_var.get())

    def get_width(self) -> int:
        """Retourne la largeur choisie, en pixels."""
        return int(self.width_var.get())

    # ================================================================== #
    #  Validation continue                                               #
    # ================================================================== #

    def _on_change(self, *_args):
        """Réagit à toute modification d'un champ ou d'un menu."""
        self._update_estimate()

    def _update_estimate(self):
        """
        Met à jour la ligne d'information sous les réglages.

        Affiche la durée retenue et le poids attendu quand la saisie est
        valide, le motif du refus sinon. L'utilisateur sait ainsi
        immédiatement où il en est, sans avoir à lancer la conversion.
        """
        if self.video_info is None:
            self.estimate_var.set("")
            return

        try:
            start, end = self.get_range()
        except ValueError as error:
            self.estimate_var.set(str(error))
            self.estimate_label.configure(text_color=("#c0392b", "#e74c3c"))
            return

        duration = end - start
        size = estimate_size_mb(duration, self.get_fps(), self.get_width())
        self.estimate_var.set(
            f"Extrait de {duration:.1f} s — environ {size:.1f} Mo"
        )
        self.estimate_label.configure(text_color="gray")