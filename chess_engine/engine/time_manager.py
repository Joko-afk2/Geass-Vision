"""Gestion du temps de réflexion — S07."""

from __future__ import annotations

import time
from dataclasses import dataclass

import chess

# Cadences prédéfinies : (secondes de base, incrément en secondes).
CADENCES: dict[str, tuple[int, int]] = {
    "1+0": (1, 0),
    "3+0": (3, 0),
    "3+2": (3, 2),
    "5+0": (5, 0),
    "10+0": (10, 0),
    "15+10": (15, 10),
}


@dataclass
class Cadence:
    """Description d'une cadence (ex. 3+2 = 3 min + 2 s par coup)."""

    base_secondes: int
    increment_secondes: int
    nom: str = "custom"

    @classmethod
    def depuis_nom(cls, nom: str) -> Cadence:
        if nom not in CADENCES:
            raise ValueError(f"Cadence inconnue : {nom}")
        base, inc = CADENCES[nom]
        return cls(base, inc, nom)

    @classmethod
    def personnalisee(cls, base_secondes: int, increment_secondes: int) -> Cadence:
        return cls(base_secondes, increment_secondes, "custom")


class GestionnaireTemps:
    """
    Alloue un budget par coup et détecte le dépassement.
    Les temps sont en secondes (float pour la précision).
    """

    def __init__(
        self,
        cadence: Cadence,
        temps_blancs: float | None = None,
        temps_noirs: float | None = None,
    ) -> None:
        self.cadence = cadence
        budget = float(cadence.base_secondes)
        self.temps_blancs = temps_blancs if temps_blancs is not None else budget
        self.temps_noirs = temps_noirs if temps_noirs is not None else budget
        self.deadline: float | None = None
        self.budget_coup: float = 0.0

    def temps_restant(self, board: chess.Board) -> float:
        return self.temps_blancs if board.turn == chess.WHITE else self.temps_noirs

    def allouer_pour_coup(self, board: chess.Board) -> float:
        """
        Calcule le budget pour le coup en cours.
        Plus la position est complexe (nombre de coups légaux), plus on accorde de temps.
        """
        restant = self.temps_restant(board)
        nb_coups = max(len(list(board.legal_moves)), 1)

        # Répartition : environ 1/25 du temps restant, ajusté par la complexité.
        base = restant / 25.0
        facteur_complexite = min(2.0, 1.0 + nb_coups / 40.0)
        budget = base * facteur_complexite

        # Ne jamais dépasser 40 % du temps restant (garder de la marge).
        budget = min(budget, restant * 0.4)

        # Minimum pour éviter les timeouts instantanés en fin de partie.
        budget = max(budget, 0.05)

        self.budget_coup = budget
        self.deadline = time.perf_counter() + budget
        return budget

    def demarrer_coup(self, board: chess.Board) -> float:
        """Prépare le chronomètre pour le camp au trait."""
        return self.allouer_pour_coup(board)

    def temps_ecoule(self) -> bool:
        if self.deadline is None:
            return False
        return time.perf_counter() >= self.deadline

    def consommer(self, board: chess.Board, duree: float) -> None:
        """Déduit une durée de réflexion et ajoute l'incrément."""
        if board.turn == chess.WHITE:
            self.temps_blancs = max(0.0, self.temps_blancs - duree)
            self.temps_blancs += self.cadence.increment_secondes
        else:
            self.temps_noirs = max(0.0, self.temps_noirs - duree)
            self.temps_noirs += self.cadence.increment_secondes
        self.deadline = None

    def est_en_retard(self, board: chess.Board) -> bool:
        return self.temps_restant(board) <= 0.0
