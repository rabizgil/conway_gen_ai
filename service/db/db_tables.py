from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GameData(Base):
    __tablename__ = "game_requests"

    id = Column(Integer, primary_key=True, nullable=False)
    word = Column(String(250), unique=True, nullable=False)
    num_generations = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    stop_reason = Column(String(30), nullable=False)
