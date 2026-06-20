# Moteur d'échecs — Geass Vision

Jouer contre le moteur en **ligne de commande** ou via **site web**.

## Lancer en local (le plus simple)

```bash
pip install -r requirements.txt
python -m chess_engine.main --elo 800
```

Coups en UCI : `e2e4`, `g1f3` — taper `quit` pour quitter.

## Site web + moteur (Docker)

```bash
docker compose up --build
```

Ouvre http://localhost:8080

## Mise en ligne (Render)

1. Pousse ce dépôt sur GitHub (branche `main`).
2. Compte sur [render.com](https://render.com) → **New → Blueprint** ou **Web Service**.
3. Connecte le dépôt **Geass-Vision**, runtime **Docker**, fichier `./Dockerfile`.
4. Instance **512 Mo RAM** minimum. Render définit `PORT` automatiquement.
5. URL publique : `https://…onrender.com` — échiquier + API sur la même adresse.

Vérifier : `https://ton-url/health` → `{"status":"ok"}`

> Plan gratuit : veille après inactivité (~30 s au 1er chargement).

Test local Docker : `docker compose up --build` → http://localhost:8080
