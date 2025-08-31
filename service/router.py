import os

from fastapi import APIRouter, HTTPException

from .cgol_engine import GameOfLifeEngine
from .data_model import GameRequest, GameResponse
from .db.db_service import SQLiteService

router = APIRouter(prefix="/cgol")


@router.post("/game")
async def run_game(request: GameRequest) -> GameResponse:
    word = request.word
    db_service = SQLiteService(os.environ["ENGINE_DB_URL"])

    if not isinstance(word, str):
        raise HTTPException(status_code=400, detail="Provided word must be a string")
    if not word:
        raise HTTPException(status_code=400, detail="Provided word should have at least one character")
    if not word.isascii():
        raise HTTPException(status_code=400, detail="Provided word should contain only ASCII characters")

    db_response = db_service.get_response(word)
    if db_response is None:
        engine = GameOfLifeEngine()
        response = engine.run_from_word_cpp(word)
        db_service.insert_response(word=word, response=response)
    else:
        response = GameResponse(
            num_generations=db_response.num_generations,
            score=db_response.score,
            stop_reason=db_response.stop_reason,
        )

    return response
