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

## Scenario de demo rapide

1. Lancer le serveur.
2. Creer une session avec `POST /api/baskets/start/`.
3. Ouvrir `/basket-screen/<code>/`.
4. Envoyer une detection reconnue.
5. Cliquer sur `Terminer le panier`.
6. Ouvrir le QR code ou le lien caisse.
7. Valider le paiement.
8. Verifier le stock dans Django Admin.
