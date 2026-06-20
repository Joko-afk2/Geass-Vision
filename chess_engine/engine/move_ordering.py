"""Ordonnancement des coups — S05 : MVV-LVA, killers, history."""

from __future__ import annotations

import chess

from chess_engine.engine.evaluation import VALEURS_PIECE

PROFONDEUR_MAX = 64
NB_KILLERS = 2

# Victime la plus précieuse, attaquant le moins cher en premier.
SCORE_MVV_LVA_BASE = 300_000
SCORE_PROMOTION_BASE = 500_000
SCORE_KILLER_BASE = 200_000
SCORE_HISTORY_BASE = 100_000


class OrdonnancementCoups:
    """Gère l'ordre de recherche des coups légaux."""

    def __init__(self) -> None:
        self.killers: list[list[chess.Move | None]] = [
            [None] * NB_KILLERS for _ in range(PROFONDEUR_MAX)
        ]
        # (type de pièce, case d'arrivée) → bonus history
        self.history: dict[tuple[chess.PieceType, chess.Square], int] = {}

    def reinitialiser(self) -> None:
        """Remet à zéro killers et history (début de recherche)."""
        for niveau in range(PROFONDEUR_MAX):
            self.killers[niveau] = [None] * NB_KILLERS
        self.history.clear()

    def score_mvv_lva(self, board: chess.Board, coup: chess.Move) -> int:
        """Score MVV-LVA pour les captures (0 si coup tranquille)."""
        if not board.is_capture(coup):
            return 0

        if board.is_en_passant(coup):
            valeur_victime = VALEURS_PIECE[chess.PAWN]
        else:
            piece_victime = board.piece_at(coup.to_square)
            valeur_victime = VALEURS_PIECE[piece_victime.piece_type] if piece_victime else 0

        piece_attaquante = board.piece_at(coup.from_square)
        valeur_attaquant = (
            VALEURS_PIECE[piece_attaquante.piece_type] if piece_attaquante else 0
        )

        return 10 * valeur_victime - valeur_attaquant

    def score_coup(
        self,
        board: chess.Board,
        coup: chess.Move,
        niveau: int,
        coup_tt: chess.Move | None = None,
    ) -> int:
        """Score de priorité — plus élevé = recherché en premier."""
        if coup_tt is not None and coup == coup_tt:
            return 1_000_000

        if coup.promotion is not None:
            return SCORE_PROMOTION_BASE + (coup.promotion or 0)

        score_capture = self.score_mvv_lva(board, coup)
        if score_capture > 0:
            return SCORE_MVV_LVA_BASE + score_capture

        for indice, killer in enumerate(self.killers[niveau]):
            if killer is not None and coup == killer:
                return SCORE_KILLER_BASE - indice

        piece = board.piece_at(coup.from_square)
        if piece is not None:
            bonus = self.history.get((piece.piece_type, coup.to_square), 0)
            return SCORE_HISTORY_BASE + bonus

        return 0

    def ordonner(
        self,
        board: chess.Board,
        coups: list[chess.Move],
        niveau: int,
        coup_tt: chess.Move | None = None,
    ) -> list[chess.Move]:
        """Trie les coups par score décroissant."""
        return sorted(
            coups,
            key=lambda coup: self.score_coup(board, coup, niveau, coup_tt),
            reverse=True,
        )

    def enregistrer_killer(self, niveau: int, coup: chess.Move) -> None:
        """Mémorise un coup tranquille ayant provoqué une coupure."""
        if self.killers[niveau][0] == coup:
            return
        self.killers[niveau][1] = self.killers[niveau][0]
        self.killers[niveau][0] = coup

    def enregistrer_history(
        self,
        board: chess.Board,
        coup: chess.Move,
        niveau: int,
    ) -> None:
        """Augmente le bonus history d'un coup efficace."""
        piece = board.piece_at(coup.from_square)
        if piece is None:
            return
        cle = (piece.piece_type, coup.to_square)
        self.history[cle] = self.history.get(cle, 0) + niveau * niveau

    def obtenir_killers(self, niveau: int) -> list[chess.Move | None]:
        return list(self.killers[niveau])
