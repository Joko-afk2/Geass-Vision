"""Routes d'analyse post-partie — W07."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from web.backend.services.analysis_service import (
    analyser_partie_web,
    analyser_pgn_texte,
)
from web.backend.services.engine_service import ServiceMoteur, service_moteur

router = APIRouter(prefix="/api", tags=["analyze"])


def obtenir_service() -> ServiceMoteur:
    return service_moteur


class AnalyseCoupReponse(BaseModel):
    numero: int
    coup: str
    couleur: str
    eval_avant: int
    eval_apres: int
    meilleur_coup: str | None
    perte_cp: int
    categorie: str


class RapportAnalyseReponse(BaseModel):
    event: str
    blancs: str
    noirs: str
    resultat: str
    coups: list[AnalyseCoupReponse]
    precision_blancs: float
    precision_noirs: float


class AnalysePgnRequete(BaseModel):
    pgn: str
    profondeur: int = Field(default=2, ge=1, le=4)


def _vers_reponse(rapport) -> RapportAnalyseReponse:
    return RapportAnalyseReponse(
        event=rapport.event,
        blancs=rapport.blancs,
        noirs=rapport.noirs,
        resultat=rapport.resultat,
        coups=[
            AnalyseCoupReponse(
                numero=c.numero,
                coup=c.coup,
                couleur=c.couleur,
                eval_avant=c.eval_avant,
                eval_apres=c.eval_apres,
                meilleur_coup=c.meilleur_coup,
                perte_cp=c.perte_cp,
                categorie=c.categorie,
            )
            for c in rapport.coups
        ],
        precision_blancs=rapport.precision_blancs,
        precision_noirs=rapport.precision_noirs,
    )


@router.post("/analyze", response_model=RapportAnalyseReponse)
def analyser_pgn_route(requete: AnalysePgnRequete) -> RapportAnalyseReponse:
    try:
        rapport = analyser_pgn_texte(requete.pgn, requete.profondeur)
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur)) from erreur
    return _vers_reponse(rapport)


@router.get("/game/{game_id}/analyze", response_model=RapportAnalyseReponse)
def analyser_partie_route(
    game_id: str,
    profondeur: int = 2,
    service: ServiceMoteur = Depends(obtenir_service),
) -> RapportAnalyseReponse:
    if profondeur < 1 or profondeur > 4:
        raise HTTPException(status_code=400, detail="Profondeur entre 1 et 4.")

    try:
        partie = service._obtenir_partie(game_id)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur

    if not partie.historique_uci:
        raise HTTPException(status_code=400, detail="Aucun coup à analyser.")

    rapport = analyser_partie_web(partie, profondeur)
    return _vers_reponse(rapport)
