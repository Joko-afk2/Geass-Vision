import { useCallback, useEffect, useState } from "react";
import type { CSSProperties } from "react";
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
import { AvantageMateriel } from "./AvantageMateriel";
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
  const [barreEvalVisible, setBarreEvalVisible] = useState(false);
  const [flechesActives, setFlechesActives] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [menaces, setMenaces] = useState<Menaces | null>(null);
  const [menacesActives, setMenacesActives] = useState(false);
  const [sansAide, setSansAide] = useState(false);
  const [historique, setHistorique] = useState<string[]>([]);
  const [plyVue, setPlyVue] = useState<number | null>(null);
  const [caseSelectionnee, setCaseSelectionnee] = useState<string | null>(null);
  const [fenDepart, setFenDepart] = useState<string | undefined>(undefined);
  const [verrouille, setVerrouille] = useState(false);

  const enRevue = plyVue !== null;
  const fenPlateau = enRevue
    ? fenDepuisHistorique(historique, plyVue, fenDepart)
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
    gameId !== null && !partieTerminee && historique.length > 0 && !enRevue,
  );

  const tourHumain =
    !enRevue && estTourHumain(fen, couleurHumain, partieTerminee);

  const synchroniserEtat = useCallback(async (id: string) => {
    const etat = await obtenirEtat(id);
    setHistorique(etat.moves);
    setFen(etat.fen);
    setEvaluation(etat.evaluation);
    setPartieTerminee(etat.is_game_over);
    setResultat(etat.result_reason ?? etat.result);
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
    document.body.style.overflow = verrouille ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [verrouille]);

  useEffect(() => {
    if (
      sansAide ||
      !gameId ||
      partieTerminee ||
      !tourHumain ||
      chargement ||
      enRevue
    ) {
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
  }, [gameId, fen, tourHumain, partieTerminee, chargement, enRevue, sansAide]);

  useEffect(() => {
    if (sansAide || !gameId || partieTerminee || chargement || enRevue) {
      if (enRevue || sansAide) {
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
  }, [gameId, fen, partieTerminee, chargement, enRevue, sansAide]);

  const fleches = flechesDepuisSuggestions(suggestions, flechesActives);
  const stylesCases: Record<string, CSSProperties> = {
    ...stylesDepuisMenaces(menaces, menacesActives),
  };
  if (caseSelectionnee && tourHumain && !enRevue) {
    stylesCases[caseSelectionnee] = {
      ...stylesCases[caseSelectionnee],
      background: "rgba(225, 16, 46, 0.45)",
    };
    try {
      const echecsSel = new Chess(fenPourChess(fen));
      for (const coup of echecsSel.moves({
        square: caseSelectionnee as never,
        verbose: true,
      }) as Array<{ to: string }>) {
        stylesCases[coup.to] = {
          ...stylesCases[coup.to],
          background:
            "radial-gradient(circle, rgba(225, 16, 46, 0.55) 24%, transparent 28%)",
        };
      }
    } catch {
      // case sans coup légal : pas de surbrillance
    }
  }

  const appliquerEtatPartie = useCallback(
    (donnees: NouvellePartieReponse, configuration: ConfigurationPartie) => {
      setGameId(donnees.game_id);
      setFen(donnees.fen);
      setFenDepart(configuration.fen);
      setConfig(configuration);
      setSansAide(configuration.sansAide);
      setBarreEvalVisible(false);
      setFlechesActives(false);
      setMenacesActives(false);
      setCouleurHumain(donnees.human_color);
      setEvaluation(donnees.evaluation);
      setPartieTerminee(donnees.is_game_over);
      setResultat(donnees.result_reason ?? donnees.result);
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
    setCaseSelectionnee(null);
    setFenDepart(undefined);
    setVerrouille(false);
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

  const tenterCoup = (depart: string, arrivee: string): boolean => {
    if (!gameId || !tourHumain || chargement || partieTerminee || enRevue) {
      return false;
    }

    const echecs = new Chess(fenPourChess(fen));
    const piece = echecs.get(depart as never);
    const estPromotion =
      piece?.type === "p" &&
      ((piece.color === "w" && arrivee[1] === "8") ||
        (piece.color === "b" && arrivee[1] === "1"));

    let coup: ReturnType<Chess["move"]> | null = null;
    try {
      coup = echecs.move({
        from: depart,
        to: arrivee,
        promotion: estPromotion ? "q" : undefined,
      });
    } catch {
      coup = null;
    }

    if (!coup) {
      return false;
    }

    const uci = `${coup.from}${coup.to}${coup.promotion ?? ""}`;
    setFen(echecs.fen());
    setCaseSelectionnee(null);
    void envoyerCoup(uci);
    return true;
  };

  const onPieceDrop = (sourceSquare: string, targetSquare: string): boolean => {
    setCaseSelectionnee(null);
    return tenterCoup(sourceSquare, targetSquare);
  };

  const onSquareClick = (square: string) => {
    if (!gameId || !tourHumain || chargement || partieTerminee || enRevue) {
      return;
    }

    const echecs = new Chess(fenPourChess(fen));
    const traitCourant = echecs.turn();

    if (caseSelectionnee) {
      if (square === caseSelectionnee) {
        setCaseSelectionnee(null);
        return;
      }
      if (tenterCoup(caseSelectionnee, square)) {
        return;
      }
      const cible = echecs.get(square as never);
      if (cible && cible.color === traitCourant) {
        setCaseSelectionnee(square);
      } else {
        setCaseSelectionnee(null);
      }
      return;
    }

    const piece = echecs.get(square as never);
    if (piece && piece.color === traitCourant) {
      setCaseSelectionnee(square);
    }
  };

  const plyAffiche = plyVue ?? historique.length;
  const reculerCoup = () => {
    setCaseSelectionnee(null);
    setPlyVue(Math.max(0, plyAffiche - 1));
  };
  const avancerCoup = () => {
    const suivant = plyAffiche + 1;
    setPlyVue(suivant >= historique.length ? null : suivant);
  };

  if (enConfiguration) {
    return (
      <section className="vue-configuration">
        <GameSetup onDemarrer={demarrerPartie} chargement={chargement} />
        {erreur && <p className="erreur">{erreur}</p>}
      </section>
    );
  }

  return (
    <>
    <section className="partie">
      <div className="colonne-plateau">
        <div className="barre-controles">
          <button
            type="button"
            className="bouton-menu"
            onClick={retourConfiguration}
          >
            ← Menu principal
          </button>
          {!partieTerminee && historique.length > 0 && (
            <div className="nav-rapide">
              <button
                type="button"
                onClick={reculerCoup}
                disabled={plyAffiche <= 0}
                title="Voir la position précédente"
              >
                ◀
              </button>
              <span className="nav-rapide-pos">
                {enRevue ? `Coup ${plyAffiche}/${historique.length}` : "Actuel"}
              </span>
              <button
                type="button"
                onClick={avancerCoup}
                disabled={!enRevue}
                title="Revenir à la position actuelle"
              >
                ▶
              </button>
            </div>
          )}
          <button
            type="button"
            className={`bouton-verrou ${verrouille ? "actif" : ""}`}
            onClick={() => setVerrouille((v) => !v)}
            title="Bloquer le défilement de la page"
          >
            {verrouille ? "Débloquer" : "Bloquer"}
          </button>
        </div>
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
            visible={!sansAide && barreEvalVisible}
            orientation={couleurHumain}
          />
          <div className="plateau">
            <Chessboard
              position={fenPlateau}
              onPieceDrop={onPieceDrop}
              onSquareClick={onSquareClick}
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
        {sansAide ? (
          <p className="mode-sans-aide">Mode sans aide</p>
        ) : (
          <label className="case-option">
            <input
              type="checkbox"
              checked={barreEvalVisible}
              onChange={(event) => setBarreEvalVisible(event.target.checked)}
            />
            Barre d&apos;évaluation
          </label>
        )}
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
        <AvantageMateriel fen={fenPlateau} couleurHumain={couleurHumain} />
        {resultat && (
          <p>
            <strong>Résultat :</strong> {resultat}
          </p>
        )}
        {!sansAide && (
          <>
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
          </>
        )}
        <MoveHistory
          coups={historique}
          plyVue={plyVue}
          onChangerPly={setPlyVue}
          navigationVisible={partieTerminee}
        />
        {gameId && partieTerminee && <GameExport gameId={gameId} />}
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
