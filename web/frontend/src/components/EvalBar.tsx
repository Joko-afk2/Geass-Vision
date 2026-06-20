import { evaluationVersPourcentage } from "../utils/chessDisplay";

interface PropsBarreEval {
  evaluation: number;
  visible: boolean;
  orientation: "white" | "black";
}

export function EvalBar({ evaluation, visible, orientation }: PropsBarreEval) {
  if (!visible) {
    return null;
  }

  // Remplissage = part des Blancs (orienté via CSS selon le camp du joueur).
  const pourcentage = evaluationVersPourcentage(evaluation);
  // Chiffre affiché du point de vue du joueur (positif = avantage pour lui).
  const valeurJoueur = orientation === "white" ? evaluation : -evaluation;
  const texte =
    valeurJoueur > 0
      ? `+${(valeurJoueur / 100).toFixed(1)}`
      : (valeurJoueur / 100).toFixed(1);

  return (
    <div
      className={`barre-eval orientation-${orientation}`}
      aria-label={`Évaluation : ${texte}`}
    >
      <div className="barre-eval-piste">
        <div
          className="barre-eval-remplissage"
          style={{ height: `${pourcentage}%` }}
        />
      </div>
      <span className="barre-eval-texte">{texte}</span>
    </div>
  );
}
