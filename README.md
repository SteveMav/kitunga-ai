# Kitunga AI

Kitunga AI est un MVP Django pour un panier intelligent de Fab Lab.

Le systeme permet de recevoir les detections d'objets depuis une Raspberry Pi,
d'ajouter automatiquement les produits dans un panier numerique, de calculer le
total, de generer un QR code de caisse, puis de valider la transaction avec mise
a jour du stock.

## Architecture cible

Le projet est separe en deux roles.

### PC backend / caisse

Le PC lance Django. Il gere :

- la base de donnees SQLite ;
- les produits, prix fictifs et stocks ;
- les sessions panier ;
- l'API REST recue par la Raspberry Pi ;
- la generation du QR code ;
- la page caisse ;
- le dashboard ;
- Django Admin.

Le PC ne lance pas la camera et ne lance pas YOLO dans l'architecture finale.
Il recoit uniquement un label et une confidence envoyes par la Raspberry Pi.

### Raspberry Pi

La Raspberry Pi gere :

- la camera CSI ou USB ;
- le modele YOLO local ;
- l'interface client Vite ou l'ecran de demo ;
- l'envoi HTTP/REST vers Django.

Elle ne se connecte jamais directement a la base de donnees. Elle appelle
Django avec du JSON.

## Structure du repo

```text
kitunga-AI/
+-- baskets/              # Sessions panier, items, API panier, services
+-- checkout/             # Caisse, validation paiement, ticket
+-- config/               # Settings Django, URLs racine
+-- dashboard/            # Dashboard simple
+-- detections/           # Detection live/demo et catalogue de labels
+-- products/             # Produits Fab Lab, admin, seed demo
+-- templates/            # Pages HTML Django
+-- static/               # CSS/JS/assets Django
+-- media/                # QR codes generes en local
+-- camera_tester/        # App Vite de test camera navigateur/Iriun
+-- kitunga_pi_client/    # Client Python Raspberry Pi
+-- requirements.txt
+-- .env.example
+-- manage.py
```

## Stack

- Django
- Django REST Framework
- SQLite
- Bootstrap
- qrcode
- OpenCV et Ultralytics YOLO cote Raspberry/client
- Vite cote interface Raspberry ou test camera navigateur

## Installation backend sur le PC

Ces commandes se lancent depuis le dossier racine du repo Django.

```powershell
cd "C:\dev\makers\kitunga ai\kitunga-AI"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_data
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Pour lancer le backend sur le reseau local :

```powershell
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Pour le mode demo sans double processus Django :

```powershell
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000 --noreload
```

## Configuration `.env` du backend

Exemple generique :

```env
SECRET_KEY=django-insecure-kitunga-ai-local-demo
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0,192.168.1.20,*
PUBLIC_BASE_URL=http://192.168.1.20:8000
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5174,http://localhost:5174,http://192.168.1.20:8000,http://RASPBERRY_IP:5174
TIME_ZONE=Africa/Kinshasa
```

Remplace `192.168.1.20` par l'IP Wi-Fi du PC.

Dans la demo actuelle, le PC etait accessible sur :

```text
http://10.20.20.158:8000
```

Donc la Raspberry devait utiliser :

```env
VITE_DJANGO_TARGET=http://10.20.20.158:8000
KITUNGA_API_BASE_URL=http://10.20.20.158:8000
```

`PUBLIC_BASE_URL` est important pour les QR codes. Si cette valeur vaut
`http://127.0.0.1:8000`, le telephone du caissier scannera un lien inutilisable,
car `127.0.0.1` pointera vers le telephone lui-meme.

## Trouver l'IP LAN du PC

Sur Windows :

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.PrefixOrigin -ne 'WellKnown' } |
  Select-Object IPAddress,InterfaceAlias
```

Ou plus simplement :

```powershell
ipconfig
```

Prends l'IPv4 de l'interface Wi-Fi connectee au meme reseau que la Raspberry.

## URLs utiles cote PC

En remplacant `IP_DU_PC` par l'IP LAN :

- Dashboard : `http://IP_DU_PC:8000/dashboard/`
- Admin : `http://IP_DU_PC:8000/admin/`
- Ecran panier Django : `http://IP_DU_PC:8000/basket-screen/<code>/`
- API panier : `http://IP_DU_PC:8000/api/baskets/<code>/`
- Caisse : `http://IP_DU_PC:8000/checkout/t/<token>/`

## Endpoints API principaux

```http
POST /api/baskets/start/
POST /api/baskets/ensure-active/
GET /api/baskets/<code>/
POST /api/baskets/<code>/add-detection/
POST /api/baskets/<code>/remove-item/
POST /api/baskets/<code>/finish/
GET /checkout/t/<token>/
POST /checkout/t/<token>/validate/
```

### Creer ou recuperer le panier actif d'un device

La Raspberry doit utiliser cet endpoint au demarrage pour recuperer une session
active existante ou en creer une nouvelle.

```http
POST /api/baskets/ensure-active/
```

Payload :

```json
{
  "device_id": "KITUNGA-PI-001"
}
```

Reponse :

```json
{
  "code": "SB-004",
  "device_id": "KITUNGA-PI-001",
  "status": "active",
  "total_amount": "0.00",
  "items": []
}
```

### Envoyer une detection depuis la Raspberry

La Raspberry envoie uniquement le label detecte et la confidence.

```http
POST /api/baskets/<code>/add-detection/
```

Payload :

```json
{
  "device_id": "KITUNGA-PI-001",
  "detected_label": "servo_sg90",
  "confidence": 0.90
}
```

Regles :

- si `confidence < 0.75`, le produit n'est pas ajoute ;
- si le label n'existe pas en base, la detection est historisee comme inconnue ;
- si le produit existe deja dans le panier, la quantite augmente ;
- le total est recalcule automatiquement.

### Terminer un panier

```http
POST /api/baskets/<code>/finish/
```

Reponse attendue :

```json
{
  "status": "pending_checkout",
  "checkout_url": "http://IP_DU_PC:8000/checkout/t/abc123/",
  "qr_code_url": "http://IP_DU_PC:8000/media/qrcodes/abc123.png"
}
```

Le QR code contient `checkout_url`.

### Valider le paiement

```http
POST /checkout/t/<token>/validate/
```

Effets :

- cree une transaction ;
- passe le panier en `paid` ;
- enregistre `paid_at` ;
- decremente le stock des produits ;
- affiche le ticket.

## Tests API rapides

Avec PowerShell depuis le PC :

```powershell
$base = "http://IP_DU_PC:8000"
$deviceId = "KITUNGA-PI-001"

$basket = Invoke-RestMethod `
  -Uri "$base/api/baskets/ensure-active/" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{ device_id = $deviceId } | ConvertTo-Json)

$code = $basket.code

Invoke-RestMethod `
  -Uri "$base/api/baskets/$code/add-detection/" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{
    device_id = $deviceId
    detected_label = "servo_sg90"
    confidence = 0.90
  } | ConvertTo-Json)

Invoke-RestMethod -Uri "$base/api/baskets/$code/" -Method Get

Invoke-RestMethod `
  -Uri "$base/api/baskets/$code/finish/" `
  -Method Post `
  -ContentType "application/json" `
  -Body "{}"
```

Avec `curl` depuis la Raspberry :

```bash
BASE="http://IP_DU_PC:8000"

curl -X POST "$BASE/api/baskets/ensure-active/" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"KITUNGA-PI-001"}'

curl -X POST "$BASE/api/baskets/SB-004/add-detection/" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"KITUNGA-PI-001","detected_label":"servo_sg90","confidence":0.90}'

curl "$BASE/api/baskets/SB-004/"
```

## Produits demo et labels attendus

La Raspberry envoie ces labels. Ils doivent exister dans `Product.detection_label`
avec `is_active=True`.

| Label Raspberry | Produit demo |
| --- | --- |
| `arduino_uno` | Arduino Uno |
| `esp32_devkit` | ESP32 DevKit |
| `hc_sr04` | Capteur ultrason HC-SR04 |
| `breadboard_830` | Breadboard 830 points |
| `servo_sg90` | Servo moteur SG90 |
| `relay_module_1ch` | Module relais 1 canal |
| `dupont_wires` | Jeu de cables Dupont |

Pour remplir ou reparer les produits demo :

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo_data
```

Le backend accepte aussi quelques anciens labels du modele et les redirige vers
les labels simples :

| Ancien label | Label produit |
| --- | --- |
| `esp32` | `esp32_devkit` |
| `sonar_sensor` | `hc_sr04` |
| `breadboard` | `breadboard_830` |
| `servo_motor` | `servo_sg90` |
| `relay_module` | `relay_module_1ch` |

## Scenario de demo recommande

1. Mettre le PC et la Raspberry sur le meme Wi-Fi.
2. Trouver l'IP LAN du PC.
3. Configurer `.env` du backend avec `PUBLIC_BASE_URL=http://IP_DU_PC:8000`.
4. Lancer Django sur le PC avec `runserver 0.0.0.0:8000`.
5. Depuis la Raspberry, tester `curl http://IP_DU_PC:8000/dashboard/`.
6. Configurer la Raspberry avec `VITE_DJANGO_TARGET=http://IP_DU_PC:8000`.
7. Lancer l'interface Vite sur la Raspberry.
8. Lancer le script YOLO/camera sur la Raspberry.
9. Montrer un objet, par exemple un servo SG90.
10. La Pi envoie `servo_sg90` avec une confidence.
11. Django ajoute le produit dans le panier.
12. L'interface client affiche l'objet, la quantite et le total.
13. Terminer le panier.
14. Scanner le QR code.
15. Valider la caisse.
16. Verifier le stock dans Django Admin.

## Client Raspberry Pi

Le dossier `kitunga_pi_client/` contient le client Python historique pour la
Raspberry :

- `main.py` : boucle camera + YOLO + envoi backend ;
- `camera.py` : capture image ;
- `detector.py` : chargement du modele Ultralytics ;
- `api_client.py` : appels REST vers Django ;
- `tkinter_screen.py` : ecran client de demo ;
- `scripts/` : scripts d'installation et de lancement.

Documentation detaillee :

```text
kitunga_pi_client/README.md
```

Commandes principales sur Raspberry :

```bash
git clone https://github.com/SteveMav/kitunga-ai.git
cd kitunga-ai/kitunga_pi_client
bash scripts/install_pi.sh
nano .env
bash scripts/test_backend.sh
bash scripts/test_camera.sh
bash scripts/run_all.sh
```

Le modele YOLO doit etre copie manuellement ici :

```text
kitunga_pi_client/models/best.pt
```

Le fichier `.pt` n'est pas pousse dans Git.

## Interface Vite sur la Raspberry

Si la Raspberry utilise l'interface Vite, son fichier `.env` frontend doit viser
le PC :

```env
VITE_DJANGO_TARGET=http://IP_DU_PC:8000
```

Dans la demo actuelle, l'ecran Raspberry etait ouvert sur :

```text
http://10.20.20.159:5174/
```

La page Vite doit appeler Django sur `http://10.20.20.158:8000` dans cet exemple.

## Test camera telephone avec Iriun + Vite

Le dossier `camera_tester/` sert uniquement aux tests sur PC avec une camera
navigateur comme Iriun Webcam.

Ce mode peut lancer YOLO cote Django pour faire une demo sans Raspberry, mais ce
n'est pas l'architecture cible finale.

Lancer Django localement :

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

Si Django tourne ailleurs, creer `camera_tester/.env` :

```env
VITE_DJANGO_TARGET=http://127.0.0.1:8000
```

## Commandes de verification

Tests Django :

```powershell
.\.venv\Scripts\python.exe manage.py test
```

Verification Django :

```powershell
.\.venv\Scripts\python.exe manage.py check
```

Verifier les labels actifs :

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from products.models import Product; labels=['arduino_uno','esp32_devkit','hc_sr04','breadboard_830','servo_sg90','relay_module_1ch','dupont_wires']; found=set(Product.objects.filter(is_active=True,detection_label__in=labels).values_list('detection_label', flat=True)); print('missing=', sorted(set(labels)-found))"
```

## Depannage

### La Raspberry ne voit pas Django

- Verifier que le PC et la Raspberry sont sur le meme Wi-Fi.
- Lancer Django avec `0.0.0.0:8000`, pas seulement `127.0.0.1:8000`.
- Verifier le firewall Windows pour autoriser Python/Django sur le port `8000`.
- Tester depuis la Raspberry : `curl http://IP_DU_PC:8000/dashboard/`.

### Le QR code pointe vers `127.0.0.1`

- Corriger `PUBLIC_BASE_URL` dans `.env`.
- Relancer Django.
- Regenerer un nouveau checkout avec `/finish/`.

### Une detection arrive mais le panier ne change pas

- Verifier que `confidence >= 0.75`.
- Verifier que le panier est en statut `active`.
- Verifier que `detected_label` correspond a un produit actif.
- Lancer `python manage.py seed_demo_data`.

### Erreur CSRF avec Vite

- Ajouter l'origine Vite dans `CSRF_TRUSTED_ORIGINS`.
- Exemple : `http://10.20.20.159:5174`.
- Relancer Django apres modification du `.env`.

### La caisse valide mais le stock ne change pas

- Verifier que le panier est bien en `pending_checkout` avant validation.
- Ne pas valider deux fois le meme token.
- Regarder la transaction dans Django Admin ou le dashboard.

## Notes de demo

Ce projet est un MVP etudiant. SQLite, `DEBUG=True` et `ALLOWED_HOSTS=*` sont
pratiques pour la demonstration locale, mais ne sont pas une configuration de
production.

Pour une vraie mise en production, il faudrait au minimum :

- remplacer SQLite par PostgreSQL ;
- desactiver `DEBUG` ;
- configurer des hosts precis ;
- proteger les endpoints sensibles ;
- ajouter une vraie authentification caisse/admin ;
- servir les fichiers statiques/media avec une configuration adaptee.
