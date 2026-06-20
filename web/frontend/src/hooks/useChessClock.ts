import { useCallback, useEffect, useRef, useState } from "react";

import type { Cadence } from "../types/gameConfig";
import { baseEnMillisecondes } from "../constants/timeControls";

export type Trait = "white" | "black";

export function formaterTemps(millisecondes: number): string {
  const totalSecondes = Math.max(0, Math.ceil(millisecondes / 1000));
  const minutes = Math.floor(totalSecondes / 60);
  const secondes = totalSecondes % 60;
  return `${minutes}:${secondes.toString().padStart(2, "0")}`;
}

export function useChessClock(
  trait: Trait | null,
  cadence: Cadence,
  actif: boolean,
) {
  const baseMs = baseEnMillisecondes(cadence);
  const incrementMs = cadence.incrementSeconds * 1000;

  const [tempsBlanc, setTempsBlanc] = useState(baseMs);
  const [tempsNoir, setTempsNoir] = useState(baseMs);
  const traitPrecedent = useRef<Trait | null>(null);

  const reinitialiser = useCallback(() => {
    setTempsBlanc(baseMs);
    setTempsNoir(baseMs);
    traitPrecedent.current = null;
  }, [baseMs]);

  useEffect(() => {
    reinitialiser();
  }, [cadence.label, cadence.baseMinutes, cadence.incrementSeconds, reinitialiser]);

  useEffect(() => {
    if (!actif || trait === null) {
      return;
    }

    if (traitPrecedent.current !== null && trait !== traitPrecedent.current) {
      if (traitPrecedent.current === "white") {
        setTempsBlanc((valeur) => valeur + incrementMs);
      } else {
        setTempsNoir((valeur) => valeur + incrementMs);
      }
    }
    traitPrecedent.current = trait;
  }, [trait, actif, incrementMs]);

  useEffect(() => {
    if (!actif || trait === null) {
      return;
    }

    const intervalle = window.setInterval(() => {
      if (trait === "white") {
        setTempsBlanc((valeur) => Math.max(0, valeur - 100));
      } else {
        setTempsNoir((valeur) => Math.max(0, valeur - 100));
      }
    }, 100);

    return () => window.clearInterval(intervalle);
  }, [trait, actif]);

  const timeout = (() => {
    if (!actif || trait === null) {
      return null;
    }
    if (trait === "white" && tempsBlanc <= 0) {
      return "white" as const;
    }
    if (trait === "black" && tempsNoir <= 0) {
      return "black" as const;
    }
    return null;
  })();

  return {
    tempsBlanc,
    tempsNoir,
    reinitialiser,
    timeout,
    formaterTemps,
  };
}
