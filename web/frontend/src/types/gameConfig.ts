export type CouleurHumain = "white" | "black";

export interface Cadence {
  label: string;
  baseMinutes: number;
  incrementSeconds: number;
}

export interface ConfigurationPartie {
  elo: number;
  couleurHumain: CouleurHumain;
  cadence: Cadence;
  fen?: string;
  pgn?: string;
}
