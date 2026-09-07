# Convertisor

![Version](https://img.shields.io/github/v/release/MGpro-grammer/convertisor)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Platform](https://img.shields.io/badge/Plateforme-Windows-lightgrey)

Application de bureau Windows qui télécharge une vidéo YouTube à partir de
son URL et l'enregistre en **MP3** ou en **MP4**.

---

## Fonctionnalités

- Téléchargement de l'audio d'une vidéo YouTube au format MP3 (192 kbit/s)
- Téléchargement d'une vidéo YouTube au format MP4, à la meilleure qualité disponible
- Choix du dossier de destination
- Gestion des fichiers téléchargés : liste et suppression
- Thème clair, sombre ou automatique, conservé d'une session à l'autre
- Mise à jour automatique depuis les releases du dépôt

À venir : export d'une plage de la vidéo en GIF animé.

---

## Installation

**L'installateur publié dans les releases est le seul canal de distribution
officiel.**

Téléchargez `Convertisor-Setup.exe` depuis la
[page des releases](https://github.com/MGpro-grammer/convertisor/releases)
et lancez-le. L'application s'installe avec un raccourci dans le menu
Démarrer, et sur le Bureau si vous cochez l'option correspondante.

Aucune dépendance n'est à installer : FFmpeg est inclus dans l'exécutable.

L'application vérifie au démarrage si une version plus récente est publiée,
et propose de l'installer le cas échéant.

---

## Emplacement des fichiers

| Élément | Emplacement |
|---|---|
| Préférences | `%APPDATA%\Convertisor\settings.json` |
| Fichiers téléchargés | `%USERPROFILE%\Downloads\Convertisor` |

En mode développement, les deux se trouvent à la racine du projet
(`settings.json` et `downloads/`).

---

## Développement

> Cette section s'adresse aux personnes qui souhaitent lire ou modifier le
> code source. Ce n'est **pas** une méthode d'installation : pour utiliser
> l'application, passez par l'installateur décrit plus haut.

### Prérequis

- Python 3.12
- Windows

### Mise en place

```powershell
git clone https://github.com/MGpro-grammer/convertisor.git
cd convertisor
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Lancement

```powershell
python main.py
```

---

## Structure du projet

```
convertisor/
├── assets/                  # Icônes de l'application
├── core/                    # Noyau : chemins, constantes, préférences, mises à jour
│   ├── config.py            # Emplacements des fichiers selon le mode d'exécution
│   ├── constants.py         # Dimensions, polices, espacements de l'interface
│   ├── ffmpeg.py            # Accès au binaire FFmpeg embarqué
│   ├── settings.py          # Lecture et écriture des préférences
│   └── updater.py           # Vérification et installation des mises à jour
├── gif/                     # Découpage et conversion en GIF (en développement)
├── mp3/                     # Téléchargement au format MP3
├── mp4/                     # Téléchargement au format MP4
├── ui/                      # Interface graphique (CustomTkinter)
│   ├── app.py               # Fenêtre principale et assemblage des onglets
│   ├── base_download_tab.py # Socle commun aux onglets de téléchargement
│   ├── player_frame.py      # Sélection d'une plage de la vidéo (en développement)
│   ├── tab_convert.py       # Onglet MP3
│   ├── tab_video.py         # Onglet MP4
│   ├── tab_gif.py           # Onglet GIF (en développement)
│   ├── tab_files.py         # Onglet Fichiers
│   └── tab_settings.py      # Onglet Paramètres
├── convert_icon.py          # Utilitaire : génère icon.ico à partir de icon.png
├── Convertisor.spec         # Configuration PyInstaller
├── installer.iss            # Configuration Inno Setup
├── main.py                  # Point d'entrée
├── requirements.txt
└── version.txt              # Source unique de la version
```

Les onglets MP3 et MP4 héritent de `BaseDownloadTab`, qui rassemble toute la
logique commune : champ d'URL, sélecteur de dossier, téléchargement en
arrière-plan, barre de progression et gestion des erreurs. Ajouter un format
revient à définir quelques attributs de classe et une méthode `download`.

---

## Construction

Le numéro de version est lu depuis `version.txt`, aussi bien par
l'application que par l'installateur. C'est le seul endroit à modifier avant
une nouvelle release.

**Exécutable** :

```powershell
pyinstaller Convertisor.spec
```

Produit `dist\Convertisor.exe`.

**Installateur** : ouvrez `installer.iss` dans
[Inno Setup](https://jrsoftware.org/isinfo.php) et lancez la compilation.
Produit `installer\Convertisor-Setup.exe`.

---

## Composants tiers

| Composant | Rôle | Licence |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Téléchargement depuis YouTube | Unlicense |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interface graphique | MIT |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | Fourniture du binaire FFmpeg | BSD-2-Clause |
| [FFmpeg](https://ffmpeg.org/) | Conversion audio et vidéo | GPL v3 |
| [Pillow](https://github.com/python-pillow/Pillow) | Génération de l'icône | MIT-CMU |
| [PyInstaller](https://pyinstaller.org/) | Création de l'exécutable | GPL v2 avec exception |

Le binaire FFmpeg redistribué est le build `essentials` de
[gyan.dev](https://www.gyan.dev/ffmpeg/builds/), compilé avec `--enable-gpl`
et `--enable-version3`, et donc placé sous **GPL v3**. Ses sources sont
disponibles auprès du [projet FFmpeg](https://ffmpeg.org/download.html).

---

## Auteur

Mouratidis Georges — [LinkedIn](https://www.linkedin.com/in/georges-mouratidis-a0b14a399/)