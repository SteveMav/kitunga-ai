# Kitunga Camera Tester

App Vite pour utiliser une webcam virtuelle comme Iriun Webcam, envoyer des frames en continu a Django, lancer YOLO et dessiner les boites de detection par-dessus la video.

## Lancer Iriun

1. Ouvrir Iriun Webcam sur le telephone.
2. Ouvrir Iriun Webcam sur le PC.
3. Attendre que le flux du telephone soit visible dans l'application Iriun PC.

Le navigateur verra ensuite Iriun comme une camera classique.

## Lancer Django

Depuis la racine du repo :

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Si Django tourne sur `8001`, creer `camera_tester/.env` :

```text
VITE_DJANGO_TARGET=http://127.0.0.1:8001
```

## Lancer Vite

```powershell
cd camera_tester
npm install
npm run dev
```

Ouvrir :

```text
http://127.0.0.1:5174
```

En mode live, Django ecrase une image temporaire par device pour eviter de remplir le disque :

```text
kitunga_pi_client/captures/live_IRIUN-PC-TEST.jpg
```

Depuis l'interface :

- Choisir Iriun Webcam.
- Cliquer `Ouvrir`.
- Verifier le `Basket code`.
- Cliquer `Lancer YOLO live`.
- Garder `Ajouter automatiquement au panier` actif si tu veux que les labels detectes soient envoyes au panier avec cooldown.

Si YOLO retourne `Servo-Motor`, Django le convertit en `servo_sg90`, puis le panier ajoute `Servo moteur SG90` quand la confiance est suffisante.
