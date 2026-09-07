"""
Interface graphique de l'application, construite avec CustomTkinter.

La fenêtre principale :class:`App` assemble quatre onglets, chacun
défini dans son propre module ``tab_*``.
"""

from .app import App

__all__ = ["App"]