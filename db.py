import random
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column, relationship

load_dotenv("config.env")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(nullable=False, unique=True)
    person_dictionary: Mapped[list["PersonDictionary"]] = relationship("PersonDictionary",
                                                                       back_populates="user")
    general_user_words: Mapped[list["GeneralDictionaryUser"]] = relationship("GeneralDictionaryUser",
                                                                             back_populates="users",
                                                                             cascade="all, delete-orphan")


class GeneralDictionary(Base):
    __tablename__ = 'general_dictionary'

    id: Mapped[int] = mapped_column(primary_key=True)
    en_word: Mapped[str] = mapped_column(nullable=False, unique=True)
    ru_word: Mapped[str] = mapped_column(nullable=False, unique=True)
    dictionary_users: Mapped[list["GeneralDictionaryUser"]] = relationship("GeneralDictionaryUser",
                                                                           back_populates="general_dictionaries",
                                                                           cascade="all, delete-orphan")


class PersonDictionary(Base):
    __tablename__ = 'person_dictionary'

    id: Mapped[int] = mapped_column(primary_key=True)
    en_word: Mapped[str] = mapped_column(nullable=False)
    ru_word: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(User, back_populates="person_dictionary")


class GeneralDictionaryUser(Base):
    __tablename__ = 'general_dictionary_user'

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True)
    users: Mapped[User] = relationship(User,
                                       back_populates="general_user_words")
    general_dictionary_id: Mapped[int] = mapped_column(
        ForeignKey("general_dictionary.id", ondelete="CASCADE"),
        primary_key=True)
    general_dictionaries: Mapped[GeneralDictionary] = relationship(GeneralDictionary,
                                                                   back_populates="dictionary_users")


class DB:
    def __init__(self):
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")

        if not all([db_user, db_password, db_host, db_port, db_name]):
            raise ValueError("One or more database parameters are not set in environment variables")
        self.engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

    def session(self) -> Session:
        return Session(self.engine)

    def populate_general_dictionary(self):
        predefined_words = [
            {"en_word": "apple", "ru_word": "яблоко"},
            {"en_word": "dog", "ru_word": "собака"},
            {"en_word": "cat", "ru_word": "кошка"},
            {"en_word": "house", "ru_word": "дом"},
            {"en_word": "car", "ru_word": "машина"},
            {"en_word": "book", "ru_word": "книга"},
            {"en_word": "sun", "ru_word": "солнце"},
            {"en_word": "moon", "ru_word": "луна"},
            {"en_word": "water", "ru_word": "вода"},
            {"en_word": "tree", "ru_word": "дерево"},
            {"en_word": "flower", "ru_word": "цветок"},
            {"en_word": "computer", "ru_word": "компьютер"}
        ]

        with self.session() as session:
            if not session.query(GeneralDictionary).first():
                words_to_add = [GeneralDictionary(**word) for word in predefined_words]
                session.add_all(words_to_add)
                session.commit()
                print("Таблица general_dictionary заполнена предопределёнными данными.")
            else:
                print("Таблица general_dictionary уже содержит данные.")

    def get_user(self, user_id: int) -> User.telegram_id:
        with self.session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
        return user

    def new_user(self, user_id: int):
        with self.session() as session:
            user = User(telegram_id=user_id)
            session.add(user)
            session.commit()

    def trainer(self, user_id: int) -> dict:
        result_dict = {}
        with self.session() as session:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if user:
                personal_words = session.query(PersonDictionary).filter(PersonDictionary.user_id == user.id).all()
                for p in personal_words:
                    result_dict[p.en_word] = [p.ru_word]
            general_words = session.query(GeneralDictionary).all()
            for g in general_words:
                result_dict[g.en_word] = [g.ru_word]

        word_pairs = list(result_dict.items())
        count = min(4, len(word_pairs))
        return random.sample(word_pairs, count) if count > 0 else []

    def add_personal_word(self, telegram_id: int, en_word: str, ru_word: str) -> bool:
        with self.session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False

            existing_word = session.query(PersonDictionary).filter(
                PersonDictionary.user_id == user.id,
                PersonDictionary.en_word == en_word
            ).first()

            if existing_word:
                return False

            new_word = PersonDictionary(
                en_word=en_word,
                ru_word=ru_word,
                user_id=user.id
            )
            session.add(new_word)
            session.commit()
            return True

    def delete_personal_word(self, telegram_id: int, en_word: str) -> bool:
        with self.session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False

            word_to_delete = session.query(PersonDictionary).filter(
                PersonDictionary.user_id == user.id,
                PersonDictionary.en_word == en_word
            ).first()

            if not word_to_delete:
                return False

            session.delete(word_to_delete)
            session.commit()
            return True

    def get_personal_words(self, telegram_id: int) -> list:
        result = []
        with self.session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                words = session.query(PersonDictionary).filter(
                    PersonDictionary.user_id == user.id
                ).all()

                for word in words:
                    result.append((word.en_word, word.ru_word))

        return result
