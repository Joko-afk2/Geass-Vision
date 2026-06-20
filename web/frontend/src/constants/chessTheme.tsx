import type { CustomPieces } from "react-chessboard/dist/chessboard/types";

/** Thème « noyer / ivoire » — distinct du vert Lichess. */
export const COULEUR_CASE_CLAIRE = "#EAD8BE";
export const COULEUR_CASE_SOMBRE = "#9C6B4A";

export const STYLE_PLATEAU = {
  borderRadius: "8px",
  boxShadow: "inset 0 0 0 2px rgba(60, 40, 20, 0.35)",
};

const CODES = [
  "wP",
  "wN",
  "wB",
  "wR",
  "wQ",
  "wK",
  "bP",
  "bN",
  "bB",
  "bR",
  "bQ",
  "bK",
] as const;

type CodePiece = (typeof CODES)[number];

/**
 * Pièces servies en local depuis /pieces/*.svg (jeu « alpha »).
 * Aucune dépendance réseau externe : évite les images cassées.
 */
function pieceImg(code: CodePiece, squareWidth: number) {
  return (
    <img
      src={`/pieces/${code}.svg`}
      alt={code}
      draggable={false}
      style={{ width: squareWidth, height: squareWidth }}
    />
  );
}

export const PIECES_PERSONNALISEES: CustomPieces = Object.fromEntries(
  CODES.map((code) => [
    code,
    ({ squareWidth }: { squareWidth: number }) => pieceImg(code, squareWidth),
  ]),
) as CustomPieces;
