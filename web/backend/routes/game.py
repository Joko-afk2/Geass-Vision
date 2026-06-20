"""Routes API partie — W02."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from web.backend.services.engine_service import ServiceMoteur, service_moteur

router = APIRouter(prefix="/api/game", tags=["game"])


def obtenir_service() -> ServiceMoteur:
    return service_moteur


class NouvellePartieRequete(BaseModel):
    elo: int = Field(default=1200, ge=1, le=2000)
    human_color: Literal["white", "black", "random"] = "white"
    fen: str | None = None


class NouvellePartieReponse(BaseModel):
    game_id: str
    fen: str
    turn: str
    evaluation: int
    elo: int
    human_color: str
    engine_move: str | None = None
    is_game_over: bool
    result: str | None = None
    is_human_turn: bool


class CoupRequete(BaseModel):
    uci: str


class CoupReponse(BaseModel):
    fen: str
    turn: str
    evaluation: int
    human_move: str
    engine_move: str | None = None
    is_game_over: bool
    result: str | None = None


class EtatReponse(BaseModel):
    game_id: str
    fen: str
    turn: str
    evaluation: int
    elo: int
    human_color: str
    moves: list[str]
    is_game_over: bool
    result: str | None = None
    is_human_turn: bool


class SuggestionReponse(BaseModel):
    uci: str
    san: str
    score: int


class HintsReponse(BaseModel):
    suggestions: list[SuggestionReponse]


class PieceMenaceeReponse(BaseModel):
    square: str
    piece: str
    attackers: int
    defenders: int
    undefended: bool


class MenacesReponse(BaseModel):
    threatened_pieces: list[PieceMenaceeReponse]
    critical_squares: list[str]


class ChargerFenRequete(BaseModel):
    fen: str
    elo: int = Field(default=1200, ge=1, le=2000)
    human_color: Literal["white", "black", "random"] = "white"


class ImporterPgnRequete(BaseModel):
    pgn: str
    elo: int = Field(default=1200, ge=1, le=2000)
    human_color: Literal["white", "black", "random"] = "white"


class PgnReponse(BaseModel):
    pgn: str


class FenReponse(BaseModel):
    fen: str


def _reponse_nouvelle_partie(partie, coup_moteur, service) -> NouvellePartieReponse:
    etat = service.obtenir_etat(partie.id)
    return NouvellePartieReponse(
        game_id=etat.game_id,
        fen=etat.fen,
        turn=etat.turn,
        evaluation=etat.evaluation,
        elo=etat.elo,
        human_color=etat.human_color,
        engine_move=coup_moteur,
        is_game_over=etat.is_game_over,
        result=etat.result,
        is_human_turn=etat.is_human_turn,
    )


@router.post("/new", response_model=NouvellePartieReponse)
def nouvelle_partie(
    requete: NouvellePartieRequete,
    service: ServiceMoteur = Depends(obtenir_service),
) -> NouvellePartieReponse:
    try:
        partie, coup_moteur = service.nouvelle_partie(
            elo=requete.elo,
            couleur_humain=requete.human_color,
            fen=requete.fen,
        )
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur)) from erreur

    return _reponse_nouvelle_partie(partie, coup_moteur, service)


@router.post("/load-fen", response_model=NouvellePartieReponse)
def charger_fen(
    requete: ChargerFenRequete,
    service: ServiceMoteur = Depends(obtenir_service),
) -> NouvellePartieReponse:
    try:
        partie, coup_moteur = service.charger_fen(
            fen=requete.fen,
            elo=requete.elo,
            couleur_humain=requete.human_color,
        )
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur)) from erreur

    return _reponse_nouvelle_partie(partie, coup_moteur, service)


@router.post("/import-pgn", response_model=NouvellePartieReponse)
def importer_pgn(
    requete: ImporterPgnRequete,
    service: ServiceMoteur = Depends(obtenir_service),
) -> NouvellePartieReponse:
    try:
        partie, coup_moteur = service.importer_pgn(
            pgn_texte=requete.pgn,
            elo=requete.elo,
            couleur_humain=requete.human_color,
        )
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur)) from erreur

    return _reponse_nouvelle_partie(partie, coup_moteur, service)


@router.get("/{game_id}/pgn", response_model=PgnReponse)
def exporter_pgn(
    game_id: str,
    service: ServiceMoteur = Depends(obtenir_service),
) -> PgnReponse:
    try:
        pgn = service.exporter_pgn(game_id)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    return PgnReponse(pgn=pgn)


@router.get("/{game_id}/fen", response_model=FenReponse)
def exporter_fen(
    game_id: str,
    service: ServiceMoteur = Depends(obtenir_service),
) -> FenReponse:
    try:
        fen = service.exporter_fen(game_id)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    return FenReponse(fen=fen)


@router.post("/{game_id}/move", response_model=CoupReponse)
def jouer_coup(
    game_id: str,
    requete: CoupRequete,
    service: ServiceMoteur = Depends(obtenir_service),
) -> CoupReponse:
    try:
        resultat = service.jouer_coup_humain(game_id, requete.uci)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    except ValueError as erreur:
        raise HTTPException(status_code=400, detail=str(erreur)) from erreur

    return CoupReponse(
        fen=resultat.fen,
        turn=resultat.turn,
        evaluation=resultat.evaluation,
        human_move=resultat.human_move,
        engine_move=resultat.engine_move,
        is_game_over=resultat.is_game_over,
        result=resultat.result,
    )


@router.get("/{game_id}/state", response_model=EtatReponse)
def etat_partie(
    game_id: str,
    service: ServiceMoteur = Depends(obtenir_service),
) -> EtatReponse:
    try:
        etat = service.obtenir_etat(game_id)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur

    return EtatReponse(
        game_id=etat.game_id,
        fen=etat.fen,
        turn=etat.turn,
        evaluation=etat.evaluation,
        elo=etat.elo,
        human_color=etat.human_color,
        moves=etat.moves,
        is_game_over=etat.is_game_over,
        result=etat.result,
        is_human_turn=etat.is_human_turn,
    )


@router.get("/{game_id}/hints", response_model=HintsReponse)
def suggestions_partie(
    game_id: str,
    service: ServiceMoteur = Depends(obtenir_service),
) -> HintsReponse:
    try:
        suggestions = service.obtenir_suggestions(game_id)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur

    return HintsReponse(
        suggestions=[
            SuggestionReponse(uci=s.uci, san=s.san, score=s.score)
            for s in suggestions
        ]
    )


@router.get("/{game_id}/threats", response_model=MenacesReponse)
def menaces_partie(
    game_id: str,
    service: ServiceMoteur = Depends(obtenir_service),
) -> MenacesReponse:
    try:
        menaces = service.obtenir_menaces(game_id)
    except KeyError as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur

    return MenacesReponse(
        threatened_pieces=[
            PieceMenaceeReponse(
                square=p.square,
                piece=p.piece,
                attackers=p.attackers,
                defenders=p.defenders,
                undefended=p.undefended,
            )
            for p in menaces.threatened_pieces
        ],
        critical_squares=menaces.critical_squares,
    )
