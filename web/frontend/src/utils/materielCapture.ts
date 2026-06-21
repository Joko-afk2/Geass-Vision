/**
 * Calcule l'avantage matériel à partir d'une FEN, façon chess.com / lichess :
 * pièces capturées par chaque camp + différence de valeur ("+N").
 */

const VALEURS: Record<string, number> = { p: 1, n: 3, b: 3, r: 5, q: 9 };
const DEPART: Record<string, number> = { p: 8, n: 2, b: 2, r: 2, q: 1 };
// Ordre d'affichage des prises (valeur décroissante, pions en dernier).
const ORDRE = ["q", "r", "b", "n", "p"] as const;

export interface PrisePiece {
  /** Code react-chessboard, ex. "bN" (cavalier noir) ou "wP" (pion blanc). */
  code: string;
  nombre: number;
}

export interface BilanMateriel {
  /** Pièces noires capturées par les Blancs. */
  prisesBlanc: PrisePiece[];
  /** Pièces blanches capturées par les Noirs. */
  prisesNoir: PrisePiece[];
  /** Valeur matérielle Blancs − Noirs (positif = avantage blanc). */
  diff: number;
}

export function calculerBilanMateriel(fen: string): BilanMateriel {
  const plateau = fen.split(" ")[0] ?? "";
  const compte: Record<string, number> = {};
  for (const c of plateau) {
    if (/[pnbrqkPNBRQK]/.test(c)) {
      compte[c] = (compte[c] ?? 0) + 1;
    }
  }

  let valeurBlanc = 0;
  let valeurNoir = 0;
  for (const type of ["p", "n", "b", "r", "q"]) {
    valeurNoir += (compte[type] ?? 0) * VALEURS[type];
    valeurBlanc += (compte[type.toUpperCase()] ?? 0) * VALEURS[type];
  }

  const prisesBlanc: PrisePiece[] = [];
  const prisesNoir: PrisePiece[] = [];
  for (const type of ORDRE) {
    const noirManquant = DEPART[type] - (compte[type] ?? 0);
    if (noirManquant > 0) {
      prisesBlanc.push({ code: `b${type.toUpperCase()}`, nombre: noirManquant });
    }
    const blancManquant = DEPART[type] - (compte[type.toUpperCase()] ?? 0);
    if (blancManquant > 0) {
      prisesNoir.push({ code: `w${type.toUpperCase()}`, nombre: blancManquant });
    }
  }

  return { prisesBlanc, prisesNoir, diff: valeurBlanc - valeurNoir };
}
