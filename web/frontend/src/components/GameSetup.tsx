import { useState } from "react";

import {
  CADENCES_PREDEFINIES,
  cadencePersonnalisee,
} from "../constants/timeControls";
import type { ConfigurationPartie, CouleurHumain } from "../types/gameConfig";

interface PropsConfiguration {
  onDemarrer: (config: ConfigurationPartie) => void;
  chargement: boolean;
}

type ModeImport = "aucun" | "fen" | "pgn";

export function GameSetup({ onDemarrer, chargement }: PropsConfiguration) {
  const [elo, setElo] = useState(1200);
  const [couleur, setCouleur] = useState<CouleurHumain>("white");
  const [cadenceChoisie, setCadenceChoisie] = useState("3+0");
  const [modePersonnalise, setModePersonnalise] = useState(false);
  const [minutesPerso, setMinutesPerso] = useState(5);
  const [incrementPerso, setIncrementPerso] = useState(0);
  const [modeImport, setModeImport] = useState<ModeImport>("aucun");
  const [fenImport, setFenImport] = useState("");
  const [pgnImport, setPgnImport] = useState("");

  const lancerPartie = () => {
    const cadence = modePersonnalise
      ? cadencePersonnalisee(minutesPerso, incrementPerso)
      : (CADENCES_PREDEFINIES.find((c) => c.label === cadenceChoisie) ??
        CADENCES_PREDEFINIES[1]);

    const config: ConfigurationPartie = {
      elo,
      couleurHumain: couleur,
      cadence,
    };

    if (modeImport === "fen" && fenImport.trim()) {
      config.fen = fenImport.trim();
    } else if (modeImport === "pgn" && pgnImport.trim()) {
      config.pgn = pgnImport.trim();
    }

    onDemarrer(config);
  };

  return (
    <section className="configuration">
      <h2>Nouvelle partie</h2>

      <fieldset className="groupe">
        <legend>Couleur</legend>
        <div className="boutons-couleur">
          <button
            type="button"
            className={couleur === "white" ? "actif" : ""}
            onClick={() => setCouleur("white")}
          >
            Blancs
          </button>
          <button
            type="button"
            className={couleur === "black" ? "actif" : ""}
            onClick={() => setCouleur("black")}
          >
            Noirs
          </button>
        </div>
      </fieldset>

      <fieldset className="groupe">
        <legend>Niveau Elo : {elo}</legend>
        <input
          type="range"
          min={1}
          max={2000}
          value={elo}
          onChange={(event) => setElo(Number(event.target.value))}
        />
        <input
          type="number"
          className="entree-elo"
          min={1}
          max={2000}
          value={elo}
          onChange={(event) => {
            const valeur = Number(event.target.value);
            if (!Number.isNaN(valeur)) {
              setElo(Math.min(2000, Math.max(1, valeur)));
            }
          }}
        />
      </fieldset>

      <fieldset className="groupe">
        <legend>Cadence</legend>
        <div className="boutons-cadence">
          {CADENCES_PREDEFINIES.map((cadence) => (
            <button
              key={cadence.label}
              type="button"
              className={
                !modePersonnalise && cadenceChoisie === cadence.label
                  ? "actif"
                  : ""
              }
              onClick={() => {
                setModePersonnalise(false);
                setCadenceChoisie(cadence.label);
              }}
            >
              {cadence.label}
            </button>
          ))}
          <button
            type="button"
            className={modePersonnalise ? "actif" : ""}
            onClick={() => setModePersonnalise(true)}
          >
            Perso
          </button>
        </div>

        {modePersonnalise && (
          <div className="cadence-perso">
            <label>
              Minutes
              <input
                type="number"
                min={1}
                max={120}
                value={minutesPerso}
                onChange={(event) =>
                  setMinutesPerso(Math.max(1, Number(event.target.value)))
                }
              />
            </label>
            <label>
              Incrément (s)
              <input
                type="number"
                min={0}
                max={60}
                value={incrementPerso}
                onChange={(event) =>
                  setIncrementPerso(Math.max(0, Number(event.target.value)))
                }
              />
            </label>
          </div>
        )}
      </fieldset>

      <fieldset className="groupe">
        <legend>Importer une position</legend>
        <div className="boutons-cadence">
          <button
            type="button"
            className={modeImport === "aucun" ? "actif" : ""}
            onClick={() => setModeImport("aucun")}
          >
            Départ
          </button>
          <button
            type="button"
            className={modeImport === "fen" ? "actif" : ""}
            onClick={() => setModeImport("fen")}
          >
            FEN
          </button>
          <button
            type="button"
            className={modeImport === "pgn" ? "actif" : ""}
            onClick={() => setModeImport("pgn")}
          >
            PGN
          </button>
        </div>
        {modeImport === "fen" && (
          <textarea
            className="zone-import"
            placeholder="Coller une FEN…"
            value={fenImport}
            onChange={(event) => setFenImport(event.target.value)}
            rows={2}
          />
        )}
        {modeImport === "pgn" && (
          <textarea
            className="zone-import"
            placeholder="Coller un PGN…"
            value={pgnImport}
            onChange={(event) => setPgnImport(event.target.value)}
            rows={5}
          />
        )}
      </fieldset>

      <button
        type="button"
        className="bouton-principal"
        onClick={lancerPartie}
        disabled={chargement}
      >
        Jouer
      </button>
    </section>
  );
}
