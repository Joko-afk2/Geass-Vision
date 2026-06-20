import type { Suggestion } from "../api/gameApi";
import { scoreVersTexte } from "../utils/chessDisplay";
import type { Arrow, Square } from "react-chessboard/dist/chessboard/types";

interface PropsSuggestions {
  suggestions: Suggestion[];
  flechesActives: boolean;
  onBasculerFleches: (actif: boolean) => void;
}

const COULEURS_FLECHES = [
  "rgba(61, 126, 255, 0.85)",
  "rgba(52, 199, 89, 0.75)",
  "rgba(255, 159, 10, 0.65)",
];

export function flechesDepuisSuggestions(
  suggestions: Suggestion[],
  actives: boolean,
): Arrow[] {
  if (!actives) {
    return [];
  }
  return suggestions.slice(0, 3).map((suggestion, index) => {
    const depart = suggestion.uci.slice(0, 2) as Square;
    const arrivee = suggestion.uci.slice(2, 4) as Square;
    return [depart, arrivee, COULEURS_FLECHES[index] ?? COULEURS_FLECHES[0]];
  });
}

export function Suggestions({
  suggestions,
  flechesActives,
  onBasculerFleches,
}: PropsSuggestions) {
  return (
    <section className="suggestions">
      <div className="suggestions-entete">
        <h3>Suggestions</h3>
        <label className="case-option">
          <input
            type="checkbox"
            checked={flechesActives}
            onChange={(event) => onBasculerFleches(event.target.checked)}
            disabled={suggestions.length === 0}
          />
          Flèches sur l&apos;échiquier
        </label>
      </div>

      {suggestions.length === 0 ? (
        <p className="suggestions-vide">Aucune suggestion pour le moment.</p>
      ) : (
        <ol className="liste-suggestions">
          {suggestions.map((suggestion, index) => (
            <li key={suggestion.uci}>
              <span className="rang-suggestion">{index + 1}.</span>
              <span className="san-suggestion">{suggestion.san}</span>
              <span className="score-suggestion">
                {scoreVersTexte(suggestion.score)}
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
