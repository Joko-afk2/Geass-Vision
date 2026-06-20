"""Service d'analyse post-partie — W07."""

from __future__ import annotations

import chess

from chess_engine.analysis.blunder_detection import CategorieCoup, precision_pourcent
from chess_engine.analysis.game_analysis import (
    RapportPartie,
    analyser_partie,
    analyser_pgn,
)
from web.backend.services.engine_service import Partie


def analyser_partie_web(partie: Partie, profondeur: int = 2) -> RapportPartie:
    """Analyse les coups d'une partie web en mémoire."""
    board = chess.Board()
    coups = [chess.Move.from_uci(uci) for uci in partie.historique_uci]
    analyses = analyser_partie(board, coups, profondeur)

    if partie.couleur_humain == chess.WHITE:
        blancs, noirs = "Humain", "Moteur"
    else:
        blancs, noirs = "Moteur", "Humain"

    cats_blancs = [
        CategorieCoup(coup.categorie) for coup in analyses if coup.couleur == "blanc"
    ]
    cats_noirs = [
        CategorieCoup(coup.categorie) for coup in analyses if coup.couleur == "noir"
    ]

    board_final = chess.Board()
    for uci in partie.historique_uci:
        board_final.push(chess.Move.from_uci(uci))
    resultat = "1/2-1/2"
    if board_final.is_checkmate():
        resultat = "0-1" if board_final.turn == chess.WHITE else "1-0"

    return RapportPartie(
        event="Partie web",
        blancs=blancs,
        noirs=noirs,
        resultat=resultat,
        coups=analyses,
        precision_blancs=precision_pourcent(cats_blancs),
        precision_noirs=precision_pourcent(cats_noirs),
    )


def analyser_pgn_texte(pgn: str, profondeur: int = 2) -> RapportPartie:
    return analyser_pgn(pgn, profondeur)
