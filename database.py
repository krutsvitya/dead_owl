from sqlalchemy import create_engine, Column, Integer, String, PickleType, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pickle
from bot import bot
from keyboard import markup_main, markup_dict, markup_quiz, markup_end_quiz, show_keyboard
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Запись логов в файл
        logging.StreamHandler()  # Вывод логов в консоль
    ]
)

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

    def add_word(self, word, translate):
        self.my_dict[word] = translate
        Dictionary.save(self)

    def delete_word(self, message):
        deletable_word = message.text
        if not self.check_dict(deletable_word):
            bot.send_message(message.chat.id, 'Такого слова нет в вашем словаре!')
            return show_keyboard(message.chat.id, markup_dict)
        else:
            for item in self.my_dict.keys():
                if item.lower() == deletable_word.lower():
                    self.my_dict.pop(item)
                    break
            Dictionary.save(self)
            bot.send_message(message.chat.id, 'Слово успешно удалено!')
            show_keyboard(message.chat.id, markup_dict)

    def check_dict(self, word: str) -> bool:
        if word.lower() in (item.lower() for item in self.my_dict.keys()):
            print(word)
            return True
        else:
            return False

    def set_period(self, message):
        try:
            self.period = int(message.text)
            if self.period < 1:
                self.period = 1
            Dictionary.save(self)
            bot.send_message(message.chat.id, f"Период изменен. Теперь вы будете получать вопросы с квиза раз"
                                              f" в {self.period} минут.")
            show_keyboard(message.chat.id, markup_quiz)
        except (TypeError, ValueError) as e:
            logging.error(f'Ошибка {e}')
            bot.send_message(message.chat.id, 'Вам нужно написать время в минутах, как часто вы хотите получать'
                                              'вопросы с квиза. Это должно быть число')
            show_keyboard(message.chat.id, markup_quiz)


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


