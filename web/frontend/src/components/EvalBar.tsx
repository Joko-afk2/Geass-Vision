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

  const pourcentage = evaluationVersPourcentage(evaluation);
  const texte =
    evaluation > 0 ? `+${(evaluation / 100).toFixed(1)}` : (evaluation / 100).toFixed(1);

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
