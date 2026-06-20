"""Mesures de performance — S17."""

from __future__ import annotations

import time

import chess

from chess_engine.engine import search

FEN_BENCHMARK = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
PROFONDEUR_BENCHMARK = 4

# Référence avant optimisations S17 (profondeur 4, livre désactivé) : ~2500 n/s en isolation.
# En suite complète pytest, le débit baisse ; on vérifie surtout le nombre de nœuds et la durée max.
NOEUDS_MIN_ATTENDUS = 5_000
DUREE_MAX_SEC = 10.0


def mesurer_recherche(
    board: chess.Board | None = None,
    profondeur: int = PROFONDEUR_BENCHMARK,
) -> tuple[float, int]:
    """
    Lance une recherche alpha-beta et retourne (durée en secondes, nœuds explorés).
    Livre et bruit d'évaluation désactivés pour une mesure reproductible.
    """
    if board is None:
        board = chess.Board(FEN_BENCHMARK)

    ancien_livre = search.livre_actif
    ancien_bruit = search.bruit_evaluation
    search.livre_actif = False
    search.bruit_evaluation = 0
    search.reinitialiser_compteurs()

    debut = time.perf_counter()
    search.trouver_meilleur_coup(board, profondeur)
    duree = time.perf_counter() - debut
    noeuds = search.obtenir_noeuds_alpha_beta()

    search.livre_actif = ancien_livre
    search.bruit_evaluation = ancien_bruit
    return duree, noeuds


def noeuds_par_seconde(duree: float, noeuds: int) -> float:
    if duree <= 0:
        return 0.0
    return noeuds / duree
