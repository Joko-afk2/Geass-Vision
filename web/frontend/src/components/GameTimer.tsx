import { formaterTemps } from "../hooks/useChessClock";
import type { CouleurHumain } from "../types/gameConfig";

interface PropsHorloge {
  tempsBlanc: number;
  tempsNoir: number;
  trait: "white" | "black" | null;
  couleurHumain: CouleurHumain;
  cadenceLabel: string;
  partieTerminee: boolean;
}

export function GameTimer({
  tempsBlanc,
  tempsNoir,
  trait,
  couleurHumain,
  cadenceLabel,
  partieTerminee,
}: PropsHorloge) {
  const afficherNoirEnHaut = couleurHumain === "white";

  const horlogeNoir = (
    <div
      className={`horloge ${trait === "black" && !partieTerminee ? "active" : ""}`}
    >
      <span className="horloge-label">Noirs</span>
      <span className="horloge-temps">{formaterTemps(tempsNoir)}</span>
    </div>
  );

  const horlogeBlanc = (
    <div
      className={`horloge ${trait === "white" && !partieTerminee ? "active" : ""}`}
    >
      <span className="horloge-label">Blancs</span>
      <span className="horloge-temps">{formaterTemps(tempsBlanc)}</span>
    </div>
  );

  return (
    <div className="horloges">
      <p className="cadence-active">Cadence : {cadenceLabel}</p>
      {afficherNoirEnHaut ? (
        <>
          {horlogeNoir}
          {horlogeBlanc}
        </>
      ) : (
        <>
          {horlogeBlanc}
          {horlogeNoir}
        </>
      )}
    </div>
  );
}
