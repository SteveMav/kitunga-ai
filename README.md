# Kitunga AI

Backend Django MVP pour un panier intelligent Fab Lab : detection IA, panier numerique, QR code de caisse, validation paiement demo et gestion de stock.

## Stack

- Django
- Django REST Framework
- SQLite
- Bootstrap
- qrcode

## Installation locale

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_data
.\.venv\Scripts\python.exe manage.py sync_model_catalog
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

## URLs utiles

- Dashboard : `http://127.0.0.1:8000/dashboard/`
- Admin : `http://127.0.0.1:8000/admin/`
- Ecran panier : `http://127.0.0.1:8000/basket-screen/SB-001/`
- API panier : `http://127.0.0.1:8000/api/baskets/SB-001/`

## API MVP

```http
POST /api/baskets/start/
GET /api/baskets/<code>/
POST /api/baskets/<code>/add-detection/
POST /api/baskets/<code>/remove-item/
POST /api/baskets/<code>/finish/
GET /checkout/t/<token>/
POST /checkout/t/<token>/validate/
```

Exemple de detection :

```json
{
  "device_id": "KITUNGA-PI-001",
  "detected_label": "arduino_uno",
  "confidence": 0.91
}
```

## Labels YOLO

Le modele ElectroCom-61 utilise des labels bruts comme `Servo-Motor`. Kitunga AI les convertit en labels simples Django comme `servo_motor`, puis cherche `Product.detection_label`.

Pour aligner la base avec le modele :

```powershell
.\.venv\Scripts\python.exe manage.py sync_model_catalog
```

Voir [docs/model_label_mapping.md](docs/model_label_mapping.md) pour les correspondances principales.

## QR code caisse sur telephone

Pour scanner le QR code avec un telephone, le lien ne doit pas etre en `127.0.0.1`, car ce localhost pointerait vers le telephone. Mets l'IP Wi-Fi du laptop dans `.env` :

```text
PUBLIC_BASE_URL=http://10.20.20.174:8000
```

Puis lance Django sur le reseau local :

```powershell
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Les nouveaux QR codes contiendront alors une URL du type `http://10.20.20.174:8000/checkout/t/.../`.

## Scenario de demo rapide

1. Lancer le serveur.
2. Creer une session avec `POST /api/baskets/start/`.
3. Ouvrir `/basket-screen/<code>/`.
4. Envoyer une detection reconnue.
5. Cliquer sur `Terminer le panier`.
6. Ouvrir le QR code ou le lien caisse.
7. Valider le paiement.
8. Verifier le stock dans Django Admin.

## Client camera / Raspberry Pi

Le dossier `kitunga_pi_client/` contient le client Python charge de capturer une image, lancer YOLO, puis envoyer la detection a Django.

Installation :

```powershell
cd kitunga_pi_client
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Placer le modele YOLO entraine dans :

```text
kitunga_pi_client/models/best.pt
```

Mode camera PC :

```powershell
.\.venv\Scripts\python.exe main.py --api-base-url http://127.0.0.1:8000 --basket-code SB-001 --camera-index 0
```

Mode image fixe, pratique pour tester sans camera :

```powershell
.\.venv\Scripts\python.exe main.py --test-image C:\chemin\image.jpg --once --no-send
```

Ecran client Tkinter pour demo PC/Raspberry :

```powershell
cd kitunga_pi_client
.\.venv\Scripts\python.exe tkinter_screen.py --api-base-url http://127.0.0.1:8000 --basket-code SB-001
```

Sur Raspberry Pi ou en reseau local :

```powershell
python tkinter_screen.py --api-base-url http://192.168.1.20:8000 --basket-code SB-001 --fullscreen
```

## Lancement sur Raspberry Pi

Les etapes completes sont dans [kitunga_pi_client/README.md](kitunga_pi_client/README.md), section `Etapes exactes sur Raspberry Pi`.

Sur le laptop, Django doit etre accessible depuis le reseau Wi-Fi :

```powershell
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Sur la Raspberry :

```bash
git clone https://github.com/SteveMav/kitunga-ai.git
cd kitunga-ai/kitunga_pi_client
bash scripts/install_pi.sh
nano .env
bash scripts/test_backend.sh
bash scripts/test_camera.sh
bash scripts/run_all.sh
```

Dans `.env`, `KITUNGA_API_BASE_URL` doit etre l'IP du laptop, pas `127.0.0.1`.

Le modele YOLO doit etre copie manuellement dans :

```text
kitunga_pi_client/models/best.pt
```

## Test camera telephone avec Iriun + Vite

Le dossier `camera_tester/` contient une petite app Vite pour utiliser Iriun Webcam comme camera navigateur, lancer YOLO en continu et afficher les boites de detection en overlay sur la video.

Lancer Django :

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Lancer Vite :

```powershell
cd camera_tester
npm install
npm run dev
```

Ouvrir :

```text
http://127.0.0.1:5174
```

En mode live, la page envoie des frames a Django, Django lance YOLO sur `kitunga_pi_client/models/best.pt`, puis Vite dessine les boites de detection sur la video. L'option `Ajouter automatiquement au panier` envoie les labels detectes au panier avec un cooldown pour eviter les doublons.

Pour que la detection fonctionne depuis Django, installer les dependances YOLO dans l'environnement racine :

```powershell
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Verifier que le modele existe :

```text
kitunga_pi_client/models/best.pt
```
