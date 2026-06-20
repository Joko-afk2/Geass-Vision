"""Analyse de partie coup par coup — S15."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from io import StringIO
from typing import Any

import chess
import chess.pgn

import chess_engine.engine.search as search
from chess_engine.engine.search import SCORE_MAT, alpha_beta, trouver_meilleur_coup, zobrist
from chess_engine.analysis.blunder_detection import (
    CategorieCoup,
    classifier_perte,
    precision_pourcent,
)


@dataclass
class AnalyseCoup:
    numero: int
    coup: str
    couleur: str
    eval_avant: int
    eval_apres: int
    meilleur_coup: str | None
    perte_cp: int
    categorie: str


@dataclass
class RapportPartie:
    event: str
    blancs: str
    noirs: str
    resultat: str
    coups: list[AnalyseCoup]
    precision_blancs: float
    precision_noirs: float

    def vers_dict(self) -> dict[str, Any]:
        return asdict(self)

    def vers_json(self, indent: int = 2) -> str:
        return json.dumps(self.vers_dict(), indent=indent, ensure_ascii=False)


def _score_position(board: chess.Board, profondeur: int) -> int:
    if board.is_game_over():
        return search._evaluer_terminal(board, 0)
    return alpha_beta(
        board,
        profondeur,
        -SCORE_MAT * 2,
        SCORE_MAT * 2,
        cle=zobrist.hash_initial(board),
    )


def _score_apres_coup(board: chess.Board, coup: chess.Move, profondeur: int) -> int:
    board.push(coup)
    score = _score_position(board, max(0, profondeur - 1))
    board.pop()
    return score


def analyser_coup(
    board: chess.Board,
    coup: chess.Move,
    numero: int,
    profondeur: int = 3,
) -> AnalyseCoup:
    """Analyse un coup : évaluation, meilleur coup moteur, perte et classification."""
    eval_avant = _score_position(board, profondeur)
    meilleur = trouver_meilleur_coup(board, profondeur)

    score_meilleur = _score_apres_coup(board, meilleur, profondeur) if meilleur else eval_avant
    score_joue = _score_apres_coup(board, coup, profondeur)

    if board.turn == chess.WHITE:
        perte = max(0, score_meilleur - score_joue)
    else:
        perte = max(0, score_joue - score_meilleur)

    coup_est_meilleur = meilleur is not None and coup == meilleur
    gain_tactique = score_joue - eval_avant > 150 if board.turn == chess.WHITE else eval_avant - score_joue > 150
    categorie = classifier_perte(perte, coup_est_meilleur, gain_tactique)

    board.push(coup)
    eval_apres = _score_position(board, profondeur)
    board.pop()

    return AnalyseCoup(
        numero=numero,
        coup=coup.uci(),
        couleur="blanc" if board.turn == chess.WHITE else "noir",
        eval_avant=eval_avant,
        eval_apres=eval_apres,
        meilleur_coup=meilleur.uci() if meilleur else None,
        perte_cp=perte,
        categorie=categorie.value,
    )


def analyser_partie(
    board: chess.Board,
    coups: list[chess.Move],
    profondeur: int = 3,
) -> list[AnalyseCoup]:
    """Analyse une liste de coups sur un échiquier."""
    livre_avant = search.livre_actif
    search.livre_actif = False
    analyses: list[AnalyseCoup] = []

    try:
        for numero, coup in enumerate(coups, start=1):
            analyses.append(analyser_coup(board, coup, numero, profondeur))
            board.push(coup)
    finally:
        search.livre_actif = livre_avant

    return analyses


def analyser_pgn(pgn_texte: str, profondeur: int = 3) -> RapportPartie:
    """Analyse une partie au format PGN et produit un rapport complet."""
    partie = chess.pgn.read_game(StringIO(pgn_texte))
    if partie is None:
        raise ValueError("PGN invalide ou vide")

    board = partie.board()
    coups = list(partie.mainline_moves())
    analyses = analyser_partie(board, coups, profondeur)

    cats_blancs = [
        CategorieCoup(a.categorie)
        for a in analyses
        if a.couleur == "blanc"
    ]
    cats_noirs = [
        CategorieCoup(a.categorie)
        for a in analyses
        if a.couleur == "noir"
    ]

    return RapportPartie(
        event=partie.headers.get("Event", "?"),
        blancs=partie.headers.get("White", "?"),
        noirs=partie.headers.get("Black", "?"),
        resultat=partie.headers.get("Result", "*"),
        coups=analyses,
        precision_blancs=precision_pourcent(cats_blancs),
        precision_noirs=precision_pourcent(cats_noirs),
    )
