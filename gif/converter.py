"""
Conversion d'un extrait de vidéo YouTube en image animée GIF.

Le traitement se déroule en deux temps :

1. yt-dlp télécharge la vidéo dans un dossier temporaire. Seul le flux
   vidéo est récupéré — un GIF n'a pas de son — et la résolution est
   plafonnée : inutile de rapatrier de la 4K pour produire une image de
   480 pixels de large.
2. FFmpeg extrait la plage demandée et la convertit en GIF, en deux
   passes. La première calcule une palette de 256 couleurs adaptée aux
   images concernées, la seconde l'applique. Une passe unique donnerait
   une palette générique et un résultat visiblement dégradé.

Le découpage est confié à FFmpeg sur un fichier local, et non à
l'option ``download_ranges`` de yt-dlp : celle-ci délègue à FFmpeg le
téléchargement depuis les serveurs de YouTube, qui refuse ses requêtes
avec une erreur 403.

Les fichiers intermédiaires vivent dans un dossier temporaire, supprimé
à la fin quel que soit le déroulement.
"""

import subprocess
import tempfile
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import sanitize_filename

from core.ffmpeg import get_ffmpeg_path
from core.ytdlp import base_options

#—— Réglages par défaut ———————————————————————————————————————————————————————————
DEFAULT_FPS = 12
DEFAULT_WIDTH = 480

#—— Bornes acceptées ——————————————————————————————————————————————————————————————
MIN_DURATION = 0.5
MAX_DURATION = 30.0
FPS_CHOICES = (8, 10, 12, 15, 20, 25)
WIDTH_CHOICES = (240, 320, 480, 640, 800)

# Hauteur maximale du flux source téléchargé. Au-delà, on paierait du
# téléchargement pour des pixels que la réduction jettera de toute façon.
MAX_SOURCE_HEIGHT = 720

# Poids approximatif d'un pixel encodé, en octets. Valeur empirique :
# le poids réel varie fortement selon le mouvement à l'image.
_BYTES_PER_PIXEL = 0.3

# Empêche l'ouverture d'une fenêtre console à chaque appel de FFmpeg.
# L'attribut n'existe que sous Windows.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def estimate_size_mb(duration: float, fps: int, width: int) -> float:
    """
    Estime le poids du GIF produit, en mégaoctets.

    L'estimation suppose un format 16/9 et une compression moyenne.
    Elle donne un ordre de grandeur, pas une valeur exacte : une scène
    très animée peut dépasser le double, un plan fixe tomber sous la
    moitié.

    :param duration: Durée de l'extrait, en secondes.
    :param fps: Images par seconde.
    :param width: Largeur en pixels.
    :return: Poids approximatif en mégaoctets.
    """
    height = width * 9 / 16
    frames = duration * fps
    return frames * width * height * _BYTES_PER_PIXEL / (1024 * 1024)


def _run_ffmpeg(arguments: list[str]) -> None:
    """
    Exécute FFmpeg avec les arguments donnés.

    :param arguments: Arguments passés à FFmpeg, sans le binaire lui-même.
    :raises RuntimeError: Si FFmpeg se termine sur un code d'erreur ;
        le message reprend les dernières lignes de sa sortie d'erreur.
    """
    result = subprocess.run(
        [get_ffmpeg_path(), *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_NO_WINDOW,
    )
    if result.returncode != 0:
        details = "\n".join((result.stderr or "").strip().splitlines()[-5:])
        raise RuntimeError(f"FFmpeg a échoué :\n{details}")


def _download_video(url: str, work_dir: Path) -> tuple[Path, str]:
    """
    Télécharge le flux vidéo dans un dossier de travail.

    Le nom de sortie est fixé à « source » plutôt qu'au titre de la
    vidéo : le fichier produit est ainsi retrouvé sans dépendre du
    nommage de yt-dlp.

    :param url: URL de la vidéo YouTube.
    :param work_dir: Dossier de travail temporaire.
    :return: Le fichier téléchargé et le titre de la vidéo.
    :raises RuntimeError: Si le téléchargement ne produit aucun fichier.
    :raises yt_dlp.utils.DownloadError: URL invalide, vidéo
        indisponible, ou absence de connexion réseau.
    """
    options = {
        **base_options(),
        "format": (
            f"bestvideo[height<=?{MAX_SOURCE_HEIGHT}]"
            f"/best[height<=?{MAX_SOURCE_HEIGHT}]"
            "/best"
        ),
        "outtmpl": str(work_dir / "source.%(ext)s"),
    }

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

    produced = sorted(
        work_dir.glob("source.*"),
        key=lambda path: path.stat().st_size,
        reverse=True,
    )
    if not produced:
        raise RuntimeError("Le téléchargement n'a produit aucun fichier.")

    return produced[0], (info.get("title") or "video")


def _unique_path(directory: Path, stem: str, suffix: str) -> Path:
    """
    Construit un chemin libre dans le dossier donné.

    Si « nom.gif » existe déjà, renvoie « nom (2).gif », puis
    « nom (3).gif », et ainsi de suite.

    :param directory: Dossier de destination.
    :param stem: Nom du fichier, sans extension.
    :param suffix: Extension, point compris.
    :return: Un chemin qui n'existe pas encore.
    """
    candidate = directory / f"{stem}{suffix}"
    index = 2
    while candidate.exists():
        candidate = directory / f"{stem} ({index}){suffix}"
        index += 1
    return candidate


def convert_youtube_to_gif(
    url: str,
    output_dir: Path,
    start: float,
    end: float,
    fps: int = DEFAULT_FPS,
    width: int = DEFAULT_WIDTH,
    on_progress=None,
) -> Path:
    """
    Télécharge une vidéo YouTube et convertit un extrait en GIF.

    :param url: URL de la vidéo YouTube.
    :param output_dir: Dossier de destination, créé s'il n'existe pas.
    :param start: Début de l'extrait, en secondes.
    :param end: Fin de l'extrait, en secondes.
    :param fps: Images par seconde du GIF produit.
    :param width: Largeur en pixels ; la hauteur suit les proportions.
    :param on_progress: Fonction optionnelle appelée avec un message
        d'avancement (str), pour informer l'interface.
    :return: Le chemin du GIF produit.
    :raises ValueError: Si la plage demandée est trop courte, inversée,
        ou plus longue que :data:`MAX_DURATION`.
    :raises RuntimeError: Si le téléchargement ou FFmpeg échoue.
    """
    duration = end - start
    if duration < MIN_DURATION:
        raise ValueError(
            f"L'extrait doit durer au moins {MIN_DURATION:g} seconde."
        )
    if duration > MAX_DURATION:
        raise ValueError(
            f"L'extrait ne peut pas dépasser {MAX_DURATION:g} secondes "
            f"(demandé : {duration:.1f} s)."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    def notify(message: str) -> None:
        if on_progress:
            on_progress(message)

    with tempfile.TemporaryDirectory(prefix="convertisor-gif-") as temp_name:
        work_dir = Path(temp_name)

        notify("Téléchargement de la vidéo...")
        source, title = _download_video(url, work_dir)

        palette = work_dir / "palette.png"
        video_filter = f"fps={fps},scale={width}:-1:flags=lanczos"

        # « -ss » puis « -t » en options d'entrée : FFmpeg se place au
        # début de l'extrait et n'en décode que la durée demandée.
        trim = ["-ss", f"{start:.3f}", "-t", f"{duration:.3f}"]

        notify("Calcul de la palette de couleurs...")
        _run_ffmpeg([
            "-y",
            *trim,
            "-i", str(source),
            "-vf", f"{video_filter},palettegen=stats_mode=diff",
            str(palette),
        ])

        destination = _unique_path(output_dir, sanitize_filename(title), ".gif")

        notify("Création du GIF...")
        _run_ffmpeg([
            "-y",
            *trim,
            "-i", str(source),
            "-i", str(palette),
            "-lavfi",
            f"{video_filter}[x];[x][1:v]paletteuse="
            "dither=bayer:bayer_scale=5:diff_mode=rectangle",
            "-loop", "0",
            str(destination),
        ])

    return destination