"""
Téléchargement en lot de vidéos YouTube au format MP3.

Les liens sont traités un par un, dans l'ordre du fichier d'origine.
L'échec de l'un d'eux — vidéo privée, supprimée, coupure réseau — est
enregistré puis le lot se poursuit : sur une liste de vingt titres, un
lien mort ne doit pas priver l'utilisateur des dix-neuf autres.

Le module ne connaît rien de l'interface : il signale son avancement
par un appel de fonction et consulte une fonction d'arrêt entre deux
liens. C'est à l'appelant de les relier à une barre de progression ou
à un bouton.
"""

from collections.abc import Callable, Sequence
import re
from dataclasses import dataclass
from pathlib import Path

from mp3.downloader import download_audio_as_mp3
from mp3.linkfile import DetectedLink

#: Longueur maximale d'un motif d'échec conservé dans le rapport.
_MAX_REASON_LENGTH = 200
#: Séquences de couleur ANSI, que yt-dlp insère dans ses messages
#: d'erreur lorsqu'il croit écrire vers un terminal.
_ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True)
class FailedDownload:
    """
    Lien dont le téléchargement a échoué.

    :param link: Le lien concerné, avec son numéro de ligne d'origine.
    :param reason: Motif de l'échec, abrégé pour rester lisible.
    """

    link: DetectedLink
    reason: str


@dataclass(frozen=True)
class BatchResult:
    """
    Bilan d'un téléchargement en lot.

    :param succeeded: Liens téléchargés avec succès.
    :param failed: Liens en échec, avec leur motif.
    :param stopped: Vrai si l'utilisateur a interrompu le lot ; les
        liens non traités n'apparaissent alors dans aucune des deux
        listes.
    """

    succeeded: list[DetectedLink]
    failed: list[FailedDownload]
    stopped: bool = False

    @property
    def processed(self) -> int:
        """Nombre de liens effectivement traités."""
        return len(self.succeeded) + len(self.failed)


def _short_reason(error: Exception) -> str:
    """
    Résume une exception en un message présentable.

    yt-dlp produit des messages longs, parfois sur plusieurs lignes et
    préfixés de « ERROR: ». Seule la dernière ligne porte l'information
    utile.

    :param error: Exception rencontrée.
    :return: Un motif court, sur une seule ligne.
    """
    text = _ANSI_PATTERN.sub("", str(error)).strip()
    if not text:
        return type(error).__name__

    reason = text.splitlines()[-1].strip()
    reason = reason.removeprefix("ERROR:").strip()
    if len(reason) > _MAX_REASON_LENGTH:
        reason = reason[:_MAX_REASON_LENGTH].rstrip() + "..."
    return reason


def download_links_as_mp3(
    links: Sequence[DetectedLink],
    output_dir: Path,
    on_progress: Callable[[int, int, DetectedLink], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> BatchResult:
    """
    Télécharge une série de vidéos YouTube au format MP3.

    :param links: Liens à traiter, dans l'ordre souhaité.
    :param output_dir: Dossier de destination, créé s'il n'existe pas.
    :param on_progress: Appelée avant chaque lien avec le rang (à
        partir de 1), le total et le lien traité.
    :param should_stop: Consultée entre deux liens ; si elle retourne
        vrai, le lot s'arrête proprement. Le téléchargement en cours
        n'est jamais interrompu en plein milieu, ce qui éviterait un
        fichier incomplet sur le disque.
    :return: Le bilan du lot.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    succeeded: list[DetectedLink] = []
    failed: list[FailedDownload] = []
    total = len(links)

    for index, link in enumerate(links, start=1):
        if should_stop is not None and should_stop():
            return BatchResult(succeeded=succeeded, failed=failed, stopped=True)

        if on_progress is not None:
            on_progress(index, total, link)

        try:
            download_audio_as_mp3(link.url, output_dir)
        except Exception as error:
            # Volontairement large : aucun lien ne doit pouvoir
            # interrompre le reste du lot.
            failed.append(FailedDownload(link=link, reason=_short_reason(error)))
        else:
            succeeded.append(link)

    return BatchResult(succeeded=succeeded, failed=failed, stopped=False)