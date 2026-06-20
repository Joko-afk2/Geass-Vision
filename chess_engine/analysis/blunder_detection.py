"""Classification des coups joués — S15."""

from __future__ import annotations

from enum import Enum


class CategorieCoup(str, Enum):
    BRILLIANT = "brilliant"
    EXCELLENT = "excellent"
    BEST = "best"
    GOOD = "good"
    INACCURACY = "inaccuracy"
    MISTAKE = "mistake"
    BLUNDER = "blunder"


SEUIL_EXCELLENT = 10
SEUIL_GOOD = 30
SEUIL_INACCURACY = 80
SEUIL_MISTAKE = 200


def classifier_perte(
    perte_cp: int,
    coup_est_meilleur: bool,
    gain_tactique: bool = False,
) -> CategorieCoup:
    """
    Classe un coup selon la perte en centipions.
    perte_cp >= 0 : 0 = meilleur coup trouvé par le moteur.
    """
    if gain_tactique and perte_cp <= 0:
        return CategorieCoup.BRILLIANT
    if coup_est_meilleur or perte_cp <= 0:
        return CategorieCoup.BEST
    if perte_cp <= SEUIL_EXCELLENT:
        return CategorieCoup.EXCELLENT
    if perte_cp <= SEUIL_GOOD:
        return CategorieCoup.GOOD
    if perte_cp <= SEUIL_INACCURACY:
        return CategorieCoup.INACCURACY
    if perte_cp <= SEUIL_MISTAKE:
        return CategorieCoup.MISTAKE
    return CategorieCoup.BLUNDER


def precision_pourcent(categories: list[CategorieCoup]) -> float:
    """Estime la précision : part de coups best/excellent/good."""
    if not categories:
        return 100.0
    bons = sum(
        1 for cat in categories
        if cat in (CategorieCoup.BEST, CategorieCoup.EXCELLENT, CategorieCoup.GOOD, CategorieCoup.BRILLIANT)
    )
    return round(100.0 * bons / len(categories), 1)
