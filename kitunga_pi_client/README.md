# Kitunga Pi Client

Client Python pour envoyer les detections camera/YOLO au backend Django Kitunga AI.

## Etapes exactes sur Raspberry Pi

Ces etapes sont le chemin recommande pour installer et lancer la demo sur une Raspberry Pi fraiche.

### 1. Demarrer le backend sur le laptop

Sur le laptop, dans le repo Django :

```powershell
cd "C:\dev\makers\kitunga ai\kitunga-AI"
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Note l'IP Wi-Fi du laptop. Exemple :

```text
10.20.20.174
```

Dans le `.env` du backend, `PUBLIC_BASE_URL` doit utiliser cette IP pour que le QR code soit scannable depuis un telephone :

```text
PUBLIC_BASE_URL=http://10.20.20.174:8000
```

### 2. Cloner le projet sur la Raspberry

Si la branche Raspberry n'est pas encore mergee dans `main` :

```bash
git clone -b codex/raspberry-client https://github.com/SteveMav/kitunga-ai.git
```

Si elle est deja mergee :

```bash
git clone https://github.com/SteveMav/kitunga-ai.git
```

Puis :

```bash
cd kitunga-ai/kitunga_pi_client
```

### 3. Installer les dependances Raspberry

```bash
bash scripts/install_pi.sh
```

Ce script installe les paquets systeme utiles, cree `.venv`, installe les packages Python et cree `.env` si necessaire.

### 4. Configurer la Raspberry

Edite le fichier `.env` :

```bash
nano .env
```

Exemple de configuration :

```text
KITUNGA_API_BASE_URL=http://10.20.20.174:8000
KITUNGA_DEVICE_ID=KITUNGA-PI-001
KITUNGA_BASKET_CODE=SB-001
KITUNGA_CAMERA_INDEX=0
KITUNGA_CONFIDENCE_THRESHOLD=0.75
KITUNGA_COOLDOWN_SECONDS=4
KITUNGA_SCAN_INTERVAL_SECONDS=2
```

Important : `KITUNGA_API_BASE_URL` doit etre l'IP du laptop, pas `127.0.0.1`.

### 5. Copier le modele YOLO

Le modele n'est pas dans Git. Copie-le ici sur la Raspberry :

```text
kitunga_pi_client/models/best.pt
```

Depuis le dossier `kitunga_pi_client`, le fichier doit donc exister ici :

```bash
ls -lh models/best.pt
```

### 6. Tester la connexion backend

```bash
bash scripts/test_backend.sh
```

Si cette commande echoue, corrige d'abord :

- l'IP dans `KITUNGA_API_BASE_URL` ;
- le Wi-Fi ;
- le firewall du laptop ;
- le lancement Django en `0.0.0.0:8000`.

### 7. Tester camera + YOLO sans envoyer au panier

```bash
bash scripts/test_camera.sh
```

Si la camera ne s'ouvre pas, essaie un autre index :

```bash
bash scripts/test_camera.sh --camera-index 1
```

Si le modele manque, verifie `models/best.pt`.

### 8. Lancer la demo complete

```bash
bash scripts/run_all.sh
```

Ce script lance :

- le detecteur YOLO ;
- l'ecran client Tkinter en plein ecran ;
- les logs dans `logs/detector.log` et `logs/screen.log`.

Pour quitter l'ecran plein ecran, appuie sur `Echap`.

### 9. Lancer les processus separement si besoin

Terminal 1 :

```bash
bash scripts/run_detector.sh
```

Terminal 2 :

```bash
bash scripts/run_screen.sh
```

### 10. Verifier les logs

```bash
tail -f logs/detector.log
tail -f logs/screen.log
```

Le detecteur lit le panier actif depuis :

```text
state/basket_code.txt
```

Quand l'ecran cree une nouvelle session, ce fichier est mis a jour automatiquement.

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
