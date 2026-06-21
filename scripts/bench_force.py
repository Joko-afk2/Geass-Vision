"""Validation de force : profondeur atteinte + résolution de puzzles tactiques."""

from __future__ import annotations

import time

import chess

from chess_engine.engine import search
from chess_engine.engine.engine import MoteurEchecs

POSITIONS = {
    "ouverture": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "milieu": "r1bq1rk1/pp2bppp/2n1pn2/2pp4/3P1B2/2PBPN2/PP1N1PPP/R2Q1RK1 w - - 0 9",
    "clouage": "rnbq1rk1/ppp1bppp/4pn2/3p2B1/3P4/2N1PN2/PPPQ1PPP/R3KB1R w KQ - 0 1",
}

# (FEN, coups attendus, description). Le moteur (Elo 2000) doit trouver le coup.
PUZZLES = [
    (
        "r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 4",
        {"h5f7"},
        "Mat du berger (mat en 1)",
    ),
    (
        "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
        {"a1a8"},
        "Mat du couloir (mat en 1)",
    ),
    (
        "7k/8/8/3q4/8/8/8/3RK3 w - - 0 1",
        {"d1d5"},
        "Dame noire en prise sur la colonne (gain de dame)",
    ),
    (
        "4k3/8/8/8/8/2b5/3P4/3QK3 w - - 0 1",
        {"d2c3"},
        "Le pion prend le fou (gain de pièce)",
    ),
]


def mesure(fen: str, budget: float = 2.5) -> None:
    board = chess.Board(fen)
    search.reinitialiser_compteurs()
    debut = time.perf_counter()
    scores = search.scores_coups_racine_iteratif(board, 64, budget)
    duree = time.perf_counter() - debut
    noeuds = search.obtenir_noeuds_alpha_beta()
    blancs = board.turn == chess.WHITE
    scores.sort(key=lambda p: p[1], reverse=blancs)
    meilleur = scores[0] if scores else (None, 0)
    print(
        f"  budget={budget}s duree={duree:.2f}s prof={search.derniere_profondeur_iterative} "
        f"noeuds={noeuds} meilleur={meilleur[0]} score={meilleur[1]}"
    )


def puzzles(budget: float = 2.5) -> None:
    reussis = 0
    for fen, attendus, desc in PUZZLES:
        board = chess.Board(fen)
        moteur = MoteurEchecs(elo=2000)
        debut = time.perf_counter()
        coup = moteur.choisir_coup(board, budget_secondes=budget)
        duree = time.perf_counter() - debut
        ok = coup is not None and coup.uci() in attendus
        reussis += int(ok)
        marque = "OK " if ok else "RATE"
        print(f"  [{marque}] {desc} -> {coup} ({duree:.2f}s) attendu={attendus}")
    print(f"  => {reussis}/{len(PUZZLES)} puzzles resolus")


if __name__ == "__main__":
    print("== Profondeur / vitesse ==")
    for nom, fen in POSITIONS.items():
        print(f"[{nom}]")
        mesure(fen)
    print("== Puzzles tactiques (Elo 2000) ==")
    puzzles()
