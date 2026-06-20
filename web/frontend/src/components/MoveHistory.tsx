interface PropsHistorique {
  coups: string[];
  plyVue: number | null;
  onChangerPly: (ply: number | null) => void;
  /** Affiche les boutons de navigation (réservés à la revue après partie). */
  navigationVisible?: boolean;
}

export function MoveHistory({
  coups,
  plyVue,
  onChangerPly,
  navigationVisible = true,
}: PropsHistorique) {
  if (coups.length === 0) {
    return null;
  }

  const plyCourant = plyVue ?? coups.length;
  const enDirect = plyVue === null;

  return (
    <section className="historique">
      <h3>Historique</h3>
      {navigationVisible && (
      <div className="historique-nav">
        <button type="button" onClick={() => onChangerPly(0)} title="Début">
          |◀
        </button>
        <button
          type="button"
          onClick={() => onChangerPly(Math.max(0, plyCourant - 1))}
          title="Précédent"
        >
          ◀
        </button>
        <button
          type="button"
          onClick={() => {
            if (plyCourant >= coups.length) {
              return;
            }
            onChangerPly(plyCourant + 1 >= coups.length ? null : plyCourant + 1);
          }}
          title="Suivant"
        >
          ▶
        </button>
        <button type="button" onClick={() => onChangerPly(null)} title="Direct">
          ▶|
        </button>
        <span className="historique-position">
          {enDirect
            ? `Direct (${coups.length} coups)`
            : `Coup ${plyCourant} / ${coups.length}`}
        </span>
      </div>
      )}
      <ol className="liste-historique">
        {coups.map((uci, index) => {
          const ply = index + 1;
          const actif = enDirect
            ? ply === coups.length
            : plyCourant === ply;
          return (
            <li key={`${index}-${uci}`}>
              {navigationVisible ? (
                <button
                  type="button"
                  className={actif ? "actif" : ""}
                  onClick={() =>
                    onChangerPly(ply >= coups.length ? null : ply)
                  }
                >
                  {ply}. {uci}
                </button>
              ) : (
                <span className="coup-fige">
                  {ply}. {uci}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
