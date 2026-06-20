import type { CustomPieces } from "react-chessboard/dist/chessboard/types";

/** Thème « noyer / ivoire » — distinct du vert Lichess. */
export const COULEUR_CASE_CLAIRE = "#EEDCC6";
export const COULEUR_CASE_SOMBRE = "#AA7055";

export const STYLE_PLATEAU = {
  borderRadius: "8px",
  boxShadow: "inset 0 0 0 2px rgba(60, 40, 20, 0.35)",
};

/** Pièces Wikimedia (style classique, pas cburnett Lichess). */
const URL_PIECES: Record<string, string> = {
  wP: "https://upload.wikimedia.org/wikipedia/commons/4/45/Chess_plt45.svg",
  wN: "https://upload.wikimedia.org/wikipedia/commons/7/70/Chess_nlt45.svg",
  wB: "https://upload.wikimedia.org/wikipedia/commons/b/b1/Chess_blt45.svg",
  wR: "https://upload.wikimedia.org/wikipedia/commons/c/c7/Chess_rlt45.svg",
  wQ: "https://upload.wikimedia.org/wikipedia/commons/1/15/Chess_qlt45.svg",
  wK: "https://upload.wikimedia.org/wikipedia/commons/4/47/Chess_klt45.svg",
  bP: "https://upload.wikimedia.org/wikipedia/commons/c/cf/Chess_pdt45.svg",
  bN: "https://upload.wikimedia.org/wikipedia/commons/e/ef/Chess_ndt45.svg",
  bB: "https://upload.wikimedia.org/wikipedia/commons/9/98/Chess_bdt45.svg",
  bR: "https://upload.wikimedia.org/wikipedia/commons/f/ff/Chess_rdt45.svg",
  bQ: "https://upload.wikimedia.org/wikipedia/commons/4/41/Chess_qdt45.svg",
  bK: "https://upload.wikimedia.org/wikipedia/commons/f/f0/Chess_kdt45.svg",
};

function pieceImg(piece: string, squareWidth: number) {
  return (
    <img
      src={URL_PIECES[piece]}
      alt=""
      draggable={false}
      style={{ width: squareWidth, height: squareWidth }}
    />
  );
}

export const PIECES_PERSONNALISEES: CustomPieces = {
  wP: ({ squareWidth }) => pieceImg("wP", squareWidth),
  wN: ({ squareWidth }) => pieceImg("wN", squareWidth),
  wB: ({ squareWidth }) => pieceImg("wB", squareWidth),
  wR: ({ squareWidth }) => pieceImg("wR", squareWidth),
  wQ: ({ squareWidth }) => pieceImg("wQ", squareWidth),
  wK: ({ squareWidth }) => pieceImg("wK", squareWidth),
  bP: ({ squareWidth }) => pieceImg("bP", squareWidth),
  bN: ({ squareWidth }) => pieceImg("bN", squareWidth),
  bB: ({ squareWidth }) => pieceImg("bB", squareWidth),
  bR: ({ squareWidth }) => pieceImg("bR", squareWidth),
  bQ: ({ squareWidth }) => pieceImg("bQ", squareWidth),
  bK: ({ squareWidth }) => pieceImg("bK", squareWidth),
};
