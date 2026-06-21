export type TypePromotion = "q" | "r" | "b" | "n";

interface Props {
  couleur: "w" | "b";
  onChoisir: (type: TypePromotion) => void;
  onAnnuler: () => void;
}

const CHOIX: { type: TypePromotion; libelle: string }[] = [
  { type: "q", libelle: "Dame" },
  { type: "r", libelle: "Tour" },
  { type: "b", libelle: "Fou" },
  { type: "n", libelle: "Cavalier" },
];

export function PromotionDialog({ couleur, onChoisir, onAnnuler }: Props) {
  return (
    <div
      className="promotion-overlay"
      role="dialog"
      aria-label="Choix de la promotion"
      onClick={onAnnuler}
    >
      <div className="promotion-carte" onClick={(e) => e.stopPropagation()}>
        <span className="promotion-titre">Promotion</span>
        <div className="promotion-choix">
          {CHOIX.map(({ type, libelle }) => (
            <button
              key={type}
              type="button"
              className="promotion-bouton"
              title={libelle}
              aria-label={libelle}
              onClick={() => onChoisir(type)}
            >
              <img
                src={`/pieces/${couleur}${type.toUpperCase()}.svg`}
                alt={libelle}
                draggable={false}
              />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
