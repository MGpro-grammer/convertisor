# Convertisor

![Version](https://img.shields.io/github/v/release/MGpro-grammer/convertisor)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Platform](https://img.shields.io/badge/Plateforme-Windows-lightgrey)

Application de bureau Windows qui télécharge une vidéo YouTube à partir de
son URL et l'enregistre en **MP3**, en **MP4**, ou en **GIF animé**.

---

## Fonctionnalités

- Téléchargement de l'audio d'une vidéo YouTube au format MP3 (192 kbit/s)
- Téléchargement d'une vidéo YouTube au format MP4, à la meilleure qualité disponible
- Conversion d'un extrait de vidéo en GIF animé, avec choix de la plage, du nombre d'images par seconde et de la largeur
- Choix du dossier de destination
- Gestion des fichiers téléchargés : liste et suppression
- Thème clair, sombre ou automatique, conservé d'une session à l'autre
- Mise à jour automatique depuis les releases du dépôt

---

## Installation

**L'installateur publié dans les releases est le seul canal de distribution
officiel.**

Téléchargez `Convertisor-Setup.exe` depuis la
[page des releases](https://github.com/MGpro-grammer/convertisor/releases)
et lancez-le. L'application s'installe avec un raccourci dans le menu
Démarrer, et sur le Bureau si vous cochez l'option correspondante.

Aucune dépendance n'est à installer : FFmpeg et le moteur JavaScript
nécessaire aux téléchargements sont inclus.

L'application vérifie au démarrage si une version plus récente est publiée,
et propose de l'installer le cas échéant.

---

## Créer un GIF

Collez l'URL puis cliquez sur **Analyser la vidéo** : le titre, la durée et
la miniature s'affichent. Indiquez ensuite les bornes de l'extrait au format
`mm:ss`, relevées sur YouTube, et ajustez si besoin le nombre d'images par
seconde et la largeur. Le poids estimé se met à jour à chaque modification.

Un extrait est limité à 30 secondes : au-delà, le fichier devient trop lourd
pour l'usage auquel un GIF est destiné.

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
- [Deno](https://deno.com/) 2.3 ou supérieur

Deno est indispensable. YouTube exige la résolution d'un défi JavaScript
pour servir une partie de ses vidéos ; sans moteur pour l'exécuter, les
téléchargements échouent avec une erreur `HTTP 403 Forbidden`.

```powershell
winget install DenoLand.Deno
```

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

En développement, l'application utilise le Deno présent dans le `PATH`.
Pour compiler l'exécutable, il faut en revanche en placer une copie dans le
projet — voir la section Construction.

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
│   ├── timecode.py          # Conversion entre secondes et « mm:ss »
│   ├── updater.py           # Vérification et installation des mises à jour
│   ├── youtube.py           # Métadonnées d'une vidéo, sans téléchargement
│   └── ytdlp.py             # Options communes à tous les téléchargements
├── gif/                     # Découpage et conversion en GIF
├── mp3/                     # Téléchargement au format MP3
├── mp4/                     # Téléchargement au format MP4
├── ui/                      # Interface graphique (CustomTkinter)
│   ├── app.py               # Fenêtre principale et assemblage des onglets
│   ├── base_download_tab.py # Socle commun aux onglets de téléchargement
│   ├── player_frame.py      # Sélection d'une plage de la vidéo
│   ├── tab_convert.py       # Onglet MP3
│   ├── tab_video.py         # Onglet MP4
│   ├── tab_gif.py           # Onglet GIF
│   ├── tab_files.py         # Onglet Fichiers
│   └── tab_settings.py      # Onglet Paramètres
├── vendor/                  # Binaires embarqués, non versionnés (voir Construction)
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

`core/ytdlp.py` centralise la configuration passée à yt-dlp — emplacement de
FFmpeg, emplacement de Deno, autorisation du solveur externe. Tout module
qui télécharge doit partir de `base_options()`.

---

## Construction

Le numéro de version est lu depuis `version.txt`, aussi bien par
l'application que par l'installateur. C'est le seul endroit à modifier avant
une nouvelle release.

### Binaires embarqués

`vendor/` n'est pas versionné : un exécutable de 93 Mo resterait
définitivement dans l'historique du dépôt. Il faut donc l'alimenter avant la
première compilation :

```powershell
mkdir vendor
Copy-Item (Get-Command deno).Source .\vendor\deno.exe
```

FFmpeg, lui, provient du paquet `imageio-ffmpeg` et est embarqué
automatiquement.

### Exécutable

```powershell
pyinstaller Convertisor.spec
```

Produit le dossier `dist\Convertisor\`, d'environ 220 Mo.

Le mode **onedir** est délibéré : avec 180 Mo de binaires, un exécutable
unique devrait tout décompresser à chaque lancement, imposant plusieurs
secondes d'attente à chaque ouverture.

### Installateur

Ouvrez `installer.iss` dans [Inno Setup](https://jrsoftware.org/isinfo.php)
et lancez la compilation. Produit `installer\Convertisor-Setup.exe`.

---

## Composants tiers

| Composant | Rôle | Licence |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Téléchargement depuis YouTube | Unlicense |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interface graphique | MIT |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | Fourniture du binaire FFmpeg | BSD-2-Clause |
| [FFmpeg](https://ffmpeg.org/) | Conversion audio et vidéo | GPL v3 |
| [Deno](https://deno.com/) | Moteur JavaScript pour les défis YouTube | MIT |
| [Pillow](https://github.com/python-pillow/Pillow) | Génération de l'icône | MIT-CMU |
| [PyInstaller](https://pyinstaller.org/) | Création de l'exécutable | GPL v2 avec exception |

Le binaire FFmpeg redistribué est le build `essentials` de
[gyan.dev](https://www.gyan.dev/ffmpeg/builds/), compilé avec `--enable-gpl`
et `--enable-version3`, et donc placé sous **GPL v3**. Ses sources sont
disponibles auprès du [projet FFmpeg](https://ffmpeg.org/download.html).

L'application autorise par ailleurs yt-dlp à télécharger, au besoin, le
solveur de défis JavaScript publié dans le dépôt
[yt-dlp/ejs](https://github.com/yt-dlp/ejs). Ce code est récupéré depuis le
dépôt officiel de yt-dlp et exécuté dans le bac à sable de Deno.

---

## Auteur

Mouratidis Georges — [LinkedIn](https://www.linkedin.com/in/georges-mouratidis-a0b14a399/)