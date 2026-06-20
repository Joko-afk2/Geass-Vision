export interface AnalyseCoup {
  numero: number;
  coup: string;
  couleur: string;
  eval_avant: number;
  eval_apres: number;
  meilleur_coup: string | null;
  perte_cp: number;
  categorie: string;
}

export interface RapportAnalyse {
  event: string;
  blancs: string;
  noirs: string;
  resultat: string;
  coups: AnalyseCoup[];
  precision_blancs: number;
  precision_noirs: number;
}

async function lireErreur(reponse: Response): Promise<string> {
  try {
    const corps = await reponse.json();
    if (typeof corps.detail === "string") {
      return corps.detail;
    }
  } catch {
    // ignore
  }
  return `Erreur HTTP ${reponse.status}`;
}

export async function analyserPartie(
  gameId: string,
  profondeur = 2,
): Promise<RapportAnalyse> {
  const reponse = await fetch(
    `/api/game/${gameId}/analyze?profondeur=${profondeur}`,
  );
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function analyserPgn(
  pgn: string,
  profondeur = 2,
): Promise<RapportAnalyse> {
  const reponse = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pgn, profondeur }),
  });
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export const LIBELLES_CATEGORIE: Record<string, string> = {
  brilliant: "Brillant",
  excellent: "Excellent",
  best: "Meilleur",
  good: "Bon",
  inaccuracy: "Imprécision",
  mistake: "Erreur",
  blunder: "Gaffe",
};
