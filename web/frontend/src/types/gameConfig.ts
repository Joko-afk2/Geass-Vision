export type CouleurHumain = "white" | "black";

/** Choix à l'écran de configuration (inclut le tirage aléatoire). */
export type ChoixCouleur = CouleurHumain | "random";

export interface Cadence {
  label: string;
  baseMinutes: number;
  incrementSeconds: number;
}

export interface ConfigurationPartie {
  elo: number;
  couleurHumain: ChoixCouleur;
  cadence: Cadence;
  fen?: string;
  pgn?: string;
}
