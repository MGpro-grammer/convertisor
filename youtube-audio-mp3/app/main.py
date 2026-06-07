from .downloader import download_audio_as_mp3

def main():
    url = input("Entrez l'URL de la vidéo YouTube : ").strip()

    try:
        download_audio_as_mp3(url)
        print("Téléchargement terminé avec succès !")
    except ValueError as ve:
        print(f"Erreur de validation : {ve}")
    except Exception as exc:
        print(f"Une erreur est survenue : {exc}")

if __name__ == "__main__":
    main()