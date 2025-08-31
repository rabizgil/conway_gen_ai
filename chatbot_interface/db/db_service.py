from argon2 import PasswordHasher
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db_tables import Base, User


class SQLiteService:

    def __init__(self, db_name: str):
        self.url = "sqlite:///" + db_name
        self.password_hasher = PasswordHasher()

        self.engine = create_engine(self.url)
        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

    def validate_user(self, username: str, password: str) -> bool:
        session = self.Session()
        matched: bool = False

        try:
            user_match = session.query(User).filter_by(username=username).first()
            if self.password_hasher.verify(user_match.password, password):  # type: ignore
                matched = True
        except Exception as e:
            session.rollback()
        finally:
            session.close()

        return matched

    def register_user(self, username: str, password: str) -> None:
        session = self.Session()

        try:
            password_hash = self.password_hasher.hash(password)
            user = User(username=username, password=password_hash)
            session.add(user)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error occured on registering user. Error: {e}")
        finally:
            session.close()
