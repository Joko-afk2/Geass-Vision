import type { CSSProperties } from "react";

import type { Menaces, PieceMenacee } from "../api/gameApi";

interface PropsMenaces {
  menaces: Menaces | null;
  actif: boolean;
  onBasculer: (actif: boolean) => void;
}

export function stylesDepuisMenaces(
  menaces: Menaces | null,
  actif: boolean,
): Record<string, CSSProperties> {
  if (!actif || menaces === null) {
    return {};
  }

  const styles: Record<string, CSSProperties> = {};

  for (const piece of menaces.threatened_pieces) {
    styles[piece.square] = {
      background: piece.undefended
        ? "radial-gradient(circle, rgba(255, 70, 70, 0.55) 36%, transparent 72%)"
        : "radial-gradient(circle, rgba(255, 150, 60, 0.48) 36%, transparent 72%)",
    };
  }

  for (const caseSquare of menaces.critical_squares) {
    if (styles[caseSquare]) {
      continue;
    }
    styles[caseSquare] = {
      backgroundColor: "rgba(255, 210, 60, 0.38)",
    };
  }

  return styles;
}

function libellePiece(symbole: string): string {
  const table: Record<string, string> = {
    p: "pion",
    r: "tour",
    n: "cavalier",
    b: "fou",
    q: "dame",
    k: "roi",
    P: "pion",
    R: "tour",
    N: "cavalier",
    B: "fou",
    Q: "dame",
    K: "roi",
  };
  return table[symbole] ?? "pièce";
}

function decrirePiece(piece: PieceMenacee): string {
  const nom = libellePiece(piece.piece);
  if (piece.undefended) {
    return `${nom} en ${piece.square} (non défendu)`;
  }
  return `${nom} en ${piece.square} (${piece.attackers} att. / ${piece.defenders} déf.)`;
}

export function Threats({ menaces, actif, onBasculer }: PropsMenaces) {
  return (
    <section className="menaces">
      <div className="menaces-entete">
        <h3>Menaces</h3>
        <label className="case-option">
          <input
            type="checkbox"
            checked={actif}
            onChange={(event) => onBasculer(event.target.checked)}
          />
          Surligner sur l&apos;échiquier
        </label>
      </div>

      {!menaces || menaces.threatened_pieces.length === 0 ? (
        <p className="menaces-vide">Aucune pièce sous menace directe.</p>
      ) : (
        <ul className="liste-menaces">
          {menaces.threatened_pieces.map((piece) => (
            <li
              key={piece.square}
              className={piece.undefended ? "non-defendu" : "defendu"}
            >
              {decrirePiece(piece)}
            </li>
          ))}
        </ul>
      )}

      {menaces && menaces.critical_squares.length > 0 && (
        <p className="cases-critiques">
          <strong>Cases critiques :</strong>{" "}
          {menaces.critical_squares.join(", ")}
        </p>
      )}
    </section>
  );
}
