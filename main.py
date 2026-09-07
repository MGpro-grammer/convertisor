"""
Point d'entrée de l'application Convertisor.

Lance l'interface graphique. C'est ce module que PyInstaller prend
comme script d'analyse (voir Convertisor.spec).

Utilisation en développement, depuis la racine du projet :

    python main.py
"""

from ui import App


def main() -> None:
    """Crée la fenêtre principale et démarre la boucle d'événements."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()