"""Recherche minimax et alpha-beta — S03…S10/S14."""

from __future__ import annotations

import random
import time

import chess

from chess_engine.engine.evaluation import VALEURS_PIECE, evaluer
from chess_engine.engine.move_ordering import OrdonnancementCoups
from chess_engine.engine.opening_book import livre_actif, livre_ouvertures
from chess_engine.engine.time_manager import GestionnaireTemps
from chess_engine.engine.transposition import TableTransposition, TypeNoeud, Zobrist

# Score de mat : assez grand pour primer sur l'évaluation matérielle.
SCORE_MAT = 100_000
PROFONDEUR_MAX = 32
PROFONDEUR_QUIESCENCE_MAX = 12
REDUCTION_NULL_MOVE = 3

# Élagage SEE des captures perdantes en quiescence.
see_actif = True
# Late Move Reductions (LMR) : on réduit la profondeur des coups tranquilles tardifs.
lmr_actif = True
LMR_PROFONDEUR_MIN = 3
LMR_INDICE_MIN = 3
# Extensions d'échec : on prolonge la recherche quand le camp au trait est en échec.
extensions_actives = True
EXTENSION_MAX = 3


def _valeur_piece(piece_type: chess.PieceType) -> int:
    return VALEURS_PIECE.get(piece_type, 0)


def _capture_la_moins_chere(board: chess.Board, case: chess.Square) -> chess.Move | None:
    """Coup de capture **légal** le moins cher vers `case` (respecte les clouages)."""
    couleur = board.turn
    meilleur_coup: chess.Move | None = None
    meilleure_valeur: int | None = None
    for source in board.attackers(couleur, case):
        piece = board.piece_at(source)
        if piece is None:
            continue
        promotion = None
        if piece.piece_type == chess.PAWN and chess.square_rank(case) in (0, 7):
            promotion = chess.QUEEN
        coup = chess.Move(source, case, promotion=promotion)
        if not board.is_legal(coup):
            continue
        valeur = _valeur_piece(piece.piece_type)
        if meilleure_valeur is None or valeur < meilleure_valeur:
            meilleure_valeur = valeur
            meilleur_coup = coup
    return meilleur_coup


def _see_sur_case(board: chess.Board, case: chess.Square, valeur_sur_case: int) -> int:
    """Gain optimal du camp au trait en reprenant sur `case` (récursif, clouage compris)."""
    reprise = _capture_la_moins_chere(board, case)
    if reprise is None:
        return 0
    attaquant = board.piece_at(reprise.from_square)
    valeur_attaquant = _valeur_piece(attaquant.piece_type) if attaquant else 0
    board.push(reprise)
    gain = valeur_sur_case - _see_sur_case(board, case, valeur_attaquant)
    board.pop()
    # Le camp au trait peut refuser l'échange s'il est défavorable.
    return max(0, gain)


def see_capture(board: chess.Board, coup: chess.Move) -> int:
    """
    Static Exchange Evaluation : gain net (centipions) d'une capture, en
    n'utilisant que des reprises **légales**. Une pièce clouée ne peut donc
    pas reprendre — ce qui corrige les bévues sur pièces clouées.
    """
    case = coup.to_square
    if board.is_en_passant(coup):
        valeur_victime = VALEURS_PIECE[chess.PAWN]
    else:
        victime = board.piece_at(case)
        valeur_victime = _valeur_piece(victime.piece_type) if victime else 0

    attaquant = board.piece_at(coup.from_square)
    if attaquant is None:
        return valeur_victime
    valeur_sur_case = _valeur_piece(attaquant.piece_type)
    if coup.promotion is not None:
        gain_promo = _valeur_piece(coup.promotion) - VALEURS_PIECE[chess.PAWN]
        valeur_victime += gain_promo
        valeur_sur_case = _valeur_piece(coup.promotion)

    board.push(coup)
    resultat = valeur_victime - _see_sur_case(board, case, valeur_sur_case)
    board.pop()
    return resultat

# Compteurs de nœuds explorés (utiles pour comparer minimax vs alpha-beta).
noeuds_minimax = 0
noeuds_alpha_beta = 0

# Ordonnancement des coups (killers, history).
ordonnancement = OrdonnancementCoups()
ordonnancement_actif = True

# Table de transposition.
zobrist = Zobrist()
table_tt = TableTransposition()
tt_actif = True
null_move_actif = True
pvs_actif = True

# Paramètres de niveau Elo (S14).
bruit_evaluation = 0
captures_uniquement = False

# Cache d'évaluation statique (S17) — clé Zobrist → score sans bruit.
_cache_eval_statique: dict[int, int] = {}
TAILLE_MAX_CACHE_EVAL = 200_000

# Gestion du temps (S07).
gestionnaire_temps_actif: GestionnaireTemps | None = None
recherche_interrompue = False
derniere_profondeur_complete = 0
# Profondeur racine entièrement complétée lors du dernier appel itératif (diagnostic).
derniere_profondeur_iterative = 0


def reinitialiser_compteurs() -> None:
    global noeuds_minimax, noeuds_alpha_beta
    noeuds_minimax = 0
    noeuds_alpha_beta = 0
    reinitialiser_caches()


def reinitialiser_caches() -> None:
    """Vide le cache d'évaluation statique."""
    global _cache_eval_statique
    _cache_eval_statique = {}


def obtenir_noeuds_minimax() -> int:
    return noeuds_minimax


def obtenir_noeuds_alpha_beta() -> int:
    return noeuds_alpha_beta


def obtenir_taille_cache_eval() -> int:
    return len(_cache_eval_statique)


def _verifier_temps() -> None:
    global recherche_interrompue
    if gestionnaire_temps_actif is not None and gestionnaire_temps_actif.temps_ecoule():
        recherche_interrompue = True


def _evaluer_position(board: chess.Board, cle: int | None = None) -> int:
    """Évaluation statique, avec bruit optionnel pour les niveaux faibles."""
    if bruit_evaluation == 0 and cle is not None:
        score_cache = _cache_eval_statique.get(cle)
        if score_cache is not None:
            return score_cache

    score = evaluer(board)
    if bruit_evaluation > 0:
        score += random.randint(-bruit_evaluation, bruit_evaluation)
    elif cle is not None and len(_cache_eval_statique) < TAILLE_MAX_CACHE_EVAL:
        _cache_eval_statique[cle] = score
    return score


def _evaluer_terminal(board: chess.Board, profondeur: int, cle: int | None = None) -> int:
    """Évalue une feuille ou une position terminale."""
    if board.is_checkmate():
        return -SCORE_MAT + profondeur if board.turn == chess.WHITE else SCORE_MAT - profondeur

    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    return _evaluer_position(board, cle)


def _coups_ordonnes(
    board: chess.Board,
    niveau: int,
    coup_tt: chess.Move | None = None,
) -> list[chess.Move]:
    coups = list(board.legal_moves)
    if ordonnancement_actif:
        return ordonnancement.ordonner(board, coups, niveau, coup_tt)
    return coups


def _noter_coupure(
    board: chess.Board,
    coup: chess.Move,
    niveau: int,
) -> None:
    if not ordonnancement_actif or board.is_capture(coup):
        return
    ordonnancement.enregistrer_killer(niveau, coup)
    ordonnancement.enregistrer_history(board, coup, niveau)


def _donne_echec(board: chess.Board, coup: chess.Move) -> bool:
    board.push(coup)
    echec = board.is_check()
    board.pop()
    return echec


def _est_coup_tactique(board: chess.Board, coup: chess.Move) -> bool:
    """Capture, promotion ou échec."""
    if board.is_capture(coup) or coup.promotion is not None:
        return True
    return _donne_echec(board, coup)


def _coups_quiescence(
    board: chess.Board,
    niveau: int,
    coup_tt: chess.Move | None = None,
) -> list[chess.Move]:
    tactiques: list[chess.Move] = []
    for coup in board.legal_moves:
        if not _est_coup_tactique(board, coup):
            continue
        # On élague les captures clairement perdantes (SEE < 0). La SEE n'est
        # calculée que lorsqu'on prend avec une pièce plus chère que la victime
        # (seul cas potentiellement perdant), afin de rester rapide.
        if see_actif and board.is_capture(coup) and coup.promotion is None:
            attaquant = board.piece_at(coup.from_square)
            victime = board.piece_at(coup.to_square)
            val_attaquant = _valeur_piece(attaquant.piece_type) if attaquant else 0
            val_victime = (
                _valeur_piece(victime.piece_type)
                if victime
                else VALEURS_PIECE[chess.PAWN]
            )
            if val_attaquant > val_victime and see_capture(board, coup) < 0:
                continue
        tactiques.append(coup)

    if ordonnancement_actif:
        return ordonnancement.ordonner(board, tactiques, niveau, coup_tt)
    return tactiques


def quiescence(
    board: chess.Board,
    alpha: int,
    beta: int,
    niveau: int,
    cle: int | None = None,
    profondeur_qs: int = 0,
) -> int:
    """
    Recherche de quiescence : explore captures, promotions et échecs
    avant d'évaluer statiquement (évite l'effet horizon).
    """
    global noeuds_alpha_beta
    noeuds_alpha_beta += 1

    _verifier_temps()
    if recherche_interrompue:
        return _evaluer_position(board, cle)

    if cle is None:
        cle = zobrist.hash_initial(board)

    if board.is_game_over():
        return _evaluer_terminal(board, 0, cle)

    # Stand-pat : on peut s'arrêter sans capturer si l'éval est déjà suffisante.
    stand_pat = _evaluer_position(board, cle)

    if board.turn == chess.WHITE:
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
    else:
        if stand_pat <= alpha:
            return alpha
        if beta > stand_pat:
            beta = stand_pat

    if profondeur_qs >= PROFONDEUR_QUIESCENCE_MAX:
        return stand_pat

    coups = _coups_quiescence(board, niveau)
    if not coups:
        return stand_pat

    if board.turn == chess.WHITE:
        valeur = alpha
        for coup in coups:
            cle_fils = zobrist.appliquer_coup(cle, board, coup)
            board.push(coup)
            score = quiescence(
                board, alpha, beta, niveau + 1, cle_fils, profondeur_qs + 1
            )
            board.pop()
            if score > valeur:
                valeur = score
            alpha = max(alpha, valeur)
            if alpha >= beta:
                break
        return valeur

    valeur = beta
    for coup in coups:
        cle_fils = zobrist.appliquer_coup(cle, board, coup)
        board.push(coup)
        score = quiescence(
            board, alpha, beta, niveau + 1, cle_fils, profondeur_qs + 1
        )
        board.pop()
        if score < valeur:
            valeur = score
        beta = min(beta, valeur)
        if alpha >= beta:
            break
    return valeur


def _sonder_tt(
    cle: int,
    profondeur: int,
    alpha: int,
    beta: int,
) -> tuple[int | None, chess.Move | None, int, int]:
    """
    Interroge la TT. Retourne (score_cutoff, coup_tt, alpha, beta).
    score_cutoff non None si la recherche peut s'arrêter immédiatement.
    """
    if not tt_actif:
        return None, None, alpha, beta

    entree = table_tt.chercher(cle)
    if entree is None:
        return None, None, alpha, beta

    coup_tt = entree.coup

    if entree.profondeur < profondeur:
        return None, coup_tt, alpha, beta

    table_tt.noter_hit()
    score = entree.score

    if entree.type_noeud == TypeNoeud.EXACT:
        return score, coup_tt, alpha, beta

    if entree.type_noeud == TypeNoeud.BORNE_BASSE:
        alpha = max(alpha, score)
        if alpha >= beta:
            return score, coup_tt, alpha, beta
    elif entree.type_noeud == TypeNoeud.BORNE_HAUTE:
        beta = min(beta, score)
        if alpha >= beta:
            return score, coup_tt, alpha, beta

    return None, coup_tt, alpha, beta


def _en_finale_pions_rois(board: chess.Board) -> bool:
    """Finale simplifiée : uniquement rois et pions sur l'échiquier."""
    pieces = board.occupied
    mineurs_majeurs = pieces & ~board.kings & ~board.pawns
    return mineurs_majeurs == 0


def _peut_null_move(board: chess.Board, profondeur: int) -> bool:
    """Garde-fous : pas de null move en échec, en finale ou en profondeur faible."""
    if not null_move_actif:
        return False
    if profondeur < REDUCTION_NULL_MOVE + 1:
        return False
    if board.is_check():
        return False
    if _en_finale_pions_rois(board):
        return False
    return True


def _hash_null_move(cle: int) -> int:
    """Le null move inverse uniquement le trait au trait."""
    return cle ^ zobrist.cle_trait_blanc


def minimax(board: chess.Board, profondeur: int) -> int:
    """
    Minimax classique. Retourne un score du point de vue des Blancs.
    profondeur = nombre de demi-coups (plies) restants à explorer.
    """
    global noeuds_minimax
    noeuds_minimax += 1

    if profondeur == 0 or board.is_game_over():
        return _evaluer_terminal(board, profondeur)

    if board.turn == chess.WHITE:
        meilleur = -SCORE_MAT * 2
        for coup in board.legal_moves:
            board.push(coup)
            score = minimax(board, profondeur - 1)
            board.pop()
            meilleur = max(meilleur, score)
        return meilleur

    pire = SCORE_MAT * 2
    for coup in board.legal_moves:
        board.push(coup)
        score = minimax(board, profondeur - 1)
        board.pop()
        pire = min(pire, score)
    return pire


def _reduction_lmr(
    board: chess.Board,
    coup: chess.Move,
    profondeur: int,
    indice: int,
    en_echec: bool,
) -> int:
    """Réduction de profondeur pour les coups tranquilles tardifs (LMR)."""
    if not lmr_actif:
        return 0
    if profondeur < LMR_PROFONDEUR_MIN or indice < LMR_INDICE_MIN:
        return 0
    if en_echec:
        return 0
    # Coups tranquilles uniquement (les captures/promotions gardent leur profondeur).
    # On évite volontairement un test d'échec coûteux (push/pop) : la re-recherche
    # PVS à pleine profondeur rattrape les rares coups réduits à tort.
    if board.is_capture(coup) or coup.promotion is not None:
        return 0
    return 2 if indice >= 6 else 1


def alpha_beta(
    board: chess.Board,
    profondeur: int,
    alpha: int,
    beta: int,
    niveau: int = 1,
    cle: int | None = None,
    pv: list[chess.Move] | None = None,
    extensions_utilisees: int = 0,
) -> int:
    """
    Alpha-beta avec PVS (Principal Variation Search), extensions d'échec et LMR.
    niveau = profondeur depuis la racine (pour killers / history).
    pv = liste remplie avec la ligne principale de ce sous-arbre.
    """
    global noeuds_alpha_beta
    noeuds_alpha_beta += 1

    _verifier_temps()
    if recherche_interrompue:
        return _evaluer_terminal(board, profondeur, cle)

    alpha_orig, beta_orig = alpha, beta

    if cle is None:
        cle = zobrist.hash_initial(board)

    # Extension d'échec : on prolonge la recherche tant que le camp est en échec.
    en_echec = extensions_actives and board.is_check()
    if (
        en_echec
        and extensions_utilisees < EXTENSION_MAX
        and not board.is_game_over()
    ):
        profondeur += 1
        extensions_utilisees += 1

    if profondeur == 0 or board.is_game_over():
        if board.is_game_over():
            score = _evaluer_terminal(board, profondeur, cle)
        else:
            score = quiescence(board, alpha, beta, niveau, cle)
        if tt_actif and board.is_game_over():
            table_tt.stocker(cle, profondeur, score, alpha_orig, beta_orig, None)
        if pv is not None:
            pv.clear()
        return score

    score_tt, coup_tt, alpha, beta = _sonder_tt(cle, profondeur, alpha, beta)
    if score_tt is not None:
        if pv is not None:
            pv.clear()
            if coup_tt is not None:
                pv.append(coup_tt)
        return score_tt

    if _peut_null_move(board, profondeur):
        board.push(chess.Move.null())
        cle_null = _hash_null_move(cle)
        prof_null = profondeur - 1 - REDUCTION_NULL_MOVE
        score_null = alpha_beta(
            board, prof_null, alpha, beta, niveau + 1, cle_null,
            extensions_utilisees=extensions_utilisees,
        )
        board.pop()

        if board.turn == chess.WHITE and score_null >= beta:
            if pv is not None:
                pv.clear()
            return beta
        if board.turn == chess.BLACK and score_null <= alpha:
            if pv is not None:
                pv.clear()
            return alpha

    coups = _coups_ordonnes(board, niveau, coup_tt)
    meilleur_coup: chess.Move | None = coup_tt
    pv_enfants: list[chess.Move] = []

    if board.turn == chess.WHITE:
        valeur = -SCORE_MAT * 2
        for indice, coup in enumerate(coups):
            reduction = _reduction_lmr(board, coup, profondeur, indice, en_echec)
            cle_fils = zobrist.appliquer_coup(cle, board, coup)
            board.push(coup)
            ligne_fils: list[chess.Move] = []

            if not pvs_actif or indice == 0:
                score = alpha_beta(
                    board, profondeur - 1, alpha, beta, niveau + 1, cle_fils, ligne_fils,
                    extensions_utilisees,
                )
            else:
                score = alpha_beta(
                    board, profondeur - 1 - reduction, alpha, alpha + 1,
                    niveau + 1, cle_fils, None, extensions_utilisees,
                )
                if reduction and score > alpha:
                    score = alpha_beta(
                        board, profondeur - 1, alpha, alpha + 1,
                        niveau + 1, cle_fils, None, extensions_utilisees,
                    )
                if alpha < score < beta:
                    score = alpha_beta(
                        board, profondeur - 1, alpha, beta, niveau + 1, cle_fils, ligne_fils,
                        extensions_utilisees,
                    )

            board.pop()
            if score > valeur:
                valeur = score
                meilleur_coup = coup
                pv_enfants = ligne_fils
            alpha = max(alpha, valeur)
            if alpha >= beta:
                _noter_coupure(board, coup, niveau)
                break
    else:
        valeur = SCORE_MAT * 2
        for indice, coup in enumerate(coups):
            reduction = _reduction_lmr(board, coup, profondeur, indice, en_echec)
            cle_fils = zobrist.appliquer_coup(cle, board, coup)
            board.push(coup)
            ligne_fils: list[chess.Move] = []

            if not pvs_actif or indice == 0:
                score = alpha_beta(
                    board, profondeur - 1, alpha, beta, niveau + 1, cle_fils, ligne_fils,
                    extensions_utilisees,
                )
            else:
                score = alpha_beta(
                    board, profondeur - 1 - reduction, beta - 1, beta,
                    niveau + 1, cle_fils, None, extensions_utilisees,
                )
                if reduction and score < beta:
                    score = alpha_beta(
                        board, profondeur - 1, beta - 1, beta,
                        niveau + 1, cle_fils, None, extensions_utilisees,
                    )
                if alpha < score < beta:
                    score = alpha_beta(
                        board, profondeur - 1, alpha, beta, niveau + 1, cle_fils, ligne_fils,
                        extensions_utilisees,
                    )

            board.pop()
            if score < valeur:
                valeur = score
                meilleur_coup = coup
                pv_enfants = ligne_fils
            beta = min(beta, valeur)
            if alpha >= beta:
                _noter_coupure(board, coup, niveau)
                break

    if pv is not None:
        pv.clear()
        if meilleur_coup is not None:
            pv.append(meilleur_coup)
            pv.extend(pv_enfants)

    if tt_actif:
        table_tt.stocker(cle, profondeur, valeur, alpha_orig, beta_orig, meilleur_coup)

    return valeur


def _coups_racine(board: chess.Board) -> list[chess.Move]:
    """Coups candidats à la racine (filtrés pour les niveaux faibles)."""
    coups = list(board.legal_moves)
    if captures_uniquement:
        tactiques = [coup for coup in coups if board.is_capture(coup) or coup.promotion]
        if tactiques:
            return tactiques
    return coups


def _coups_racine_ordonnes(board: chess.Board) -> list[chess.Move]:
    coups = _coups_racine(board)
    if ordonnancement_actif:
        return ordonnancement.ordonner(board, coups, 1, None)
    return coups


def scores_coups_racine(board: chess.Board, profondeur: int) -> list[tuple[chess.Move, int]]:
    """Évalue chaque coup racine à la profondeur donnée (perspective Blancs)."""
    global recherche_interrompue
    recherche_interrompue = False

    coups = _coups_racine_ordonnes(board)
    if not coups:
        return []

    ordonnancement.reinitialiser()
    table_tt.reinitialiser()
    reinitialiser_caches()

    cle_racine = zobrist.hash_initial(board)
    resultats: list[tuple[chess.Move, int]] = []
    alpha = -SCORE_MAT * 2
    beta = SCORE_MAT * 2

    for coup in coups:
        if recherche_interrompue:
            break
        cle_fils = zobrist.appliquer_coup(cle_racine, board, coup)
        board.push(coup)
        score = alpha_beta(board, max(0, profondeur - 1), alpha, beta, niveau=2, cle=cle_fils)
        board.pop()
        resultats.append((coup, score))

    return resultats


def _trouver_meilleur_coup_profondeur(
    board: chess.Board,
    profondeur: int,
    reinit_tt: bool = True,
) -> chess.Move | None:
    """Alpha-beta à profondeur fixe. Optionnellement réinitialise killers/history/TT."""
    if reinit_tt:
        ordonnancement.reinitialiser()
        table_tt.reinitialiser()
        reinitialiser_caches()

    coups = _coups_racine_ordonnes(board)
    if not coups:
        return None

    cle_racine = zobrist.hash_initial(board)
    meilleur_coup: chess.Move | None = None

    if board.turn == chess.WHITE:
        alpha = -SCORE_MAT * 2
        beta = SCORE_MAT * 2
        meilleur_score = alpha

        for coup in coups:
            if recherche_interrompue:
                break
            cle_fils = zobrist.appliquer_coup(cle_racine, board, coup)
            board.push(coup)
            score = alpha_beta(board, profondeur - 1, alpha, beta, niveau=2, cle=cle_fils)
            board.pop()
            if recherche_interrompue:
                break
            if score > meilleur_score:
                meilleur_score = score
                meilleur_coup = coup
            alpha = max(alpha, meilleur_score)
    else:
        alpha = -SCORE_MAT * 2
        beta = SCORE_MAT * 2
        meilleur_score = beta

        for coup in coups:
            if recherche_interrompue:
                break
            cle_fils = zobrist.appliquer_coup(cle_racine, board, coup)
            board.push(coup)
            score = alpha_beta(board, profondeur - 1, alpha, beta, niveau=2, cle=cle_fils)
            board.pop()
            if recherche_interrompue:
                break
            if score < meilleur_score:
                meilleur_score = score
                meilleur_coup = coup
            beta = min(beta, meilleur_score)

    return meilleur_coup


def trouver_meilleur_coup(board: chess.Board, profondeur: int) -> chess.Move | None:
    """Retourne le meilleur coup selon alpha-beta à la profondeur donnée."""
    global recherche_interrompue
    recherche_interrompue = False

    if livre_actif:
        coup_livre = livre_ouvertures.coup_livre(board)
        if coup_livre is not None:
            return coup_livre

    return _trouver_meilleur_coup_profondeur(board, profondeur, reinit_tt=True)


class _GardeTemps:
    """Borne dure de temps (budget fixe par coup), indépendante de la cadence."""

    def __init__(self, budget_secondes: float) -> None:
        self.deadline = time.perf_counter() + max(0.05, budget_secondes)

    def temps_ecoule(self) -> bool:
        return time.perf_counter() >= self.deadline


def scores_coups_racine_iteratif(
    board: chess.Board,
    profondeur_max: int,
    budget_secondes: float,
) -> list[tuple[chess.Move, int]]:
    """
    Approfondissement itératif borné en temps à la racine.

    Renvoie les scores de la dernière profondeur **entièrement** calculée
    (perspective Blancs). Garantit toujours au moins un résultat (profondeur 1)
    afin qu'un coup soit toujours disponible, même si le budget est minuscule.
    """
    global gestionnaire_temps_actif, recherche_interrompue, derniere_profondeur_iterative

    coups = _coups_racine_ordonnes(board)
    if not coups:
        return []

    derniere_profondeur_iterative = 0
    garde = _GardeTemps(budget_secondes)
    gestionnaire_temps_actif = garde

    ordonnancement.reinitialiser()
    table_tt.reinitialiser()
    reinitialiser_caches()

    cle_racine = zobrist.hash_initial(board)
    blancs_au_trait = board.turn == chess.WHITE
    meilleurs: list[tuple[chess.Move, int]] = [(coup, 0) for coup in coups]

    try:
        for profondeur in range(1, max(1, profondeur_max) + 1):
            recherche_interrompue = False
            resultats: list[tuple[chess.Move, int]] = []
            complet = True
            alpha = -SCORE_MAT * 2
            beta = SCORE_MAT * 2

            for coup in coups:
                if recherche_interrompue:
                    complet = False
                    break
                cle_fils = zobrist.appliquer_coup(cle_racine, board, coup)
                board.push(coup)
                score = alpha_beta(
                    board, max(0, profondeur - 1), alpha, beta, niveau=2, cle=cle_fils
                )
                board.pop()
                if recherche_interrompue:
                    complet = False
                    break
                resultats.append((coup, score))

            if complet and resultats:
                meilleurs = resultats
                derniere_profondeur_iterative = profondeur
                coups = [
                    coup
                    for coup, _ in sorted(
                        resultats, key=lambda paire: paire[1], reverse=blancs_au_trait
                    )
                ]
                # Mat forcé trouvé : inutile d'approfondir davantage.
                if any(abs(score) >= SCORE_MAT - 1000 for _, score in meilleurs):
                    break
            else:
                break

            if garde.temps_ecoule():
                break

        return meilleurs
    finally:
        gestionnaire_temps_actif = None
        recherche_interrompue = False


def recherche_approfondissement(
    board: chess.Board,
    gestionnaire: GestionnaireTemps,
) -> tuple[chess.Move | None, int]:
    """
    Iterative deepening jusqu'au timeout.
    Retourne (meilleur_coup, dernière_profondeur_complète).
    """
    global gestionnaire_temps_actif, recherche_interrompue, derniere_profondeur_complete

    gestionnaire_temps_actif = gestionnaire
    gestionnaire.demarrer_coup(board)

    if livre_actif:
        coup_livre = livre_ouvertures.coup_livre(board)
        if coup_livre is not None:
            return coup_livre, 0

    ordonnancement.reinitialiser()
    table_tt.reinitialiser()
    reinitialiser_caches()

    meilleur_coup: chess.Move | None = None
    derniere_profondeur_complete = 0

    for profondeur in range(1, PROFONDEUR_MAX + 1):
        recherche_interrompue = False
        coup = _trouver_meilleur_coup_profondeur(board, profondeur, reinit_tt=False)

        if recherche_interrompue:
            break

        if coup is not None:
            meilleur_coup = coup
            derniere_profondeur_complete = profondeur

        if gestionnaire.temps_ecoule():
            break

    gestionnaire_temps_actif = None
    return meilleur_coup, derniere_profondeur_complete
