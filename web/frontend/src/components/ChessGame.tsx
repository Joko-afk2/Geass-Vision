import { useCallback, useEffect, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";

import {
  chargerFen,
  creerPartie,
  importerPgn,
  jouerCoup,
  obtenirEtat,
  obtenirMenaces,
  obtenirSuggestions,
  type Menaces,
  type NouvellePartieReponse,
  type Suggestion,
} from "../api/gameApi";
import {
  COULEUR_CASE_CLAIRE,
  COULEUR_CASE_SOMBRE,
  PIECES_PERSONNALISEES,
  STYLE_PLATEAU,
} from "../constants/chessTheme";
import type { ConfigurationPartie } from "../types/gameConfig";
import { useChessClock } from "../hooks/useChessClock";
import { fenDepuisHistorique } from "../utils/moveHistory";
import { fenPourAffichage, fenPourChess } from "../utils/chessFen";
import { EvalBar } from "./EvalBar";
import { GameExport } from "./GameExport";
import { flechesDepuisSuggestions, Suggestions } from "./Suggestions";
import { stylesDepuisMenaces, Threats } from "./Threats";
import { GameReview } from "./GameReview";
import { GameSetup } from "./GameSetup";
import { GameTimer } from "./GameTimer";
import { MoveHistory } from "./MoveHistory";

function estTourHumain(
  fen: string,
  couleurHumain: "white" | "black",
  partieTerminee: boolean,
): boolean {
  if (partieTerminee) {
    return false;
  }
  const echecs = new Chess(fenPourChess(fen));
  const trait = echecs.turn() === "w" ? "white" : "black";
  return trait === couleurHumain;
}

function traitDepuisFen(fen: string): "white" | "black" | null {
  try {
    const echecs = new Chess(fenPourChess(fen));
    return echecs.turn() === "w" ? "white" : "black";
  } catch {
    return null;
  }
}

function resultatTimeout(
  perdant: "white" | "black",
  couleurHumain: "white" | "black",
): string {
  if (perdant === couleurHumain) {
    return perdant === "white" ? "0-1" : "1-0";
  }
  return perdant === "white" ? "1-0" : "0-1";
}

export function ChessGame() {
  const [fen, setFen] = useState<string>("start");
  const [gameId, setGameId] = useState<string | null>(null);
  const [config, setConfig] = useState<ConfigurationPartie | null>(null);
  const [couleurHumain, setCouleurHumain] = useState<"white" | "black">("white");
  const [evaluation, setEvaluation] = useState(0);
  const [partieTerminee, setPartieTerminee] = useState(false);
  const [resultat, setResultat] = useState<string | null>(null);
  const [chargement, setChargement] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [dernierCoupMoteur, setDernierCoupMoteur] = useState<string | null>(null);
  const [enConfiguration, setEnConfiguration] = useState(true);
  const [barreEvalVisible, setBarreEvalVisible] = useState(true);
  const [flechesActives, setFlechesActives] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [menaces, setMenaces] = useState<Menaces | null>(null);
  const [menacesActives, setMenacesActives] = useState(true);
  const [historique, setHistorique] = useState<string[]>([]);
  const [plyVue, setPlyVue] = useState<number | null>(null);

  const enRevue = plyVue !== null;
  const fenPlateau = enRevue
    ? fenDepuisHistorique(historique, plyVue, fen)
    : fenPourAffichage(fen);
  const trait = partieTerminee
    ? null
    : traitDepuisFen(fenPlateau);
  const cadence = config?.cadence ?? {
    label: "3+0",
    baseMinutes: 3,
    incrementSeconds: 0,
  };

  const { tempsBlanc, tempsNoir, reinitialiser, timeout } = useChessClock(
    trait,
    cadence,
    gameId !== null && !partieTerminee,
  );

  const tourHumain =
    !enRevue && estTourHumain(fen, couleurHumain, partieTerminee);

  const synchroniserEtat = useCallback(async (id: string) => {
    const etat = await obtenirEtat(id);
    setHistorique(etat.moves);
    setFen(etat.fen);
    setEvaluation(etat.evaluation);
    setPartieTerminee(etat.is_game_over);
    setResultat(etat.result);
    return etat;
  }, []);

  useEffect(() => {
    if (timeout === null) {
      return;
    }
    setPartieTerminee(true);
    setResultat(resultatTimeout(timeout, couleurHumain));
  }, [timeout, couleurHumain]);

  useEffect(() => {
    if (!gameId || partieTerminee || !tourHumain || chargement || enRevue) {
      setSuggestions([]);
      return;
    }

    let annule = false;
    obtenirSuggestions(gameId)
      .then((liste) => {
        if (!annule) {
          setSuggestions(liste);
        }
      })
      .catch(() => {
        if (!annule) {
          setSuggestions([]);
        }
      });

    return () => {
      annule = true;
    };
  }, [gameId, fen, tourHumain, partieTerminee, chargement, enRevue]);

  useEffect(() => {
    if (!gameId || partieTerminee || chargement || enRevue) {
      if (enRevue) {
        setMenaces(null);
      }
      return;
    }

    let annule = false;
    obtenirMenaces(gameId)
      .then((donnees) => {
        if (!annule) {
          setMenaces(donnees);
        }
      })
      .catch(() => {
        if (!annule) {
          setMenaces(null);
        }
      });

    return () => {
      annule = true;
    };
  }, [gameId, fen, partieTerminee, chargement, enRevue]);

  const fleches = flechesDepuisSuggestions(suggestions, flechesActives);
  const stylesCases = stylesDepuisMenaces(menaces, menacesActives);

  const appliquerEtatPartie = useCallback(
    (donnees: NouvellePartieReponse, configuration: ConfigurationPartie) => {
      setGameId(donnees.game_id);
      setFen(donnees.fen);
      setConfig(configuration);
      setCouleurHumain(donnees.human_color);
      setEvaluation(donnees.evaluation);
      setPartieTerminee(donnees.is_game_over);
      setResultat(donnees.result);
      setDernierCoupMoteur(donnees.engine_move);
      setEnConfiguration(false);
      setErreur(null);
      setPlyVue(null);
      reinitialiser();
    },
    [reinitialiser],
  );

  const demarrerPartie = async (configuration: ConfigurationPartie) => {
    setChargement(true);
    setErreur(null);
    try {
      let donnees: NouvellePartieReponse;
      if (configuration.pgn) {
        donnees = await importerPgn(
          configuration.pgn,
          configuration.elo,
          configuration.couleurHumain,
        );
      } else if (configuration.fen) {
        donnees = await chargerFen(
          configuration.fen,
          configuration.elo,
          configuration.couleurHumain,
        );
      } else {
        donnees = await creerPartie(
          configuration.elo,
          configuration.couleurHumain,
        );
      }
      appliquerEtatPartie(donnees, configuration);
      await synchroniserEtat(donnees.game_id);
    } catch (probleme) {
      setErreur(probleme instanceof Error ? probleme.message : "Erreur inconnue");
    } finally {
      setChargement(false);
    }
  };

  const retourConfiguration = () => {
    setGameId(null);
    setEnConfiguration(true);
    setFen("start");
    setPartieTerminee(false);
    setResultat(null);
    setDernierCoupMoteur(null);
    setErreur(null);
    setSuggestions([]);
    setFlechesActives(false);
    setMenaces(null);
    setHistorique([]);
    setPlyVue(null);
  };

  const envoyerCoup = async (uci: string) => {
    if (!gameId || partieTerminee || enRevue) {
      return;
    }
    setPlyVue(null);
    setChargement(true);
    setErreur(null);
    try {
      const donnees = await jouerCoup(gameId, uci);
      await synchroniserEtat(gameId);
      setDernierCoupMoteur(donnees.engine_move);
    } catch (probleme) {
      setErreur(probleme instanceof Error ? probleme.message : "Erreur inconnue");
      const echecs = new Chess(fenPourChess(fen));
      setFen(echecs.fen());
    } finally {
      setChargement(false);
    }
  };

  const onPieceDrop = (
    sourceSquare: string,
    targetSquare: string,
    piece: string,
  ): boolean => {
    if (!gameId || !tourHumain || chargement || partieTerminee || enRevue) {
      return false;
    }

    const echecs = new Chess(fenPourChess(fen));
    const estPromotion =
      piece[1]?.toLowerCase() === "p" &&
      ((piece[0] === "w" && targetSquare[1] === "8") ||
        (piece[0] === "b" && targetSquare[1] === "1"));

    const coup = echecs.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: estPromotion ? "q" : undefined,
    });

    if (!coup) {
      return false;
    }

    const uci = `${coup.from}${coup.to}${coup.promotion ?? ""}`;
    setFen(echecs.fen());
    void envoyerCoup(uci);
    return true;
  };

  if (enConfiguration) {
    return (
      <section className="partie">
        <GameSetup onDemarrer={demarrerPartie} chargement={chargement} />
        {erreur && <p className="erreur">{erreur}</p>}
      </section>
    );
  }

  return (
    <>
    <section className="partie">
      <div className="colonne-plateau">
        <GameTimer
          tempsBlanc={tempsBlanc}
          tempsNoir={tempsNoir}
          trait={trait}
          couleurHumain={couleurHumain}
          cadenceLabel={cadence.label}
          partieTerminee={partieTerminee}
        />
        <div className="zone-plateau">
          <EvalBar
            evaluation={evaluation}
            visible={barreEvalVisible}
            orientation={couleurHumain}
          />
          <div className="plateau">
            <Chessboard
              position={fenPlateau}
              onPieceDrop={onPieceDrop}
              boardOrientation={couleurHumain}
              arePiecesDraggable={
                tourHumain && !chargement && !partieTerminee && !enRevue
              }
              animationDuration={200}
              customArrows={fleches}
              customSquareStyles={stylesCases}
              customBoardStyle={STYLE_PLATEAU}
              customLightSquareStyle={{ backgroundColor: COULEUR_CASE_CLAIRE }}
              customDarkSquareStyle={{ backgroundColor: COULEUR_CASE_SOMBRE }}
              customPieces={PIECES_PERSONNALISEES}
            />
          </div>
        </div>
      </div>

      <aside className="panneau">
        <h2>Partie</h2>
        <p>
          <strong>Niveau :</strong> {config?.elo ?? 1200} Elo
        </p>
        <p>
          <strong>Vous jouez :</strong>{" "}
          {couleurHumain === "white" ? "Blancs" : "Noirs"}
          {config?.couleurHumain === "random" ? " (tirage aléatoire)" : ""}
        </p>
        <label className="case-option">
          <input
            type="checkbox"
            checked={barreEvalVisible}
            onChange={(event) => setBarreEvalVisible(event.target.checked)}
          />
          Barre d&apos;évaluation
        </label>
        <p>
          <strong>Tour :</strong>{" "}
          {partieTerminee
            ? "partie terminée"
            : tourHumain
              ? "vous"
              : "moteur"}
        </p>
        {dernierCoupMoteur && (
          <p>
            <strong>Dernier coup moteur :</strong> {dernierCoupMoteur}
          </p>
        )}
        {resultat && (
          <p>
            <strong>Résultat :</strong> {resultat}
          </p>
        )}
        <Suggestions
          suggestions={suggestions}
          flechesActives={flechesActives}
          onBasculerFleches={setFlechesActives}
        />
        <Threats
          menaces={menaces}
          actif={menacesActives}
          onBasculer={setMenacesActives}
        />
        <MoveHistory
          coups={historique}
          plyVue={plyVue}
          onChangerPly={setPlyVue}
        />
        {gameId && <GameExport gameId={gameId} />}
        <button type="button" onClick={retourConfiguration} disabled={chargement}>
          Nouvelle partie
        </button>
        {chargement && <p className="statut">Réflexion du moteur…</p>}
        {erreur && <p className="erreur">{erreur}</p>}
      </aside>
    </section>
    {partieTerminee && gameId && (
      <GameReview gameId={gameId} couleurHumain={couleurHumain} />
    )}
    </>
  );
}
