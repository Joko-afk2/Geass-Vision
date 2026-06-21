"""Façade du moteur et gestion des niveaux Elo — S14."""

from __future__ import annotations

import random
from dataclasses import dataclass

import chess

import chess_engine.engine.search as search
from chess_engine.engine.opening_book import livre_ouvertures
from chess_engine.engine.search import (
    recherche_approfondissement,
    scores_coups_racine,
    trouver_meilleur_coup,
)
from chess_engine.engine.time_manager import GestionnaireTemps

# Budget par défaut (secondes) quand aucun temps n'est imposé explicitement.
BUDGET_DEFAUT_SECONDES = 2.0


@dataclass(frozen=True)
class ParametresNiveau:
    elo: int
    profondeur_max: int
    bruit_evaluation: int
    proba_gaffe: float
    top_n: int
    captures_uniquement: bool
    utiliser_livre: bool
    null_move: bool
    pvs: bool


# profondeur_max est désormais un *plafond* : la recherche est bornée en temps
# (approfondissement itératif). Les niveaux faibles gardent un plafond bas pour
# rester accessibles ; les niveaux forts laissent le temps décider de la
# profondeur réellement atteinte.
PALIERS: tuple[ParametresNiveau, ...] = (
    ParametresNiveau(1, 1, 250, 0.92, 16, False, False, False, False),
    ParametresNiveau(200, 2, 60, 0.55, 6, True, False, False, False),
    ParametresNiveau(500, 3, 90, 0.40, 5, False, True, False, False),
    ParametresNiveau(800, 4, 55, 0.28, 4, False, True, True, False),
    ParametresNiveau(1200, 6, 30, 0.18, 3, False, True, True, True),
    ParametresNiveau(1500, 10, 18, 0.08, 2, False, True, True, True),
    ParametresNiveau(1800, 16, 8, 0.03, 1, False, True, True, True),
    ParametresNiveau(2000, 64, 0, 0.0, 1, False, True, True, True),
)


def _interp_entier(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def _interp_flottant(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def parametres_depuis_elo(elo: int) -> ParametresNiveau:
    """Construit les paramètres du moteur par interpolation entre les paliers de référence."""
    elo = max(1, min(2000, elo))

    if elo <= PALIERS[0].elo:
        return PALIERS[0]
    if elo >= PALIERS[-1].elo:
        return PALIERS[-1]

    for bas, haut in zip(PALIERS, PALIERS[1:]):
        if elo <= haut.elo:
            t = (elo - bas.elo) / (haut.elo - bas.elo)
            return ParametresNiveau(
                elo=elo,
                profondeur_max=max(1, _interp_entier(bas.profondeur_max, haut.profondeur_max, t)),
                bruit_evaluation=_interp_entier(bas.bruit_evaluation, haut.bruit_evaluation, t),
                proba_gaffe=_interp_flottant(bas.proba_gaffe, haut.proba_gaffe, t),
                top_n=max(1, _interp_entier(bas.top_n, haut.top_n, t)),
                captures_uniquement=bas.captures_uniquement if t < 0.5 else haut.captures_uniquement,
                utiliser_livre=bas.utiliser_livre if t < 0.5 else haut.utiliser_livre,
                null_move=bas.null_move if t < 0.5 else haut.null_move,
                pvs=bas.pvs if t < 0.5 else haut.pvs,
            )

    return PALIERS[-1]


def _selectionner_coup(
    board: chess.Board,
    scores: list[tuple[chess.Move, int]],
    top_n: int,
) -> chess.Move:
    """Sélectionne parmi les N meilleurs coups (tirage pondéré pour les niveaux faibles)."""
    if board.turn == chess.WHITE:
        scores.sort(key=lambda paire: paire[1], reverse=True)
    else:
        scores.sort(key=lambda paire: paire[1])

    candidats = scores[:top_n]
    if len(candidats) == 1:
        return candidats[0][0]

    poids = [max(1, top_n - index) for index in range(len(candidats))]
    return random.choices(
        [coup for coup, _ in candidats],
        weights=poids,
        k=1,
    )[0]


class MoteurEchecs:
    """Point d'entrée du moteur avec niveau Elo configurable (1–2000)."""

    def __init__(self, elo: int = 1200) -> None:
        self.elo = max(1, min(2000, elo))
        self.parametres = parametres_depuis_elo(self.elo)

    def _appliquer_parametres(self) -> None:
        parametres = self.parametres
        search.bruit_evaluation = parametres.bruit_evaluation
        search.captures_uniquement = parametres.captures_uniquement
        search.livre_actif = parametres.utiliser_livre
        search.null_move_actif = parametres.null_move
        search.pvs_actif = parametres.pvs

    @staticmethod
    def _reinitialiser_parametres() -> None:
        search.bruit_evaluation = 0
        search.captures_uniquement = False
        search.livre_actif = True
        search.null_move_actif = True
        search.pvs_actif = True

    def choisir_coup(
        self,
        board: chess.Board,
        gestionnaire: GestionnaireTemps | None = None,
        budget_secondes: float | None = None,
    ) -> chess.Move | None:
        """
        Choisit un coup selon le niveau Elo (profondeur, bruit, erreurs, top-N).

        Si ``budget_secondes`` est fourni, la recherche est bornée en temps
        (approfondissement itératif) : un coup est toujours renvoyé rapidement,
        ce qui évite tout blocage dans les positions complexes.
        """
        coups_legaux = list(board.legal_moves)
        if not coups_legaux:
            return None

        parametres = self.parametres
        self._appliquer_parametres()

        # Sécurité : sans budget ni gestionnaire de temps, on borne malgré tout
        # la recherche (le plafond de profondeur peut être très élevé).
        if budget_secondes is None and gestionnaire is None:
            budget_secondes = BUDGET_DEFAUT_SECONDES

        try:
            if random.random() < parametres.proba_gaffe:
                candidats = search._coups_racine(board)
                return random.choice(candidats if candidats else coups_legaux)

            if parametres.utiliser_livre:
                coup_livre = livre_ouvertures.coup_livre(board)
                if coup_livre is not None:
                    return coup_livre

            if budget_secondes is not None:
                scores = search.scores_coups_racine_iteratif(
                    board, parametres.profondeur_max, budget_secondes
                )
                if scores:
                    return _selectionner_coup(board, scores, parametres.top_n)
                return random.choice(coups_legaux)

            if parametres.elo >= 1800 and gestionnaire is not None:
                coup, _ = recherche_approfondissement(board, gestionnaire)
                if coup is not None:
                    return coup

            if parametres.top_n == 1 and parametres.bruit_evaluation == 0:
                return trouver_meilleur_coup(board, parametres.profondeur_max)

            scores = scores_coups_racine(board, parametres.profondeur_max)
            if not scores:
                return random.choice(coups_legaux)
            return _selectionner_coup(board, scores, parametres.top_n)
        finally:
            self._reinitialiser_parametres()
