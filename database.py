from sqlalchemy import create_engine, Column, Integer, String, PickleType, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pickle

engine = create_engine('sqlite:///objects.db')
Base = declarative_base()

# 211667308


class Dictionary(Base):
    __tablename__ = 'dictionaries'

    chat_id = Column(String, primary_key=True)
    period = Column(Integer)
    my_dict = Column(PickleType)
    quiz = Column(Boolean)

    @classmethod
    def save(cls, obj):
        session = Session()  # Создание сессии
        session.merge(obj)  # merge позволяет обновлять существующий объект
        session.commit()
        session.close()

    @classmethod
    def load(cls, chat_id):
        session = Session()  # Создание сессии
        obj = session.query(cls).filter_by(chat_id=chat_id).first()
        session.close()
        return obj

    @classmethod
    def start_quiz(cls):
        cls.quiz = True


def record_exists(chat_id):
    record = session.query(Dictionary).filter(Dictionary.chat_id == chat_id).first()
    return record is not None


def update_existing_records():
    # Получение всех записей
    records = session.query(Dictionary).all()
    for record in records:
        record.quiz = False  # Установка значения для нового поля
    session.commit()


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


# loaded_obj = Dictionary.load("211667308")
# if loaded_obj:
#     print(f"Loaded from DB: {loaded_obj.chat_id}, {loaded_obj.period}, {loaded_obj.my_dict}")


