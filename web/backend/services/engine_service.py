"""Service de gestion des parties humain vs moteur — W02."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from uuid import uuid4

import chess
import chess.pgn

from chess_engine.engine.engine import MoteurEchecs, parametres_depuis_elo
from chess_engine.engine.evaluation import evaluer
import chess_engine.engine.search as search_module
from chess_engine.engine.search import scores_coups_racine


@dataclass
class Partie:
    id: str
    board: chess.Board
    elo: int
    couleur_humain: chess.Color
    historique_uci: list[str] = field(default_factory=list)


@dataclass
class EtatPartie:
    game_id: str
    fen: str
    turn: str
    evaluation: int
    elo: int
    human_color: str
    moves: list[str]
    is_game_over: bool
    result: str | None
    is_human_turn: bool


@dataclass
class ResultatCoup:
    fen: str
    turn: str
    evaluation: int
    human_move: str
    engine_move: str | None
    is_game_over: bool
    result: str | None


@dataclass
class SuggestionCoup:
    uci: str
    san: str
    score: int


@dataclass
class PieceMenacee:
    square: str
    piece: str
    attackers: int
    defenders: int
    undefended: bool


@dataclass
class MenacesPartie:
    threatened_pieces: list[PieceMenacee]
    critical_squares: list[str]


def _couleur_depuis_chaine(nom: str) -> chess.Color:
    if nom == "white":
        return chess.WHITE
    if nom == "black":
        return chess.BLACK
    raise ValueError("Couleur invalide : white ou black attendu.")


def _nom_couleur(couleur: chess.Color) -> str:
    return "white" if couleur == chess.WHITE else "black"


def _resultat_partie(board: chess.Board) -> str | None:
    if board.is_checkmate():
        return "0-1" if board.turn == chess.WHITE else "1-0"
    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.is_seventyfive_moves()
        or board.is_fivefold_repetition()
    ):
        return "1/2-1/2"
    return None


class ServiceMoteur:
    """Parties en mémoire et coups du moteur selon le niveau Elo."""

    def __init__(self) -> None:
        self._parties: dict[str, Partie] = {}

    def reinitialiser(self) -> None:
        self._parties.clear()

    def nouvelle_partie(
        self,
        elo: int,
        couleur_humain: str,
        fen: str | None = None,
    ) -> tuple[Partie, str | None]:
        """
        Crée une partie. Si l'humain joue les Noirs, le moteur joue le premier coup.
        Retourne (partie, coup_moteur_uci ou None).
        """
        elo = max(1, min(2000, elo))
        couleur = _couleur_depuis_chaine(couleur_humain)
        board = chess.Board(fen) if fen else chess.Board()

        partie = Partie(
            id=str(uuid4()),
            board=board,
            elo=elo,
            couleur_humain=couleur,
        )
        self._parties[partie.id] = partie

        coup_moteur: str | None = None
        if not _resultat_partie(board) and board.turn != couleur:
            coup = self._choisir_coup_moteur(partie)
            if coup is not None:
                board.push(coup)
                partie.historique_uci.append(coup.uci())
                coup_moteur = coup.uci()

        return partie, coup_moteur

    def charger_fen(
        self,
        fen: str,
        elo: int,
        couleur_humain: str,
    ) -> tuple[Partie, str | None]:
        """Crée une partie à partir d'une position FEN."""
        try:
            chess.Board(fen)
        except ValueError as erreur:
            raise ValueError("FEN invalide.") from erreur
        return self.nouvelle_partie(elo, couleur_humain, fen=fen)

    def importer_pgn(
        self,
        pgn_texte: str,
        elo: int,
        couleur_humain: str,
    ) -> tuple[Partie, str | None]:
        """Rejoue un PGN et crée une partie à la position finale."""
        partie_pgn = chess.pgn.read_game(StringIO(pgn_texte))
        if partie_pgn is None:
            raise ValueError("PGN invalide ou vide.")

        elo = max(1, min(2000, elo))
        couleur = _couleur_depuis_chaine(couleur_humain)
        board = partie_pgn.board()

        partie = Partie(
            id=str(uuid4()),
            board=board,
            elo=elo,
            couleur_humain=couleur,
        )

        for coup in partie_pgn.mainline_moves():
            board.push(coup)
            partie.historique_uci.append(coup.uci())

        self._parties[partie.id] = partie

        coup_moteur: str | None = None
        if not _resultat_partie(board) and board.turn != couleur:
            coup = self._choisir_coup_moteur(partie)
            if coup is not None:
                board.push(coup)
                partie.historique_uci.append(coup.uci())
                coup_moteur = coup.uci()

        return partie, coup_moteur

    def exporter_fen(self, game_id: str) -> str:
        partie = self._obtenir_partie(game_id)
        return partie.board.fen()

    def exporter_pgn(self, game_id: str) -> str:
        partie = self._obtenir_partie(game_id)
        if partie.couleur_humain == chess.WHITE:
            blancs, noirs = "Humain", "Moteur"
        else:
            blancs, noirs = "Moteur", "Humain"

        jeu = chess.pgn.Game()
        jeu.headers["Event"] = "Partie web"
        jeu.headers["Site"] = "Moteur d'échecs"
        jeu.headers["White"] = blancs
        jeu.headers["Black"] = noirs
        jeu.headers["Result"] = _resultat_partie(partie.board) or "*"

        noeud = jeu
        for uci in partie.historique_uci:
            coup = chess.Move.from_uci(uci)
            noeud = noeud.add_variation(coup)

        sortie = StringIO()
        print(jeu, file=sortie)
        return sortie.getvalue()

    def obtenir_etat(self, game_id: str) -> EtatPartie:
        partie = self._obtenir_partie(game_id)
        return self._construire_etat(partie)

    def obtenir_suggestions(self, game_id: str, nombre: int = 3) -> list[SuggestionCoup]:
        """Top N coups pour le camp au trait (scores en perspective Blancs)."""
        partie = self._obtenir_partie(game_id)
        board = partie.board

        if _resultat_partie(board):
            return []

        parametres = parametres_depuis_elo(partie.elo)
        profondeur = max(2, min(4, parametres.profondeur_max))

        ancien_bruit = search_module.bruit_evaluation
        ancien_livre = search_module.livre_actif
        search_module.bruit_evaluation = 0
        search_module.livre_actif = False
        try:
            scores = scores_coups_racine(board, profondeur)
        finally:
            search_module.bruit_evaluation = ancien_bruit
            search_module.livre_actif = ancien_livre

        if not scores:
            return []

        if board.turn == chess.WHITE:
            scores.sort(key=lambda paire: paire[1], reverse=True)
        else:
            scores.sort(key=lambda paire: paire[1])

        suggestions: list[SuggestionCoup] = []
        for coup, score in scores[:nombre]:
            suggestions.append(
                SuggestionCoup(
                    uci=coup.uci(),
                    san=board.san(coup),
                    score=score,
                )
            )
        return suggestions

    def obtenir_menaces(self, game_id: str) -> MenacesPartie:
        """Pièces humaines attaquées et cases critiques (attaquants, roi en échec)."""
        partie = self._obtenir_partie(game_id)
        board = partie.board

        if _resultat_partie(board):
            return MenacesPartie(threatened_pieces=[], critical_squares=[])

        humain = partie.couleur_humain
        ennemi = not humain
        pieces_menacees: list[PieceMenacee] = []
        cases_critiques: set[str] = set()

        for case in chess.SQUARES:
            piece = board.piece_at(case)
            if piece is None or piece.color != humain:
                continue
            if not board.is_attacked_by(ennemi, case):
                continue

            nb_attaquants = len(board.attackers(ennemi, case))
            nb_defenseurs = len(board.attackers(humain, case))
            nom_case = chess.square_name(case)

            pieces_menacees.append(
                PieceMenacee(
                    square=nom_case,
                    piece=piece.symbol(),
                    attackers=nb_attaquants,
                    defenders=nb_defenseurs,
                    undefended=nb_defenseurs == 0,
                )
            )
            cases_critiques.add(nom_case)

            for case_attaquant in board.attackers(ennemi, case):
                cases_critiques.add(chess.square_name(case_attaquant))

        roi = board.king(humain)
        if roi is not None and board.is_attacked_by(ennemi, roi):
            cases_critiques.add(chess.square_name(roi))

        return MenacesPartie(
            threatened_pieces=pieces_menacees,
            critical_squares=sorted(cases_critiques),
        )

    def jouer_coup_humain(self, game_id: str, uci: str) -> ResultatCoup:
        partie = self._obtenir_partie(game_id)
        board = partie.board

        if _resultat_partie(board):
            raise ValueError("La partie est déjà terminée.")

        if board.turn != partie.couleur_humain:
            raise ValueError("Ce n'est pas le tour du joueur humain.")

        try:
            coup = chess.Move.from_uci(uci)
        except ValueError as erreur:
            raise ValueError("Coup UCI invalide.") from erreur

        if coup not in board.legal_moves:
            raise ValueError("Coup illégal.")

        board.push(coup)
        partie.historique_uci.append(coup.uci())

        coup_moteur: str | None = None
        if not _resultat_partie(board) and board.turn != partie.couleur_humain:
            coup = self._choisir_coup_moteur(partie)
            if coup is not None:
                board.push(coup)
                partie.historique_uci.append(coup.uci())
                coup_moteur = coup.uci()

        return ResultatCoup(
            fen=board.fen(),
            turn=_nom_couleur(board.turn),
            evaluation=evaluer(board),
            human_move=uci,
            engine_move=coup_moteur,
            is_game_over=_resultat_partie(board) is not None,
            result=_resultat_partie(board),
        )

    def _obtenir_partie(self, game_id: str) -> Partie:
        partie = self._parties.get(game_id)
        if partie is None:
            raise KeyError("Partie introuvable.")
        return partie

    def _choisir_coup_moteur(self, partie: Partie) -> chess.Move | None:
        moteur = MoteurEchecs(elo=partie.elo)
        coup = moteur.choisir_coup(partie.board)
        if coup is None or coup not in partie.board.legal_moves:
            return None
        return coup

    def _construire_etat(self, partie: Partie) -> EtatPartie:
        board = partie.board
        return EtatPartie(
            game_id=partie.id,
            fen=board.fen(),
            turn=_nom_couleur(board.turn),
            evaluation=evaluer(board),
            elo=partie.elo,
            human_color=_nom_couleur(partie.couleur_humain),
            moves=list(partie.historique_uci),
            is_game_over=_resultat_partie(board) is not None,
            result=_resultat_partie(board),
            is_human_turn=board.turn == partie.couleur_humain
            and _resultat_partie(board) is None,
        )


service_moteur = ServiceMoteur()
