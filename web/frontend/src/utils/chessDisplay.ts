export interface Suggestion {
  uci: string;
  san: string;
  score: number;
}

export function uciVersCases(uci: string): [string, string] {
  return [uci.slice(0, 2), uci.slice(2, 4)];
}

export function scoreVersTexte(score: number): string {
  const pions = score / 100;
  const signe = pions > 0 ? "+" : "";
  return `${signe}${pions.toFixed(1)}`;
}

export function evaluationVersPourcentage(centipions: number): number {
  const borne = Math.max(-800, Math.min(800, centipions));
  return 50 + (borne / 800) * 50;
}
