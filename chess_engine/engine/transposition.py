"""Table de transposition — S06 : Zobrist hashing + cache de positions."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import IntEnum

import chess

# Graine fixe : clés reproductibles pour les tests.
_GENERATEUR = random.Random(0xC0FFEE)


def _cle_aleatoire() -> int:
    return _GENERATEUR.getrandbits(64)


class TypeNoeud(IntEnum):
    EXACT = 0
    BORNE_BASSE = 1  # score >= valeur stockée (coupure beta)
    BORNE_HAUTE = 2  # score <= valeur stockée (coupure alpha)


@dataclass
class EntreeTT:
    profondeur: int
    score: int
    type_noeud: TypeNoeud
    coup: chess.Move | None = None


class Zobrist:
    """Hachage Zobrist incrémental compatible push/pop python-chess."""

    def __init__(self) -> None:
        self.cles_piece: dict[tuple[chess.PieceType, chess.Color, chess.Square], int] = {
            (piece_type, couleur, case): _cle_aleatoire()
            for piece_type in chess.PIECE_TYPES
            for couleur in chess.COLORS
            for case in chess.SQUARES
        }
        self.cle_trait_blanc = _cle_aleatoire()
        self.cles_roque_par_masque: dict[int, int] = {
            masque: _cle_aleatoire() for masque in range(16)
        }
        self.cles_ep = {case: _cle_aleatoire() for case in chess.SQUARES}

    @staticmethod
    def _index_roque(droits: chess.Bitboard) -> int:
        """Convertit les droits de roque python-chess en index 0..15."""
        index = 0
        if droits & chess.BB_A1:
            index |= 1
        if droits & chess.BB_H1:
            index |= 2
        if droits & chess.BB_A8:
            index |= 4
        if droits & chess.BB_H8:
            index |= 8
        return index

    def hash_initial(self, board: chess.Board) -> int:
        """Calcule le hash d'une position (utilisé à la racine)."""
        return self._calculer(board)

    def _calculer(self, board: chess.Board) -> int:
        h = 0

        if board.turn == chess.WHITE:
            h ^= self.cle_trait_blanc

        for case in chess.SQUARES:
            piece = board.piece_at(case)
            if piece is not None:
                h ^= self.cles_piece[(piece.piece_type, piece.color, case)]

        h ^= self.cles_roque_par_masque[self._index_roque(board.castling_rights)]

        if board.ep_square is not None:
            h ^= self.cles_ep[board.ep_square]

        return h

    def appliquer_coup(self, h: int, board: chess.Board, coup: chess.Move) -> int:
        """Met à jour le hash pour la position après coup (sans modifier le board)."""
        case_depart = coup.from_square
        case_arrivee = coup.to_square
        piece = board.piece_at(case_depart)
        if piece is None:
            return self._calculer(board)

        h ^= self.cles_piece[(piece.piece_type, piece.color, case_depart)]

        if board.is_capture(coup):
            if board.is_en_passant(coup):
                case_capturee = (
                    case_arrivee - 8 if piece.color == chess.WHITE else case_arrivee + 8
                )
                h ^= self.cles_piece[(chess.PAWN, not piece.color, case_capturee)]
            else:
                victime = board.piece_at(case_arrivee)
                if victime is not None:
                    h ^= self.cles_piece[(victime.piece_type, victime.color, case_arrivee)]

        if piece.piece_type == chess.KING and abs(case_depart - case_arrivee) == 2:
            if case_arrivee > case_depart:
                tour_depart, tour_arrivee = case_depart + 3, case_depart + 1
            else:
                tour_depart, tour_arrivee = case_depart - 4, case_depart - 1
            tour = board.piece_at(tour_depart)
            if tour is not None:
                h ^= self.cles_piece[(chess.ROOK, tour.color, tour_depart)]
                h ^= self.cles_piece[(chess.ROOK, tour.color, tour_arrivee)]

        type_arrivee = coup.promotion if coup.promotion is not None else piece.piece_type
        h ^= self.cles_piece[(type_arrivee, piece.color, case_arrivee)]

        # Droits de roque après le coup.
        roque_apres = board.castling_rights
        if piece.piece_type == chess.KING:
            if piece.color == chess.WHITE:
                roque_apres &= ~(chess.BB_A1 | chess.BB_H1)
            else:
                roque_apres &= ~(chess.BB_A8 | chess.BB_H8)
        if coup.from_square == chess.A1 or coup.to_square == chess.A1:
            roque_apres &= ~chess.BB_A1
        if coup.from_square == chess.H1 or coup.to_square == chess.H1:
            roque_apres &= ~chess.BB_H1
        if coup.from_square == chess.A8 or coup.to_square == chess.A8:
            roque_apres &= ~chess.BB_A8
        if coup.from_square == chess.H8 or coup.to_square == chess.H8:
            roque_apres &= ~chess.BB_H8

        if roque_apres != board.castling_rights:
            h ^= self.cles_roque_par_masque[self._index_roque(board.castling_rights)]
            h ^= self.cles_roque_par_masque[self._index_roque(roque_apres)]

        # En passant : effacé après tout coup ; case ep possible si pion avance de 2.
        if board.ep_square is not None:
            h ^= self.cles_ep[board.ep_square]

        if (
            piece.piece_type == chess.PAWN
            and abs(case_depart - case_arrivee) == 16
        ):
            case_ep = (case_depart + case_arrivee) // 2
            h ^= self.cles_ep[case_ep]

        h ^= self.cle_trait_blanc
        return h


class TableTransposition:
    """Cache de positions déjà explorées."""

    def __init__(self) -> None:
        self.table: dict[int, EntreeTT] = {}
        self.probes = 0
        self.hits = 0

    def reinitialiser(self) -> None:
        self.table.clear()
        self.probes = 0
        self.hits = 0

    def chercher(self, cle: int) -> EntreeTT | None:
        self.probes += 1
        return self.table.get(cle)

    def noter_hit(self) -> None:
        self.hits += 1

    def stocker(
        self,
        cle: int,
        profondeur: int,
        score: int,
        alpha: int,
        beta: int,
        coup: chess.Move | None,
    ) -> None:
        existante = self.table.get(cle)
        if existante is not None and existante.profondeur > profondeur:
            return

        if score <= alpha:
            type_noeud = TypeNoeud.BORNE_HAUTE
        elif score >= beta:
            type_noeud = TypeNoeud.BORNE_BASSE
        else:
            type_noeud = TypeNoeud.EXACT

        self.table[cle] = EntreeTT(profondeur, score, type_noeud, coup)

    def taux_hit(self) -> float:
        if self.probes == 0:
            return 0.0
        return self.hits / self.probes
