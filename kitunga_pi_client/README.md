# Kitunga Pi Client

Client Python pour envoyer les detections camera/YOLO au backend Django Kitunga AI.

## Architecture Raspberry Pi

Sur la Raspberry, le client lance deux processus :

- `main.py` : capture camera, detection YOLO, envoi des labels au backend Django.
- `tkinter_screen.py` : ecran client, panier, total et QR code.

Les deux processus partagent le panier actif via :

```text
state/basket_code.txt
```

Quand l'ecran cree une nouvelle session, il ecrit le nouveau code panier dans ce fichier. Le detecteur le relit avant chaque envoi pour eviter d'envoyer les detections vers un ancien panier.

## Installation

```powershell
cd kitunga_pi_client
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Sur Raspberry Pi, `opencv-python` peut etre remplace par le paquet OpenCV recommande pour l'OS si l'installation pip est trop lourde.

## Installation sur Raspberry Pi

Depuis la Raspberry :

```bash
git clone https://github.com/SteveMav/kitunga-ai.git
cd kitunga-ai/kitunga_pi_client
bash scripts/install_pi.sh
```

Ensuite edite `.env` :

```bash
nano .env
```

Mets l'IP du laptop qui lance Django :

```text
KITUNGA_API_BASE_URL=http://10.20.20.174:8000
KITUNGA_DEVICE_ID=KITUNGA-PI-001
KITUNGA_BASKET_CODE=SB-001
KITUNGA_CAMERA_INDEX=0
```

Copie le modele YOLO ici :

```text
kitunga_pi_client/models/best.pt
```

Le fichier `best.pt` n'est pas pousse dans Git, car il peut etre lourd.

Avant de lancer la Raspberry, le laptop doit demarrer Django sur le reseau local :

```powershell
python manage.py runserver 0.0.0.0:8000
```

Teste d'abord la connexion backend :

```bash
bash scripts/test_backend.sh
```

Teste ensuite la camera et le modele sans envoyer au backend :

```bash
bash scripts/test_camera.sh
```

Lance la demo complete :

```bash
bash scripts/run_all.sh
```

Pour lancer les deux parties separement :

```bash
bash scripts/run_detector.sh
bash scripts/run_screen.sh
```

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

## Ecran client Tkinter

Cette petite app remplace l'ecran web du panier pour une demo PC/Raspberry. Elle affiche le panier, les objets detectes, le total, puis le QR code apres finalisation.

Depuis le dossier `kitunga_pi_client` :

```powershell
.\.venv\Scripts\python.exe tkinter_screen.py --api-base-url http://127.0.0.1:8000 --basket-code SB-001
```

En mode kiosk sur Raspberry Pi :

```powershell
python tkinter_screen.py --api-base-url http://192.168.1.20:8000 --basket-code SB-001 --fullscreen
```

Tu peux appuyer sur `Echap` pour sortir du plein ecran.

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

Les labels du modele sont normalises avant envoi au backend. Exemple : `Servo-Motor` devient `servo_motor`, ce qui correspond a `Product.detection_label`.
