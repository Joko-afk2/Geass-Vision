"""Point d'entrée CLI — partie humain vs moteur."""

from __future__ import annotations

import argparse

import chess

from chess_engine.engine.engine import MoteurEchecs


def afficher_plateau(board: chess.Board) -> None:
    print()
    print(board)
    print()
    if board.is_check():
        print("Échec !")
    if board.is_checkmate():
        print("Échec et mat.")
    elif board.is_stalemate():
        print("Pat — partie nulle.")
    elif board.is_insufficient_material():
        print("Matériel insuffisant — partie nulle.")
    elif board.is_repetition(3):
        print("Triple répétition — partie nulle.")
    elif board.is_fifty_moves():
        print("Règle des 50 coups — partie nulle.")


def coup_moteur(moteur: MoteurEchecs, board: chess.Board) -> chess.Move:
    """Demande un coup au moteur et vérifie qu'il est légal."""
    coup = moteur.choisir_coup(board)
    if coup is None or coup not in board.legal_moves:
        raise RuntimeError("Le moteur n'a pas trouvé de coup légal.")
    return coup


def lire_coup_humain(board: chess.Board) -> chess.Move | None:
    """Lit un coup en notation algébrique (ex. e2e4, e7e8q)."""
    while True:
        try:
            saisie = input("Votre coup (UCI, 'quit' pour quitter) : ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if saisie in ("quit", "q", "exit"):
            return None

        try:
            coup = chess.Move.from_uci(saisie)
        except ValueError:
            print("Format invalide. Exemple : e2e4")
            continue

        if coup not in board.legal_moves:
            print("Coup illégal.")
            continue

        return coup


def lire_niveau_elo() -> int:
    """Lit le niveau Elo souhaité (1–2000)."""
    while True:
        try:
            saisie = input("Niveau du moteur (1–2000, Entrée = 1200) : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1200

        if not saisie:
            return 1200

        try:
            niveau = int(saisie)
        except ValueError:
            print("Entrez un nombre entre 1 et 2000.")
            continue

        if 1 <= niveau <= 2000:
            return niveau
        print("Le niveau doit être compris entre 1 et 2000.")


def jouer_partie(elo: int | None = None) -> None:
    if elo is None:
        elo = lire_niveau_elo()

    moteur = MoteurEchecs(elo)
    board = chess.Board()

    print("=== Moteur d'échecs ===")
    print(f"Vous jouez les Blancs. Niveau moteur : {elo} Elo.")
    print("Entrez vos coups en notation UCI (ex. e2e4).")

    while not board.is_game_over(claim_draw=True):
        afficher_plateau(board)

        if board.turn == chess.WHITE:
            coup = lire_coup_humain(board)
            if coup is None:
                print("Partie abandonnée.")
                return
        else:
            coup = coup_moteur(moteur, board)
            print(f"Moteur joue : {coup.uci()}")

        board.push(coup)

    afficher_plateau(board)
    print(f"Résultat : {board.result(claim_draw=True)}")


def main() -> None:
    parseur = argparse.ArgumentParser(description="Jouer contre le moteur d'échecs.")
    parseur.add_argument(
        "--elo",
        type=int,
        default=None,
        help="Niveau Elo du moteur (1–2000). Sans argument, demandé au lancement.",
    )
    arguments = parseur.parse_args()
    jouer_partie(arguments.elo)


if __name__ == "__main__":
    main()
