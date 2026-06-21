"""Évaluation statique de position — S02/S11/S13."""

from __future__ import annotations

import chess

# --- Matériel (centipions, perspective Blancs) ---

VALEUR_PION = 100
VALEUR_CAVALIER = 320
VALEUR_FOU = 330
VALEUR_TOUR = 500
VALEUR_DAME = 900

VALEURS_PIECE: dict[chess.PieceType, int] = {
    chess.PAWN: VALEUR_PION,
    chess.KNIGHT: VALEUR_CAVALIER,
    chess.BISHOP: VALEUR_FOU,
    chess.ROOK: VALEUR_TOUR,
    chess.QUEEN: VALEUR_DAME,
    chess.KING: 0,
}

# --- PST milieu de partie ---

PST_PION_MG: tuple[int, ...] = (
      0,   0,   0,   0,   0,   0,   0,   0,
     50,  50,  50,  50,  50,  50,  50,  50,
     10,  10,  20,  30,  30,  20,  10,  10,
      5,   5,  10,  25,  25,  10,   5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      5,  -5, -10,   0,   0, -10,  -5,   5,
      5,  10,  10, -20, -20,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0,
)

PST_CAVALIER_MG: tuple[int, ...] = (
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
)

PST_FOU_MG: tuple[int, ...] = (
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
)

PST_TOUR_MG: tuple[int, ...] = (
      0,   0,   0,   0,   0,   0,   0,   0,
      5,  10,  10,  10,  10,  10,  10,   5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     10,  15,  15,  15,  15,  15,  15,  10,
)

PST_DAME_MG: tuple[int, ...] = (
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20,
)

PST_ROI_MG: tuple[int, ...] = (
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     20,  30,  10,   0,   0,  10,  30,  20,
)

# --- PST finale (roi actif, pions avancés) ---

PST_PION_EG: tuple[int, ...] = (
      0,   0,   0,   0,   0,   0,   0,   0,
    160, 160, 160, 160, 160, 160, 160, 160,
     20,  20,  30,  50,  50,  30,  20,  20,
     10,  10,  20,  30,  30,  20,  10,  10,
      5,   5,  15,  40,  40,  15,   5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,
      0,   0,   0,   0,   0,   0,   0,   0,
)

PST_CAVALIER_EG: tuple[int, ...] = (
    -60, -40, -20, -20, -20, -20, -40, -60,
    -40, -10,   0,   0,   0,   0, -10, -40,
    -20,   0,  10,  15,  15,  10,   0, -20,
    -20,  10,  15,  20,  20,  15,  10, -20,
    -20,   0,  15,  20,  20,  15,   0, -20,
    -20,   5,  10,  15,  15,  10,   5, -20,
    -40,   0,   5,  10,  10,   5,   0, -40,
    -60, -40, -20, -20, -20, -20, -40, -60,
)

PST_FOU_EG: tuple[int, ...] = PST_FOU_MG

PST_TOUR_EG: tuple[int, ...] = (
     10,  15,  15,  15,  15,  15,  15,  10,
     10,  15,  15,  15,  15,  15,  15,  10,
     10,  15,  15,  15,  15,  15,  15,  10,
     10,  15,  15,  15,  15,  15,  15,  10,
     10,  15,  15,  15,  15,  15,  15,  10,
     10,  15,  15,  15,  15,  15,  15,  10,
     10,  15,  15,  15,  15,  15,  15,  10,
     10,  15,  15,  15,  15,  15,  15,  10,
)

PST_DAME_EG: tuple[int, ...] = PST_DAME_MG

PST_ROI_EG: tuple[int, ...] = (
    -20, -20, -20, -20, -20, -20, -20, -20,
    -20, -20, -20, -20, -20, -20, -20, -20,
    -20, -20, -20, -20, -20, -20, -20, -20,
    -20, -20, -20, -20, -20, -20, -20, -20,
    -10, -10, -10, -10, -10, -10, -10, -10,
     10,  10,  10,  10,  10,  10,  10,  10,
     30,  30,  30,  30,  30,  30,  30,  30,
     50,  50,  50,  50,  50,  50,  50,  50,
)

PST_MG: dict[chess.PieceType, tuple[int, ...]] = {
    chess.PAWN: PST_PION_MG,
    chess.KNIGHT: PST_CAVALIER_MG,
    chess.BISHOP: PST_FOU_MG,
    chess.ROOK: PST_TOUR_MG,
    chess.QUEEN: PST_DAME_MG,
    chess.KING: PST_ROI_MG,
}

PST_EG: dict[chess.PieceType, tuple[int, ...]] = {
    chess.PAWN: PST_PION_EG,
    chess.KNIGHT: PST_CAVALIER_EG,
    chess.BISHOP: PST_FOU_EG,
    chess.ROOK: PST_TOUR_EG,
    chess.QUEEN: PST_DAME_EG,
    chess.KING: PST_ROI_EG,
}

CASES_CENTRE = (
    chess.D4, chess.E4, chess.D5, chess.E5,
    chess.C3, chess.F3, chess.C6, chess.F6,
    chess.C4, chess.F4, chess.C5, chess.F5,
)

BONUS_PAIRE_FOUS = 35
BONUS_PION_PASSE = 25
MALUS_PION_DOUBLE = 15
MALUS_PION_ISOLE = 12
MALUS_PION_ARRIERE = 8
BONUS_COLONNE_OUVERTE = 18
BONUS_ROQUE = 25
BONUS_BOUCLIER_PION = 8
COEF_MOBILITE = 2

# Malus pour une pièce clouée (absolument, sur le roi) : elle ne peut pas
# bouger et défend mal, ce qui ouvre des tactiques (fourchettes, gains).
MALUS_CLOUAGE: dict[chess.PieceType, int] = {
    chess.KNIGHT: 14,
    chess.BISHOP: 14,
    chess.ROOK: 18,
    chess.QUEEN: 8,
}

# --- Finales (S13) ---

BONUS_KP_AVANCE = (0, 10, 25, 50, 90, 150, 280, 0)
BONUS_KP_ROI_PROCHE = 45
MALUS_KP_ROI_LOIN = 35
BONUS_KP_OPPOSITION = 80
BONUS_TOUR_7E_RANG = 40
BONUS_TOUR_DERRIERE_PION = 30
COEF_ROI_ACTIF_TOURS = 14


def _case_pst(square: chess.Square, couleur: chess.Color) -> chess.Square:
    if couleur == chess.WHITE:
        return square
    return square ^ 56


def _facteur_finale(board: chess.Board) -> int:
    """
    Retourne un facteur 0 (milieu) à 256 (finale) selon le matériel restant.
    """
    total = 0
    for piece_type, valeur in VALEURS_PIECE.items():
        total += len(board.pieces(piece_type, chess.WHITE)) * valeur
        total += len(board.pieces(piece_type, chess.BLACK)) * valeur

    # Matériel de départ ≈ 2×(8×100 + 2×320 + 2×330 + 2×500 + 900) sans rois
    if total >= 5000:
        return 0
    if total <= 1500:
        return 256
    return (5000 - total) * 256 // 3500


def evaluer_materiel(board: chess.Board) -> int:
    score = 0
    for piece_type, valeur in VALEURS_PIECE.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * valeur
        score -= len(board.pieces(piece_type, chess.BLACK)) * valeur
    return score


def _pst_piece(
    table_mg: tuple[int, ...],
    table_eg: tuple[int, ...],
    case: chess.Square,
    couleur: chess.Color,
    facteur_eg: int,
) -> int:
    indice = _case_pst(case, couleur)
    mg = table_mg[indice]
    eg = table_eg[indice]
    return (mg * (256 - facteur_eg) + eg * facteur_eg) // 256


def evaluer_pst(board: chess.Board) -> int:
    facteur_eg = _facteur_finale(board)
    score = 0
    for piece_type in PST_MG:
        table_mg = PST_MG[piece_type]
        table_eg = PST_EG[piece_type]
        for case in board.pieces(piece_type, chess.WHITE):
            score += _pst_piece(table_mg, table_eg, case, chess.WHITE, facteur_eg)
        for case in board.pieces(piece_type, chess.BLACK):
            score -= _pst_piece(table_mg, table_eg, case, chess.BLACK, facteur_eg)
    return score


def _evaluer_centre(board: chess.Board) -> int:
    score = 0
    for case in CASES_CENTRE:
        piece = board.piece_at(case)
        if piece is None:
            continue
        bonus = 12 if case in (chess.D4, chess.E4, chess.D5, chess.E5) else 6
        if piece.color == chess.WHITE:
            score += bonus
        else:
            score -= bonus
    return score


def _mobilite_camp(board: chess.Board, couleur: chess.Color) -> int:
    mobilite = 0
    for piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        for case in board.pieces(piece_type, couleur):
            mobilite += len(board.attacks(case))
    return mobilite


def evaluer_mobilite(board: chess.Board) -> int:
    blancs = _mobilite_camp(board, chess.WHITE)
    noirs = _mobilite_camp(board, chess.BLACK)
    return COEF_MOBILITE * (blancs - noirs)


def _roi_a_roque(board: chess.Board, couleur: chess.Color) -> bool:
    roi = board.king(couleur)
    if roi is None:
        return False
    if couleur == chess.WHITE:
        return roi in (chess.G1, chess.C1)
    return roi in (chess.G8, chess.C8)


def _bouclier_pions_roi(board: chess.Board, couleur: chess.Color) -> int:
    """Compte les pions devant le roi roqué."""
    roi = board.king(couleur)
    if roi is None:
        return 0

    if couleur == chess.WHITE:
        if roi == chess.G1:
            cases = (chess.F2, chess.G2, chess.H2, chess.F3, chess.G3, chess.H3)
        elif roi == chess.C1:
            cases = (chess.A2, chess.B2, chess.C2, chess.D2, chess.A3, chess.B3, chess.C3)
        else:
            return 0
    else:
        if roi == chess.G8:
            cases = (chess.F7, chess.G7, chess.H7, chess.F6, chess.G6, chess.H6)
        elif roi == chess.C8:
            cases = (chess.A7, chess.B7, chess.C7, chess.D7, chess.A6, chess.B6, chess.C6)
        else:
            return 0

    return sum(1 for case in cases if board.piece_at(case) == chess.Piece(chess.PAWN, couleur))


def evaluer_securite_roi(board: chess.Board) -> int:
    score = 0
    for couleur in chess.COLORS:
        signe = 1 if couleur == chess.WHITE else -1
        if _roi_a_roque(board, couleur):
            score += signe * BONUS_ROQUE
        score += signe * BONUS_BOUCLIER_PION * _bouclier_pions_roi(board, couleur)
    return score


def _pions_par_colonne(board: chess.Board, couleur: chess.Color) -> list[int]:
    colonnes = [0] * 8
    for case in board.pieces(chess.PAWN, couleur):
        colonnes[chess.square_file(case)] += 1
    return colonnes


def _pions_par_colonne_et_cases(
    board: chess.Board,
    couleur: chess.Color,
) -> tuple[list[int], list[chess.Square]]:
    colonnes = [0] * 8
    cases: list[chess.Square] = []
    for case in board.pieces(chess.PAWN, couleur):
        cases.append(case)
        colonnes[chess.square_file(case)] += 1
    return colonnes, cases


def _pion_passe(
    case: chess.Square,
    couleur: chess.Color,
    pions_ennemis: list[chess.Square],
) -> bool:
    fichier = chess.square_file(case)
    rang = chess.square_rank(case)

    for case_ennemie in pions_ennemis:
        f = chess.square_file(case_ennemie)
        r = chess.square_rank(case_ennemie)
        if abs(f - fichier) > 1:
            continue
        if couleur == chess.WHITE and r > rang:
            return False
        if couleur == chess.BLACK and r < rang:
            return False
    return True


def _pion_passe_board(board: chess.Board, case: chess.Square, couleur: chess.Color) -> bool:
    return _pion_passe(case, couleur, list(board.pieces(chess.PAWN, not couleur)))


def _pion_isole(colonnes: list[int], fichier: int) -> bool:
    gauche = colonnes[fichier - 1] if fichier > 0 else 0
    droite = colonnes[fichier + 1] if fichier < 7 else 0
    return colonnes[fichier] > 0 and gauche == 0 and droite == 0


def _pion_arriere(
    case: chess.Square,
    couleur: chess.Color,
    colonnes: list[int],
    cases_alliees: list[chess.Square],
) -> bool:
    fichier = chess.square_file(case)
    rang = chess.square_rank(case)

    if couleur == chess.WHITE:
        if rang >= 4:
            return False
        for f in (fichier - 1, fichier + 1):
            if 0 <= f <= 7 and colonnes[f] > 0:
                for case_alliee in cases_alliees:
                    if chess.square_file(case_alliee) == f and chess.square_rank(case_alliee) <= rang:
                        return False
        return True

    if rang <= 3:
        return False
    for f in (fichier - 1, fichier + 1):
        if 0 <= f <= 7 and colonnes[f] > 0:
            for case_alliee in cases_alliees:
                if chess.square_file(case_alliee) == f and chess.square_rank(case_alliee) >= rang:
                    return False
    return True


def evaluer_structure_pions(board: chess.Board) -> int:
    score = 0
    for couleur in chess.COLORS:
        signe = 1 if couleur == chess.WHITE else -1
        colonnes, cases_alliees = _pions_par_colonne_et_cases(board, couleur)
        pions_ennemis = list(board.pieces(chess.PAWN, not couleur))

        for fichier, nombre in enumerate(colonnes):
            if nombre > 1:
                score -= signe * MALUS_PION_DOUBLE * (nombre - 1)
            if nombre > 0 and _pion_isole(colonnes, fichier):
                score -= signe * MALUS_PION_ISOLE

        for case in cases_alliees:
            if _pion_arriere(case, couleur, colonnes, cases_alliees):
                score -= signe * MALUS_PION_ARRIERE
            if _pion_passe(case, couleur, pions_ennemis):
                bonus = BONUS_PION_PASSE + chess.square_rank(case) * 4
                if couleur == chess.BLACK:
                    bonus = BONUS_PION_PASSE + (7 - chess.square_rank(case)) * 4
                score += signe * bonus
    return score


def evaluer_clouages(board: chess.Board) -> int:
    """Pénalise les pièces clouées sur leur propre roi (liabilités tactiques)."""
    score = 0
    for couleur in chess.COLORS:
        signe = 1 if couleur == chess.WHITE else -1
        for piece_type, malus in MALUS_CLOUAGE.items():
            for case in board.pieces(piece_type, couleur):
                if board.is_pinned(couleur, case):
                    score -= signe * malus
    return score


def evaluer_paire_fous(board: chess.Board) -> int:
    fous_blancs = len(board.pieces(chess.BISHOP, chess.WHITE))
    fous_noirs = len(board.pieces(chess.BISHOP, chess.BLACK))
    score = 0
    if fous_blancs >= 2:
        score += BONUS_PAIRE_FOUS
    if fous_noirs >= 2:
        score -= BONUS_PAIRE_FOUS
    return score


def _colonne_ouverte(board: chess.Board, fichier: int) -> bool:
    masque_colonne = chess.BB_FILES[fichier]
    return (board.pawns & masque_colonne) == 0


def evaluer_colonnes_ouvertes(board: chess.Board) -> int:
    score = 0
    for couleur in chess.COLORS:
        signe = 1 if couleur == chess.WHITE else -1
        for case in board.pieces(chess.ROOK, couleur):
            if _colonne_ouverte(board, chess.square_file(case)):
                score += signe * BONUS_COLONNE_OUVERTE
    return score


def _distance_chebyshev(case_a: chess.Square, case_b: chess.Square) -> int:
    return max(
        abs(chess.square_file(case_a) - chess.square_file(case_b)),
        abs(chess.square_rank(case_a) - chess.square_rank(case_b)),
    )


def _sans_dames_ni_mineures(board: chess.Board) -> bool:
    for piece_type in (chess.QUEEN, chess.KNIGHT, chess.BISHOP):
        if board.pieces(piece_type, chess.WHITE) or board.pieces(piece_type, chess.BLACK):
            return False
    return True


def est_finale_roi_pion(board: chess.Board) -> bool:
    """Vrai si la position est un roi + pion contre roi."""
    if len(board.piece_map()) != 3:
        return False
    pions = len(board.pieces(chess.PAWN, chess.WHITE)) + len(board.pieces(chess.PAWN, chess.BLACK))
    return pions == 1


def est_finale_tours(board: chess.Board) -> bool:
    """Vrai si la position est une finale de tours (sans dames ni pièces mineures)."""
    if not _sans_dames_ni_mineures(board):
        return False
    tours = len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))
    return tours >= 1


def _opposition(board: chess.Board) -> int:
    """Bonus si les Blancs ont l'opposition (finale)."""
    roi_b = board.king(chess.WHITE)
    roi_n = board.king(chess.BLACK)
    if roi_b is None or roi_n is None:
        return 0

    fb, rb = chess.square_file(roi_b), chess.square_rank(roi_b)
    fn, rn = chess.square_file(roi_n), chess.square_rank(roi_n)

    if fb != fn and rb != rn:
        return 0

    if fb == fn and abs(rb - rn) == 2:
        return 30 if board.turn == chess.BLACK else -30
    if rb == rn and abs(fb - fn) == 2:
        return 30 if board.turn == chess.BLACK else -30
    return 0


def _bonus_roi_actif(roi: chess.Square, coefficient: int) -> int:
    centre = (3 - abs(chess.square_file(roi) - 3)) + (3 - abs(chess.square_rank(roi) - 3))
    return centre * coefficient


def _evaluer_roi_pion_finale(board: chess.Board) -> int:
    """Évaluation spécialisée roi + pion vs roi."""
    score = _opposition(board) * (BONUS_KP_OPPOSITION // 30)

    for couleur in chess.COLORS:
        pions = board.pieces(chess.PAWN, couleur)
        if not pions:
            continue

        signe = 1 if couleur == chess.WHITE else -1
        case_pion = pions.pop()
        roi_allie = board.king(couleur)
        if roi_allie is None:
            continue

        rang = chess.square_rank(case_pion)
        score += signe * BONUS_KP_AVANCE[rang]

        distance = _distance_chebyshev(roi_allie, case_pion)
        if distance <= 1:
            score += signe * BONUS_KP_ROI_PROCHE
        elif distance >= 4:
            score -= signe * MALUS_KP_ROI_LOIN

        # Le roi doit rester derrière ou à côté du pion qui avance.
        if couleur == chess.WHITE and chess.square_rank(roi_allie) > chess.square_rank(case_pion) + 1:
            score -= signe * 25
        if couleur == chess.BLACK and chess.square_rank(roi_allie) < chess.square_rank(case_pion) - 1:
            score -= signe * 25

    return score


def _tour_derrriere_pion_passe(board: chess.Board, couleur: chess.Color) -> int:
    bonus = 0
    signe = 1 if couleur == chess.WHITE else -1

    for case_pion in board.pieces(chess.PAWN, couleur):
        if not _pion_passe_board(board, case_pion, couleur):
            continue
        fichier = chess.square_file(case_pion)
        for case_tour in board.pieces(chess.ROOK, couleur):
            if chess.square_file(case_tour) != fichier:
                continue
            rang_tour = chess.square_rank(case_tour)
            rang_pion = chess.square_rank(case_pion)
            if couleur == chess.WHITE and rang_tour < rang_pion:
                bonus += signe * BONUS_TOUR_DERRIERE_PION
            if couleur == chess.BLACK and rang_tour > rang_pion:
                bonus += signe * BONUS_TOUR_DERRIERE_PION

    return bonus


def _evaluer_tours_finale(board: chess.Board) -> int:
    """Évaluation spécialisée des finales de tours."""
    score = 0

    for couleur in chess.COLORS:
        signe = 1 if couleur == chess.WHITE else -1
        roi = board.king(couleur)
        if roi is not None:
            score += signe * _bonus_roi_actif(roi, COEF_ROI_ACTIF_TOURS)

        rang_7e = 6 if couleur == chess.WHITE else 1
        for case in board.pieces(chess.ROOK, couleur):
            if chess.square_rank(case) == rang_7e:
                score += signe * BONUS_TOUR_7E_RANG

    score += _tour_derrriere_pion_passe(board, chess.WHITE)
    score += _tour_derrriere_pion_passe(board, chess.BLACK)
    return score


def evaluer_finale(board: chess.Board) -> int:
    if est_finale_roi_pion(board):
        return _evaluer_roi_pion_finale(board)

    if est_finale_tours(board):
        return _evaluer_tours_finale(board)

    facteur = _facteur_finale(board)
    if facteur < 128:
        return 0

    score = _opposition(board)

    for couleur in chess.COLORS:
        signe = 1 if couleur == chess.WHITE else -1
        roi = board.king(couleur)
        if roi is not None:
            score += signe * int(_bonus_roi_actif(roi, 6) * facteur / 256)

    return score


def evaluer(board: chess.Board) -> int:
    """
    Évalue la position en centipions du point de vue des Blancs.
    Positif = avantage Blanc, négatif = avantage Noir.
    """
    return (
        evaluer_materiel(board)
        + evaluer_pst(board)
        + _evaluer_centre(board)
        + evaluer_mobilite(board)
        + evaluer_securite_roi(board)
        + evaluer_structure_pions(board)
        + evaluer_paire_fous(board)
        + evaluer_colonnes_ouvertes(board)
        + evaluer_finale(board)
    )
