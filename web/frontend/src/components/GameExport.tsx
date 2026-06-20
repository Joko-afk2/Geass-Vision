import { useState } from "react";

import { exporterFen, exporterPgn } from "../api/gameApi";

interface PropsExport {
  gameId: string;
}

export function GameExport({ gameId }: PropsExport) {
  const [message, setMessage] = useState<string | null>(null);

  const copier = async (texte: string, libelle: string) => {
    try {
      await navigator.clipboard.writeText(texte);
      setMessage(`${libelle} copié.`);
      setTimeout(() => setMessage(null), 2000);
    } catch {
      setMessage(`Impossible de copier le ${libelle}.`);
    }
  };

  const copierFen = async () => {
    const { fen } = await exporterFen(gameId);
    await copier(fen, "FEN");
  };

  const copierPgn = async () => {
    const { pgn } = await exporterPgn(gameId);
    await copier(pgn, "PGN");
  };

  return (
    <section className="export-partie">
      <h3>Export</h3>
      <div className="boutons-export">
        <button type="button" onClick={() => void copierFen()}>
          Copier FEN
        </button>
        <button type="button" onClick={() => void copierPgn()}>
          Copier PGN
        </button>
      </div>
      {message && <p className="export-message">{message}</p>}
    </section>
  );
}
