"""Livre d'ouvertures — S12."""

from __future__ import annotations

import json
import random
from pathlib import Path

import chess

_CHEMIN_LIVRE = Path(__file__).resolve().parent.parent / "data" / "openings.json"

livre_actif = True


class LivreOuvertures:
    """Dictionnaire FEN → coups pondérés, construit à partir de lignes PGN/UCI."""

    def __init__(self, chemin: Path | None = None) -> None:
        self._coups: dict[str, dict[chess.Move, int]] = {}
        self._noms: list[str] = []
        self._charger(chemin or _CHEMIN_LIVRE)

    def _charger(self, chemin: Path) -> None:
        with chemin.open(encoding="utf-8") as fichier:
            donnees = json.load(fichier)

        for ouverture in donnees["ouvertures"]:
            self._noms.append(ouverture["nom"])
            for ligne in ouverture["lignes"]:
                self._ajouter_ligne(ligne["coups"], ligne.get("poids", 1))

    def _ajouter_ligne(self, coups_uci: list[str], poids: int) -> None:
        board = chess.Board()
        for uci in coups_uci:
            fen = board.fen()
            coup = chess.Move.from_uci(uci)
            if coup not in board.legal_moves:
                raise ValueError(f"Coup illégal dans le livre : {uci} ({fen})")

            if fen not in self._coups:
                self._coups[fen] = {}
            self._coups[fen][coup] = self._coups[fen].get(coup, 0) + poids
            board.push(coup)

    @property
    def noms_ouvertures(self) -> list[str]:
        return list(self._noms)

    def contient(self, board: chess.Board) -> bool:
        """True si la position courante a au moins un coup de livre légal."""
        fen = board.fen()
        if fen not in self._coups:
            return False
        return any(coup in board.legal_moves for coup in self._coups[fen])

    def coup_livre(self, board: chess.Board) -> chess.Move | None:
        """
        Retourne un coup du livre (sélection pondérée) ou None si position inconnue.
        """
        fen = board.fen()
        if fen not in self._coups:
            return None

        candidats: list[chess.Move] = []
        poids: list[int] = []
        for coup, valeur in self._coups[fen].items():
            if coup in board.legal_moves:
                candidats.append(coup)
                poids.append(valeur)

        if not candidats:
            return None

        return random.choices(candidats, weights=poids, k=1)[0]


livre_ouvertures = LivreOuvertures()
