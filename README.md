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

## Mise en ligne

Render / VPS : voir `Dockerfile` à la racine.  
Guides détaillés : dossier `explications/` (sur ton PC, pas obligatoire sur GitHub).
