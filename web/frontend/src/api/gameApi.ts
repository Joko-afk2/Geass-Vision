export interface NouvellePartieReponse {
  game_id: string;
  fen: string;
  turn: string;
  evaluation: number;
  elo: number;
  human_color: "white" | "black";
  engine_move: string | null;
  is_game_over: boolean;
  result: string | null;
  is_human_turn: boolean;
}

export interface CoupReponse {
  fen: string;
  turn: string;
  evaluation: number;
  human_move: string;
  engine_move: string | null;
  is_game_over: boolean;
  result: string | null;
}

export interface EtatPartie {
  game_id: string;
  fen: string;
  turn: string;
  evaluation: number;
  elo: number;
  human_color: "white" | "black";
  moves: string[];
  is_game_over: boolean;
  result: string | null;
  is_human_turn: boolean;
}

export interface Suggestion {
  uci: string;
  san: string;
  score: number;
}

const BASE = "/api/game";

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

export async function creerPartie(
  elo = 1200,
  humanColor: "white" | "black" | "random" = "white",
  fen?: string,
): Promise<NouvellePartieReponse> {
  const reponse = await fetch(`${BASE}/new`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ elo, human_color: humanColor, fen }),
  });
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function chargerFen(
  fen: string,
  elo = 1200,
  humanColor: "white" | "black" | "random" = "white",
): Promise<NouvellePartieReponse> {
  const reponse = await fetch(`${BASE}/load-fen`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fen, elo, human_color: humanColor }),
  });
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function importerPgn(
  pgn: string,
  elo = 1200,
  humanColor: "white" | "black" | "random" = "white",
): Promise<NouvellePartieReponse> {
  const reponse = await fetch(`${BASE}/import-pgn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pgn, elo, human_color: humanColor }),
  });
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function exporterFen(gameId: string): Promise<{ fen: string }> {
  const reponse = await fetch(`${BASE}/${gameId}/fen`);
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function exporterPgn(gameId: string): Promise<{ pgn: string }> {
  const reponse = await fetch(`${BASE}/${gameId}/pgn`);
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function jouerCoup(
  gameId: string,
  uci: string,
): Promise<CoupReponse> {
  const reponse = await fetch(`${BASE}/${gameId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ uci }),
  });
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function obtenirEtat(gameId: string): Promise<EtatPartie> {
  const reponse = await fetch(`${BASE}/${gameId}/state`);
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}

export async function obtenirSuggestions(gameId: string): Promise<Suggestion[]> {
  const reponse = await fetch(`${BASE}/${gameId}/hints`);
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  const corps: { suggestions: Suggestion[] } = await reponse.json();
  return corps.suggestions;
}

export interface PieceMenacee {
  square: string;
  piece: string;
  attackers: number;
  defenders: number;
  undefended: boolean;
}

export interface Menaces {
  threatened_pieces: PieceMenacee[];
  critical_squares: string[];
}

export async function obtenirMenaces(gameId: string): Promise<Menaces> {
  const reponse = await fetch(`${BASE}/${gameId}/threats`);
  if (!reponse.ok) {
    throw new Error(await lireErreur(reponse));
  }
  return reponse.json();
}
