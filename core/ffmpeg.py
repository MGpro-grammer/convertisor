"""
Accès au binaire FFmpeg utilisé par les modules de téléchargement.

FFmpeg est fourni par le paquet ``imageio-ffmpeg``, qui embarque un
binaire statique. Le passer explicitement à yt-dlp via l'option
``ffmpeg_location`` évite de dépendre d'une installation système, que
l'utilisateur final n'a pas forcément.
"""

from functools import lru_cache

import imageio_ffmpeg


@lru_cache(maxsize=1)
def get_ffmpeg_path() -> str:
    """
    Retourne le chemin absolu du binaire FFmpeg embarqué.

    Le résultat est mis en cache : la résolution du chemin par
    imageio-ffmpeg est identique pendant toute la durée de vie du
    processus et n'a pas besoin d'être refaite à chaque téléchargement.
    """
    return imageio_ffmpeg.get_ffmpeg_exe()