/** Reconstruit une FEN à partir d'une liste de coups UCI. */

import { Chess } from "chess.js";

export function fenDepuisHistorique(
  coups: string[],
  jusquA: number,
  fenDepart?: string,
): string {
  const echecs = new Chess(fenDepart);
  const limite = Math.min(jusquA, coups.length);
  for (let i = 0; i < limite; i += 1) {
    const uci = coups[i];
    echecs.move({
      from: uci.slice(0, 2),
      to: uci.slice(2, 4),
      promotion: uci.length > 4 ? uci[4] : undefined,
    });
  }
  return echecs.fen();
}

export function coupsEnNotation(
  coups: string[],
  fenDepart?: string,
): string[] {
  const echecs = new Chess(fenDepart);
  return coups.map((uci) => {
    const coup = echecs.move({
      from: uci.slice(0, 2),
      to: uci.slice(2, 4),
      promotion: uci.length > 4 ? uci[4] : undefined,
    });
    return coup?.san ?? uci;
  });
}
