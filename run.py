import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.constants import DEFAULT_APPEARANCE, DEFAULT_COLOR_THEME
import customtkinter as ctk

ctk.set_appearance_mode(DEFAULT_APPEARANCE)
ctk.set_default_color_theme(DEFAULT_COLOR_THEME)

from ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()