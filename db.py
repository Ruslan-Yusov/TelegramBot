import random

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, mapped_column, relationship


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
        self.engine = create_engine('postgresql://postgres:admin@localhost:5432/postgres')

    def session(self) -> Session:
        return Session(self.engine)

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
        count = min(4, len(word_pairs)) if word_pairs else 0
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
