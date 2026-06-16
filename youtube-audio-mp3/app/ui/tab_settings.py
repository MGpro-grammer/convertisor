import customtkinter as ctk
from ..constants import (
    FONT_TITLE_SIZE, FONT_BODY_SIZE, PAD_SECTION, PAD_INNER
)
from ..settings import save_settings


class TabSettings(ctk.CTkFrame):
    def __init__(self, parent, settings: dict, on_appearance_change):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.on_appearance_change = on_appearance_change
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text="⚙ Paramètres",
            font=ctk.CTkFont(size=FONT_TITLE_SIZE, weight="bold")
        ).grid(row=0, column=0, pady=(PAD_SECTION, PAD_INNER), sticky="w")

        # ── Section Apparence ──────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="APPARENCE",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=1, column=0, pady=(0, PAD_SECTION // 2), sticky="w")

        appearance_card = ctk.CTkFrame(self)
        appearance_card.grid(row=2, column=0, pady=(0, PAD_INNER), sticky="ew")
        appearance_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            appearance_card,
            text="Thème de l'application",
            font=ctk.CTkFont(size=FONT_BODY_SIZE),
            anchor="w"
        ).grid(row=0, column=0, padx=PAD_INNER, pady=PAD_INNER, sticky="w")

        self.appearance_var = ctk.StringVar(
            value=self.settings.get("appearance_mode", "Dark")
        )
        ctk.CTkSegmentedButton(
            appearance_card,
            values=["Light", "Dark", "System"],
            variable=self.appearance_var,
            command=self._on_appearance_change
        ).grid(row=0, column=1, padx=PAD_INNER, pady=PAD_INNER)

        # ── Section Suppressions ───────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="SUPPRESSIONS",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).grid(row=3, column=0, pady=(0, PAD_SECTION // 2), sticky="w")

        delete_card = ctk.CTkFrame(self)
        delete_card.grid(row=4, column=0, pady=(0, PAD_INNER), sticky="ew")
        delete_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            delete_card,
            text="Demander confirmation avant de supprimer un fichier",
            font=ctk.CTkFont(size=FONT_BODY_SIZE),
            anchor="w"
        ).grid(row=0, column=0, padx=PAD_INNER, pady=PAD_INNER, sticky="w")

        self.confirm_var = ctk.BooleanVar(
            value=self.settings.get("confirm_delete", True)
        )
        ctk.CTkSwitch(
            delete_card,
            text="",
            variable=self.confirm_var,
            command=self._save
        ).grid(row=0, column=1, padx=PAD_INNER, pady=PAD_INNER)

    def _on_appearance_change(self, value: str):
        ctk.set_appearance_mode(value)
        self.settings["appearance_mode"] = value
        save_settings(self.settings)
        if self.on_appearance_change:
            self.on_appearance_change(value)

    def _save(self):
        self.settings["confirm_delete"] = self.confirm_var.get()
        save_settings(self.settings)