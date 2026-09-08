"""
Constantes d'interface : dimensions, polices, espacements, délais.

Centraliser ces valeurs garantit la cohérence visuelle entre les
onglets et permet d'ajuster l'apparence sans toucher au code des
composants.
"""

#—— Fenêtre ———————————————————————————————————————————————————————————————————————
WINDOW_TITLE = "Convertisor"
WINDOW_WIDTH = 620
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 560
WINDOW_MIN_HEIGHT = 620

#—— Thème —————————————————————————————————————————————————————————————————————————
DEFAULT_APPEARANCE = "Dark" # "Dark" | "Light" | "System"
DEFAULT_COLOR_THEME = "blue" # "blue" | "green" | "dark-blue"

#—— Tailles des éléments UI ———————————————————————————————————————————————————————
ENTRY_HEIGHT = 38
BUTTON_HEIGHT_LG = 42 # Bouton principal
BUTTON_HEIGHT_MD = 32 # Bouton secondaires
BUTTON_HEIGHT_SM = 30 # Bouton mise à jour
BUTTON_WIDTH_SM = 100 # Bouton "Parcourir"
BUTTON_WIDTH_MD = 110 # Bouton toolbar
BUTTON_WIDTH_UPDATE = 220 # Bouton mise à jour
PROGRESS_HEIGHT = 8
FILE_ROW_HEIGHT = 36
THUMBNAIL_WIDTH = 160 # Miniature de la vidéo, onglet GIF
THUMBNAIL_HEIGHT = 90 # 160x90 : proportions 16/9

#—— Polices ————————————————————————————————————————————————————————————————————————
FONT_TITLE_SIZE = 18
FONT_BODY_SIZE = 13
FONT_SMALL_SIZE = 12
FONT_TINY_SIZE = 11

#—— Espacements ————————————————————————————————————————————————————————————————————
PAD_OUTER = 24 # Marges extérieures
PAD_INNER = 16 # Marges intérieures (cartes)
PAD_SECTION = 8 # Espacement entre sections
PAD_ITEM = 4 # Espacement entre éléments
PAD_TABS = 16 # Marges des onglets

#—— Divers —————————————————————————————————————————————————————————————————————————
SUCCESS_RESET_DELAY = 3000 # ms avant reset barre de progression
UPDATE_BTN_DELAY = 3000 # ms avant reset bouton "à jour"