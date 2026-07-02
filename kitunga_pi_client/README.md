# Kitunga Pi Client

Client Python pour envoyer les detections camera/YOLO au backend Django Kitunga AI.

## Installation

```powershell
cd kitunga_pi_client
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Sur Raspberry Pi, `opencv-python` peut etre remplace par le paquet OpenCV recommande pour l'OS si l'installation pip est trop lourde.

## Mode camera PC

Depuis le dossier `kitunga_pi_client` :

```powershell
.\.venv\Scripts\python.exe main.py --api-base-url http://127.0.0.1:8000 --basket-code SB-001 --camera-index 0
```

## Mode image fixe

```powershell
.\.venv\Scripts\python.exe main.py --test-image C:\chemin\image.jpg --once --no-send
```

Enleve `--no-send` pour envoyer la detection au backend.

## Mode reseau local

Quand Django tourne sur ton laptop :

```powershell
python manage.py runserver 0.0.0.0:8000
```

Puis lance le client avec l'IP du laptop :

```powershell
python main.py --api-base-url http://192.168.1.20:8000 --basket-code SB-001
```

## Modele YOLO

Place ton modele entraine ici :

```text
kitunga_pi_client/models/best.pt
```

Le fichier `.pt` est ignore par Git pour eviter de pousser un gros modele dans le repo.
