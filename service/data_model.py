from pydantic import BaseModel


class GameRequest(BaseModel):
    word: str


class GameResponse(BaseModel):
    num_generations: int
    score: int
    stop_reason: str
