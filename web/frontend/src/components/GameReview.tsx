import { useEffect, useState } from "react";

import {
  analyserPartie,
  LIBELLES_CATEGORIE,
  type AnalyseCoup,
  type RapportAnalyse,
} from "../api/analysisApi";
import type { CouleurHumain } from "../types/gameConfig";

interface PropsRevue {
  gameId: string;
  couleurHumain: CouleurHumain;
}

const LARGEUR_GRAPHIQUE = 400;
const HAUTEUR_GRAPHIQUE = 140;
const EVAL_MAX = 800;

function evalVersY(evalCp: number): number {
  const borne = Math.max(-EVAL_MAX, Math.min(EVAL_MAX, evalCp));
  const ratio = (borne + EVAL_MAX) / (2 * EVAL_MAX);
  return HAUTEUR_GRAPHIQUE - ratio * HAUTEUR_GRAPHIQUE;
}

function GraphiqueEval({ coups }: { coups: AnalyseCoup[] }) {
  if (coups.length === 0) {
    return <p className="revue-vide">Pas de données d&apos;évaluation.</p>;
  }

  const pasX = LARGEUR_GRAPHIQUE / Math.max(coups.length, 1);
  const points = coups
    .map((coup, index) => {
      const x = pasX * (index + 0.5);
      const y = evalVersY(coup.eval_apres);
      return `${x},${y}`;
    })
    .join(" ");

  const ligneZero = evalVersY(0);

  return (
    <div className="graphique-eval">
      <svg
        viewBox={`0 0 ${LARGEUR_GRAPHIQUE} ${HAUTEUR_GRAPHIQUE}`}
        role="img"
        aria-label="Graphique d'évaluation par coup"
      >
        <line
          x1={0}
          y1={ligneZero}
          x2={LARGEUR_GRAPHIQUE}
          y2={ligneZero}
          className="axe-zero"
        />
        <polyline points={points} className="courbe-eval" />
        {coups.map((coup, index) => (
          <circle
            key={coup.numero}
            cx={pasX * (index + 0.5)}
            cy={evalVersY(coup.eval_apres)}
            r={3}
            className={`point-eval cat-${coup.categorie}`}
          />
        ))}
      </svg>
      <div className="legendes-eval">
        <span>−8</span>
        <span>0</span>
        <span>+8</span>
      </div>
    </div>
  );
}

function precisionHumain(
  rapport: RapportAnalyse,
  couleurHumain: CouleurHumain,
): number {
  return couleurHumain === "white"
    ? rapport.precision_blancs
    : rapport.precision_noirs;
}

function precisionMoteur(
  rapport: RapportAnalyse,
  couleurHumain: CouleurHumain,
): number {
  return couleurHumain === "white"
    ? rapport.precision_noirs
    : rapport.precision_blancs;
}

export function GameReview({ gameId, couleurHumain }: PropsRevue) {
  const [rapport, setRapport] = useState<RapportAnalyse | null>(null);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    let annule = false;
    setChargement(true);
    setErreur(null);

    analyserPartie(gameId, 2)
      .then((donnees) => {
        if (!annule) {
          setRapport(donnees);
        }
      })
      .catch((probleme) => {
        if (!annule) {
          setErreur(
            probleme instanceof Error ? probleme.message : "Erreur d'analyse",
          );
        }
      })
      .finally(() => {
        if (!annule) {
          setChargement(false);
        }
      });

    return () => {
      annule = true;
    };
  }, [gameId]);

  if (chargement) {
    return (
      <section className="revue-partie">
        <h2>Analyse de la partie</h2>
        <p className="statut">Analyse en cours…</p>
      </section>
    );
  }

  if (erreur || !rapport) {
    return (
      <section className="revue-partie">
        <h2>Analyse de la partie</h2>
        <p className="erreur">{erreur ?? "Analyse indisponible."}</p>
      </section>
    );
  }

  return (
    <section className="revue-partie">
      <h2>Analyse de la partie</h2>
      <p className="revue-meta">
        {rapport.blancs} vs {rapport.noirs} — {rapport.resultat}
      </p>

      <div className="precision-bloc">
        <div className="precision-cartouche">
          <span className="precision-label">Votre précision</span>
          <span className="precision-valeur">
            {precisionHumain(rapport, couleurHumain)} %
          </span>
        </div>
        <div className="precision-cartouche moteur">
          <span className="precision-label">Moteur</span>
          <span className="precision-valeur">
            {precisionMoteur(rapport, couleurHumain)} %
          </span>
        </div>
      </div>

      <GraphiqueEval coups={rapport.coups} />

      <table className="tableau-coups">
        <thead>
          <tr>
            <th>#</th>
            <th>Coup</th>
            <th>Éval.</th>
            <th>Perte</th>
            <th>Classe</th>
          </tr>
        </thead>
        <tbody>
          {rapport.coups.map((coup) => (
            <tr key={coup.numero} className={`ligne-${coup.categorie}`}>
              <td>{coup.numero}</td>
              <td>{coup.coup}</td>
              <td>{(coup.eval_apres / 100).toFixed(1)}</td>
              <td>{coup.perte_cp}</td>
              <td>
                <span className={`badge-cat cat-${coup.categorie}`}>
                  {LIBELLES_CATEGORIE[coup.categorie] ?? coup.categorie}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
