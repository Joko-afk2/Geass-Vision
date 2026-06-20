/** FEN de départ standard (remplace le raccourci "start" de react-chessboard). */

export const FEN_DEPART =
  "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

export function fenPourChess(fen?: string): string | undefined {
  if (!fen || fen === "start") {
    return undefined;
  }
  return fen;
}

export function fenPourAffichage(fen: string): string {
  return fen === "start" ? FEN_DEPART : fen;
}
