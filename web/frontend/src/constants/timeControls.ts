import type { Cadence } from "../types/gameConfig";

export const CADENCES_PREDEFINIES: Cadence[] = [
  { label: "1+0", baseMinutes: 1, incrementSeconds: 0 },
  { label: "3+0", baseMinutes: 3, incrementSeconds: 0 },
  { label: "3+2", baseMinutes: 3, incrementSeconds: 2 },
  { label: "5+0", baseMinutes: 5, incrementSeconds: 0 },
  { label: "10+0", baseMinutes: 10, incrementSeconds: 0 },
  { label: "15+10", baseMinutes: 15, incrementSeconds: 10 },
];

export function cadencePersonnalisee(
  baseMinutes: number,
  incrementSeconds: number,
): Cadence {
  return {
    label: `${baseMinutes}+${incrementSeconds}`,
    baseMinutes,
    incrementSeconds,
  };
}

export function baseEnMillisecondes(cadence: Cadence): number {
  return cadence.baseMinutes * 60 * 1000;
}
