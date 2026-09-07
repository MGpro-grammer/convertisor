"""
Configuration commune des téléchargements yt-dlp.

Trois réglages doivent accompagner chaque appel à yt-dlp, et les
oublier au premier endroit venu produit des pannes difficiles à
diagnostiquer :

- l'emplacement de FFmpeg, qui n'est pas installé sur la machine de
  l'utilisateur mais embarqué dans l'application ;
- l'emplacement du moteur JavaScript, nécessaire depuis que YouTube
  exige la résolution d'un défi cryptographique pour servir certaines
  vidéos. Sans lui, le téléchargement échoue avec une erreur 403 ;
- l'autorisation de récupérer le solveur externe qui tourne dans ce
  moteur, publié par l'équipe yt-dlp.

Ce module rassemble ces réglages en un point unique.
"""

import shutil
from functools import lru_cache

from core.config import BASE_DIR, IS_FROZEN, RESOURCE_DIR
from core.ffmpeg import get_ffmpeg_path

#—— Moteur JavaScript embarqué ————————————————————————————————————————————————————
DENO_FILENAME = "deno.exe"

# Dossier où le binaire est rangé en développement. Il n'est pas
# versionné : voir la section « Construction » du README.
VENDOR_DIR = BASE_DIR / "vendor"


@lru_cache(maxsize=1)
def get_deno_path() -> str | None:
    """
    Retourne le chemin du moteur JavaScript Deno, ou ``None``.

    L'exécutable embarqué est cherché en premier : dans les ressources
    extraites en mode exécutable, dans ``vendor/`` en développement. À
    défaut, un Deno installé sur la machine et présent dans le PATH
    fait l'affaire.

    :return: Chemin absolu du binaire, ou ``None`` si aucun moteur
        n'est disponible — auquel cas certaines vidéos resteront
        inaccessibles.
    """
    root = RESOURCE_DIR if IS_FROZEN else VENDOR_DIR
    embedded = root / DENO_FILENAME
    if embedded.is_file():
        return str(embedded)
    return shutil.which("deno")


def base_options() -> dict:
    """
    Retourne les options yt-dlp communes à tous les téléchargements.

    À fusionner avec les options propres à chaque usage :
    ``{**base_options(), "format": ...}``.

    ``quiet`` et ``no_warnings`` ne sont pas de simples préférences :
    l'application est compilée sans console, donc ``sys.stdout`` vaut
    ``None``. Une bibliothèque qui tenterait d'y écrire ferait échouer
    le téléchargement.

    :return: Un dictionnaire d'options, nouveau à chaque appel.
    """
    options = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": get_ffmpeg_path(),
        # Autorise le téléchargement du solveur de défis JavaScript
        # depuis le dépôt officiel yt-dlp/ejs. Sans cette option,
        # yt-dlp dispose du moteur mais pas du programme à exécuter.
        "remote_components": ["ejs:github"],
    }

    deno = get_deno_path()
    if deno:
        options["js_runtimes"] = {"deno": {"path": deno}}

    return options