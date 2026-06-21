import {
  calculerBilanMateriel,
  type PrisePiece,
} from "../utils/materielCapture";

interface Props {
  fen: string;
  couleurHumain: "white" | "black";
}

function iconesPrises(prises: PrisePiece[]) {
  return prises.flatMap((prise) =>
    Array.from({ length: prise.nombre }, (_, i) => (
      <img
        key={`${prise.code}-${i}`}
        className="prise-icone"
        src={`/pieces/${prise.code}.svg`}
        alt={prise.code}
        draggable={false}
      />
    )),
  );
}

function LignePrise({
  label,
  prises,
  avantage,
}: {
  label: string;
  prises: PrisePiece[];
  avantage: number;
}) {
  return (
    <div className="prise-ligne">
      <span className="prise-label">{label}</span>
      <span className="prise-icones">{iconesPrises(prises)}</span>
      {avantage > 0 && <span className="prise-avantage">+{avantage}</span>}
    </div>
  );
}

export function AvantageMateriel({ fen, couleurHumain }: Props) {
  const bilan = calculerBilanMateriel(fen);
  const humainBlanc = couleurHumain === "white";

  const prisesHumain = humainBlanc ? bilan.prisesBlanc : bilan.prisesNoir;
  const prisesMoteur = humainBlanc ? bilan.prisesNoir : bilan.prisesBlanc;
  const avantageHumain = humainBlanc ? bilan.diff : -bilan.diff;

  const aucunePrise =
    prisesHumain.length === 0 && prisesMoteur.length === 0;

  return (
    <div className="avantage-materiel">
      <strong>Matériel :</strong>
      {aucunePrise && avantageHumain === 0 ? (
        <span className="materiel-egal">égal</span>
      ) : (
        <>
          <LignePrise
            label="Vous"
            prises={prisesHumain}
            avantage={avantageHumain > 0 ? avantageHumain : 0}
          />
          <LignePrise
            label="Moteur"
            prises={prisesMoteur}
            avantage={avantageHumain < 0 ? -avantageHumain : 0}
          />
        </>
      )}
    </div>
  );
}
