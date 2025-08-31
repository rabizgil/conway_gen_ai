from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..data_model import GameResponse
from .db_tables import Base, GameData


class SQLiteService:

    def __init__(self, db_name: str):
        self.url = "sqlite:///" + db_name

        self.engine = create_engine(self.url)
        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

    def insert_response(self, word: str, response: GameResponse):
        session = self.Session()

        try:
            game_data = GameData(
                word=word,
                num_generations=response.num_generations,
                score=response.score,
                stop_reason=response.stop_reason,
            )
            session.add(game_data)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"error occured on inserting game data. Error: {e}")
        finally:
            session.close()

    def get_response(self, word: str):
        session = self.Session()

        try:
            response = session.query(GameData).filter_by(word=word).first()
        except Exception as e:
            session.rollback()
            response = None
            print(f"error occured on loadig game data for word '{word}'. Error: {e}")
        finally:
            session.close()

        return response
