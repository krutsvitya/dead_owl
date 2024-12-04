import telebot.apihelper
from telebot import types
from random import randint
import time
from database import Dictionary, record_exists, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from keyboard import markup_main, markup_dict, markup_quiz, markup_end_quiz, show_keyboard
import threading
import requests
import re
from bot import bot
import logging

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('dead-owl-7c4759a624ca.json', scope)
client = gspread.authorize(creds)

spreadsheet_id = '1XmezWAWkYB64nX1llWarvgrUYKr0-StjuE1jsqmkK3M'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Запись логов в файл
        logging.StreamHandler()  # Вывод логов в консоль
    ]
)


class Quiz:
    def __init__(self, owner: Dictionary):
        self.owner = owner
        self.last_message = None
        self.words = list(self.owner.my_dict.keys())
        self.owner.quiz = True
        Dictionary.save(owner)

        while Dictionary.load(str(self.owner.chat_id)).quiz:
            self.quiz_type = randint(0, 1)

            if len(self.words) < 4:
                bot.send_message(self.owner.chat_id, "В вашем словаре должно быть минимум 4 слова для того чтобы начать!")
                break
            elif not Dictionary.load(str(self.owner.chat_id)).quiz:
                break

            options = []
            if self.quiz_type == 0:
                question = self.words[randint(0, len(self.words))]
                answer = self.owner.my_dict[question]
                self.words.remove(question)
                for i in range(3):
                    options.append(self.owner.my_dict[self.words[randint(0, len(self.words))]])
                options.insert(randint(0, 3), answer)
            else:
                answer = self.words[randint(0, len(self.words) - 1)]
                question = self.owner.my_dict[answer]
                self.words.remove(answer)
                for i in range(3):
                    options.append(self.words[randint(0, len(self.words) - 1)])
                options.insert(randint(0, 3), answer)

            if self.last_message is not None:
                bot.delete_message(chat_id=self.owner.chat_id, message_id=self.last_message.message_id)
            bot.send_poll(
                chat_id=self.owner.chat_id,
                question=question,
                options=options,
                type='quiz',
                correct_option_id=options.index(answer),
                is_anonymous=False
            )

            self.last_message = show_keyboard(self.owner.chat_id, markup_end_quiz)
            time.sleep(60 * int(self.owner.period))
            # time.sleep(10)
            self.words = list(self.owner.my_dict.keys())

        del self

    # def create_quiz(self):
    #     last_message = None
    #     Dictionary.save(self.owner)
    #
    #     while self.quiz_started:
    #         which_quiz = randint(0, 1)
    #         this_dict = self.owner.my_dict
    #         if len(this_dict) < 4:
    #             bot.send_message(self.owner.chat_id, "В вашем словаре должно быть минимум 4 слова для того чтобы начать!")
    #             return 0
    #         words = list(this_dict.keys())
    #         length = len(words) - 1
    #         options = []


def edit_keyboard(message, markup):
    bot.edit_message_reply_markup(message.chat.id, message_id=message.message_id, reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    if record_exists(message.chat.id):
        bot.send_message(message.chat.id, 'Твой словарик у меня уже есть!')
        show_keyboard(message.chat.id, markup_main)
    else:
        new_dictionary = Dictionary(chat_id=message.chat.id, period=60, my_dict={}, quiz=False)
        Dictionary.save(new_dictionary)
        bot.send_message(message.chat.id, 'Поехали!')
        show_keyboard(message.chat.id, markup_main)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    message = call.message
    logging.info(f'Пользователь с id: {message.chat.id} нажал {call.data}')
    if call.data == "/help":
        help(message)
    elif call.data == "/my_dictionary":
        get_dictionary(message)
    elif call.data == "/add_new_word":
        add_new_word(message)
    elif call.data == "/delete_word":
        delete_word(message)
    elif call.data == "/start_quiz":
        logging.info(f'Пользователь {message.chat.id} начал квиз.')
        start_quiz_in_thread(message.chat.id)
    elif call.data == "/set_period":
        print('lalalalala')
        set_period(message)
    elif call.data == "/stop_quiz":
        stop_quiz(message)
    elif call.data == "/from_table":
        add_words_from_table(message)
    elif call.data == "/":
        edit_keyboard(message, markup_main)
    elif call.data == "/dictionary":
        edit_keyboard(message, markup_dict)
    elif call.data == "/quiz":
        edit_keyboard(message, markup_quiz)
    elif call.data == "/quiz_nonstop":
        quiz_nonstop(message)
    elif call.data == "/random_word":
        add_random_word(message)
    elif call.data == "/complete_sentences":
        complete_sentences(message)


def get_dictionary(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    data = loaded_obj.my_dict
    words = ''
    for item in data:
        # print(item + ": " + data[item])
        if words == '':
            words = f"<b>{item}</b>: " + data[item]
        else:
            words = words + '\n' +  f"<b>{item}</b>: " + data[item]
    bot.send_message(message.chat.id, words, parse_mode='html')
    show_keyboard(message.chat.id, markup_dict)


def add_new_word(message):
    bot.send_message(message.chat.id, "Напишите слово которое хотите учить и добавить в словарь: ")
    bot.register_next_step_handler(message, add_new_word_process)


def add_new_word_process(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    key = message.text

    logging.info(f'Слово {key} {key.lower()}     {loaded_obj.my_dict.keys()}')
    if not loaded_obj.check_dict(key):
        bot.send_message(message.chat.id, 'Теперь введите перевод слова: ')
        bot.register_next_step_handler(message, add_new_word_process2, key, loaded_obj)

    else:
        bot.send_message(message.chat.id, 'Это слово уже есть у вас в словаре!')


def add_new_word_process2(message, new_word, loaded_obj):
    loaded_obj.add_word(new_word, message.text)

    bot.send_message(message.chat.id, 'Слово успешно добавлено!')
    show_keyboard(message.chat.id, markup_dict)


def add_random_word(message: types.Message):
    # Конфигурация Wordnik API
    api_key = 'fymddc6fd7x0g959jpbrdtmmk2o4tavydzuwmant777tbj7yb'
    api_url = 'https://api.wordnik.com/v4/words.json/randomWord'

    # Получение случайного слова
    params = {
        'hasDictionaryDef': True,
        'api_key': api_key
    }
    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        random_word = response.json()['word']

        # Параметры запроса
        source_lang = 'en'  # Язык исходного текста (английский)
        target_lang = 'ru'  # Язык перевода (русский)'  # Текст для перевода

        url = f'https://lingva.ml/api/v1/{source_lang}/{target_lang}/{random_word}'

        response = requests.get(url)

        if response.status_code == 200:
            translated_text = response.json()['translation']
            print(f'Перевод: {translated_text}')
            logging.info(f'Пользователь: {message.chat.id} получил слово - {random_word}, перевод - {translated_text}')
            markup_random_word = types.ReplyKeyboardMarkup()

            button_add_word_to_dictionary = types.KeyboardButton(f'Добавить {random_word} в словарь')
            button_change_word = types.KeyboardButton('Поменять слово')
            button_cancel = types.KeyboardButton('Отказаться')

            markup_random_word.row(button_add_word_to_dictionary)
            markup_random_word.row(button_change_word, button_cancel)

            bot.send_message(message.chat.id, f'Случайное слово: <b>{random_word}</b>. Слово переводится как - <b>'
                                              f'{translated_text}</b>\n'
                                              f'Вы можете добавить слово в свой словарь или отказаться',
                             parse_mode='html',
                             reply_markup=markup_random_word)

            bot.register_next_step_handler(message, add_random_word_process, random_word, translated_text,
                                           markup_random_word)
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка. Пропробуйте позже')
            print(f'Ошибка при переводе: {response.status_code}')



    else:
        print(f'Ошибка при получении случайного слова: {response.status_code}')


def add_random_word_process(message, word, translate, markup_random_word):
    if message.text == f'Добавить {word} в словарь':
        loaded_obj = Dictionary.load(str(message.chat.id))

        if not loaded_obj.check_dict(word):
            loaded_obj.add_word(word, translate)
            Dictionary.save(loaded_obj)

            bot.send_message(message.chat.id, f'Слово <b>{word}</b> успешно добавлено!', parse_mode='html',
                             reply_markup=types.ReplyKeyboardRemove())
            show_keyboard(message.chat.id, markup_dict)
    elif message.text == 'Отказаться':
        bot.send_message(message.chat.id, f'Вы отказались от слова: <b>{word}</b>',
                         reply_markup=types.ReplyKeyboardRemove(), parse_mode='html')
        show_keyboard(message.chat.id, markup_dict)
        return
    elif message.text == 'Поменять слово':
        add_random_word(message)
    else:
        bot.send_message(message.chat.id, f'Ошибка. Попробуй еще раз', parse_mode='html',
                         reply_markup=markup_random_word)
        bot.register_next_step_handler(message, add_random_word_process, word, translate)


def delete_word(message):
    bot.send_message(message.chat.id, "Напишите слово которое вы хотите удалить из словаря")
    loaded_obj = Dictionary.load(str(message.chat.id))
    bot.register_next_step_handler(message, loaded_obj.delete_word)


def start_quiz_in_thread(chat_id):
    quiz_thread = threading.Thread(target=Quiz, args=(Dictionary.load(str(chat_id)),))
    quiz_thread.start()


def create_quiz(chat_id):
    last_message = None
    loaded_obj = Dictionary.load(str(chat_id))

    loaded_obj.quiz = True
    Dictionary.save(loaded_obj)

    while loaded_obj.quiz:
        which_quiz = randint(0, 1)
        my_dict = loaded_obj.my_dict
        if len(my_dict) < 4:
            bot.send_message(chat_id, "В вашем словаре должно быть минимум 4 слова для того чтобы начать!")
            return 0

        words = list(my_dict.keys())
        length = len(my_dict) - 1
        options = []
        if which_quiz == 0:

            question = words[randint(0, length)]
            answer = my_dict[question]
            words.remove(question)

            while len(options) < 3:
                length = len(words) - 1
                x = randint(0, length)
                word = my_dict[words[x]]
                words.remove(words[x])
                options.append(word)

            options.insert(randint(0, 3), answer)

        else:
            original_word = words[randint(0, length)]
            question = my_dict[original_word]
            answer = original_word
            words.remove(original_word)

            while len(options) < 3:
                length = len(words) - 1
                x = randint(0, length)
                options.append(words[x])
                words.remove(words[x])

            options.insert(randint(0, 3), answer)

        if last_message is not None:
            bot.delete_message(chat_id=chat_id, message_id=last_message.message_id)
        bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=options,
            type='quiz',
            correct_option_id=options.index(answer),
            is_anonymous=False
        )

        last_message = show_keyboard(chat_id, markup_end_quiz)
        time.sleep(60 * int(loaded_obj.period))
        # time.sleep(10)
        loaded_obj = Dictionary.load(str(chat_id))


def quiz_nonstop(message):
    chat_id = message.chat.id
    last_message = None
    loaded_obj = Dictionary.load(str(chat_id))
    logging.info(f'Пользователь {chat_id} начал нон-стоп. {type(loaded_obj)}  {loaded_obj.chat_id}')

    which_quiz = randint(0, 1)
    logging.info(f'Выпало {which_quiz}  нон-стоп')
    my_dict = loaded_obj.my_dict
    if len(my_dict) < 4:
        bot.send_message(chat_id, "В вашем словаре должно быть минимум 4 слова для того чтобы начать!")
        return 0

    words = list(my_dict.keys())
    if which_quiz == 0:

        length = len(my_dict) - 1
        options = []

        original_word = words[randint(0, length)]
        question = my_dict[original_word]
        answer = original_word
        words.remove(original_word)
        while len(options) < 3:
            length = len(words) - 1
            x = randint(0, length)
            options.append(words[x])
            words.remove(words[x])

        options.insert(randint(0, 3), answer)

        markup_answers = types.ReplyKeyboardMarkup()

        button1 = types.KeyboardButton(options[0])
        button2 = types.KeyboardButton(options[1])
        markup_answers.row(button1, button2)

        button1 = types.KeyboardButton(options[2])
        button2 = types.KeyboardButton(options[3])
        markup_answers.row(button1, button2)

        button1 = types.KeyboardButton('Закончить квиз')
        markup_answers.add(button1)
        bot.send_message(chat_id, f'Какое слово переводится как: <b>{question}</b>', parse_mode='html',
                         reply_markup=markup_answers)
        bot.register_next_step_handler(message, quiz_nonstop_process, answer, last_message, options, question)
    else:
        length = len(my_dict) - 1

        answer = words[randint(0, length)]
        question = my_dict[answer]

        markup_answers = types.ReplyKeyboardMarkup()
        button1 = types.KeyboardButton('Закончить квиз')
        markup_answers.add(button1)

        bot.send_message(message.chat.id, f"Напишите какое слово переводится как: <b>{question}</b>",
                         reply_markup=markup_answers, parse_mode='html')
        print(question)
        bot.register_next_step_handler(message, quiz_nonstop_process2, answer, last_message, question)


def quiz_nonstop_process(message, answer, last_message, options, question):
    if message.text == 'Закончить квиз':
        bot.send_message(message.chat.id, 'Квиз закончен', reply_markup=types.ReplyKeyboardRemove())
        return show_keyboard(message.chat.id, markup_quiz)

    elif not message.text.lower() == answer.lower():
        bot.send_message(message.chat.id, f'Неправильно. Попробуй еще раз!\nКакое слово переводится как:'
                                          f' <b>{question}</b>', parse_mode='html')
        logging.info(f'Варианты: {options}   Ответ пользователя: {message.text}')
        if message.text in options:
            options.remove(message.text)

        markup_answers = types.ReplyKeyboardMarkup()

        for item in options:
            button1 = types.KeyboardButton(item)
            markup_answers.add(button1)

        button1 = types.KeyboardButton('Закончить квиз')
        markup_answers.add(button1)

        bot.send_message(message.chat.id, "Выберите правильный вариант: ", reply_markup=markup_answers)

        bot.register_next_step_handler(message, quiz_nonstop_process, answer, last_message, options, question)

    else:
        bot.send_message(message.chat.id, f'Правильно! Молодец!', parse_mode='html')
        quiz_nonstop(message)


def quiz_nonstop_process2(message, answer, last_message, question):
    if message.text == 'Закончить квиз':
        bot.send_message(message.chat.id, 'Квиз закончен', reply_markup=types.ReplyKeyboardRemove())
        return show_keyboard(message.chat.id, markup_quiz)

    elif not message.text.lower() == answer.lower():
        logging.info(f'Правильный ответ: {question}   Ответ пользователя: {message.text}')

        markup_answers = types.ReplyKeyboardMarkup()
        button1 = types.KeyboardButton('Закончить квиз')
        markup_answers.add(button1)

        bot.send_message(message.chat.id, f"Неправильно. Попробуй еще раз!\n"
                                          f"Напишите какое слово переводится как: <b>{question}</b>",
                         reply_markup=markup_answers, parse_mode='html')
        print(question)
        bot.register_next_step_handler(message, quiz_nonstop_process2, answer, last_message, question)

    else:
        bot.send_message(message.chat.id, f'Правильно! Молодец!', parse_mode='html')
        quiz_nonstop(message)


def stop_quiz(message):
    loaded_dict = Dictionary.load(str(message.chat.id))
    loaded_dict.quiz = False
    bot.send_message(message.chat.id, "Квиз остановлен")
    logging.info(f'Пользователь {message.chat.id} остановил квиз. {type(loaded_dict)}  {loaded_dict.chat_id}')
    Dictionary.save(loaded_dict)
    show_keyboard(message.chat.id, markup_quiz)


def set_period(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    bot.send_message(message.chat.id, "Укажите в минутах, как часто вы хотите получать вопрос квиза.(Минимальное "
                                      "время - 1 минута)\n"
                                      f"Сейчас вы получаете вопрос каждые {loaded_obj.period} минут.")
    bot.register_next_step_handler(message, loaded_obj.set_period)


def complete_sentences(message):
    chat_id = message.chat.id
    loaded_obj = Dictionary.load(str(chat_id))
    words = list(loaded_obj.my_dict.keys())
    logging.info(f'слова: {words} {type(words)}')
    word = words[randint(0, len(words)) - 1]
    word = re.split(r'[\\,\.]', word)[0]
    word = re.sub(r'[^a-zA-Zа-яА-ЯёЁ ]', '', word)

    r = requests.request('GET', f'https://tatoeba.org/eng/api_v0/search?from=eng&query=%3D{word}')
    if len(r.json()['results']) > 0:
        x = randint(0, len(r.json()['results'])) - 1
        print(x)
        print(r.json()['results'][x]['text'])
        print(word)
        text = r.json()['results'][x]['text'].replace(word, '______').replace(word.lower(), '______')
        markup_sentences = types.ReplyKeyboardMarkup()

        button1 = types.KeyboardButton('Узнать ответ')
        button2 = types.KeyboardButton('Закончить')

        markup_sentences.add(button1, button2)
        message_for_user = bot.send_message(message.chat.id, 'Напишите слово из вашего словаря которое должно '
                                                             'быть на месте пропуска', reply_markup=markup_sentences)
        bot.send_message(chat_id, text)
        bot.register_next_step_handler(message, complete_sentences_process, word, text, message_for_user, markup_sentences)
    else:
        complete_sentences(message)


def complete_sentences_process(message, word, text, message_for_user, markup_sentences):
    if message.text.lower() == word.lower():
        bot.send_message(message.chat.id, 'Правильно! Молодец!')
        complete_sentences(message)
    elif message.text == 'Закончить':
        bot.send_message(message.chat.id, 'Закончили', reply_markup=types.ReplyKeyboardRemove())
        show_keyboard(message.chat.id, markup_quiz)
        return
    elif message.text == 'Узнать ответ':
        bot.send_message(message.chat.id, f'Правильный ответ был: <b>{word}</b>', parse_mode='html')
        complete_sentences(message)
    elif message.text != word:
        bot.send_message(message.chat.id, f'Неправильно, попробуй еще раз. {message_for_user.text}\n{text}',
                         reply_markup=markup_sentences)
        bot.register_next_step_handler(message, complete_sentences_process, word, text, message_for_user, markup_sentences)


def add_words_from_table(message: types.Message):
    photo_paths = ['photos/table1.jpg', 'photos/table2.jpg', 'photos/table3.jpg']

    media = [types.InputMediaPhoto(types.InputFile(photo)) for photo in photo_paths]

    bot.send_media_group(message.chat.id, media)

    bot.send_message(message.chat.id, "Чтобы бот импортировал ваши слова из гугл таблицы вам нужно:\n"
                                      "1. Создать гугл таблицу и в первый столбец добавить слова которые вы хотите"
                                      " учить, а во второй слобец перевод этих слов.(смотрите фото 1)\n"
                                      "2. Теперь вам нужно дать доступ боту к таблице. Нужно дать доступ - "
                                      "'Все у кого есть ссылка' с доступом читатель.(смотрите фото 1 и 2)\n"
                                      "3.Теперь скопируйте ссылку на таблицу и отправьте ее в этот чат."
                                      "(смотрите фото 3)\n"
                                      "4. После этого ваши слова добавятся в таблицу!")
    bot.send_message(message.chat.id, "Отправьте ссылку на гугл таблицу: ")
    bot.register_next_step_handler(message, add_words_from_table_process)


def add_words_from_table_process(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    try:
        if message.text.startswith('https://docs.google.com/spreadsheets/d/'):
            identifier = message.text.split('/')[5]
            try:
                sheet = client.open_by_key(identifier).sheet1
                column1 = sheet.col_values(1)
                column2 = sheet.col_values(2)
                old_words = []

                for item, item2 in zip(column1, column2):
                    if item.lower() in (key.lower() for key in loaded_obj.my_dict.keys()):
                        old_words.append(item)
                        continue
                    else:
                        loaded_obj.my_dict[item] = item2
                print("Данные успешно добавлены в словарь!")
                if len(old_words) > 0:
                    result = ', '.join(old_words)
                    bot.send_message(message.chat.id,
                                     f"Слово(а): {result} были пропущены, так как они уже есть в вашем "
                                     "словаре")

                bot.send_message(message.chat.id, "Данные успешно добавлены в словарь! Нажмите на 'Мой словарь'"
                                                  " чтобы проверить!")
                Dictionary.save(loaded_obj)
                show_keyboard(message.chat.id, markup_dict)
            except gspread.SpreadsheetNotFound:
                print("Таблица не найдена. Проверьте идентификатор и доступ.")
                show_keyboard(message.chat.id, markup_dict)
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                show_keyboard(message.chat.id, markup_dict)
        else:
            bot.send_message(message.chat.id, "Неверная ссылка!")
    except AttributeError as e:
        logging.info(f'Пользователь {message.chat.id} отправил не ссылку, что привело к {e}')
        bot.send_message(message.chat.id, "Неверная ссылка!")


def help(message):
    bot.send_message(message.chat.id, 'Приветствую! Бот предназначен для помощи людям учить новые слова.\n'
                                      'Для того чтобы начать пользовать ботом вам необходимо '
                                      'добавить слова в словарь. Для этого вы можете перейти в раздел "Словарь". '
                                      'Если у вас уже есть свой электронный словарь, вы можете запонить гугл таблицу '
                                      'и отправить ссылку в бот чтобы импортировать все ваши слова напрямую в бота,'
                                      ' подробнее по кнопке "Импортировать слова" в разделе "Словарь".\n'
                                      'Когда вы добавили хотя бы 4 слова в свой словарь, вы можете начать проходить квизы'
                                      ' которые помогут вам запоминать эти слова!\n'
                                      'Обычный квиз из себя представляет получение вопросов в течении дня с промежутком'
                                      ' во времени,который вы сами укажете(по умолчанию это 60 минут).\nТакже есть'
                                      ' второй вариант квиза, более интенсивный - Квиз(нон-стоп). Вопросы будут'
                                      ' приходить, после кадого ответа, также будут вопросы когда вам самим нужно'
                                      ' вписать слово.\nДля более подробного описания для каждой функции читайте '
                                      'информацию от бота когда нажимаете на кнопки.\nУдачного изучения языка!')
    show_keyboard(message.chat.id, markup_main)


def main():
    active_quiz_users = session.query(Dictionary).filter(Dictionary.quiz == '1').all()
    print(active_quiz_users)

    for user in active_quiz_users:
        logging.info(f'Продолжаем квиз пользователю: {user.chat_id}!')
        start_quiz_in_thread(user.chat_id)


    bot.infinity_polling()


if __name__ == "__main__":
    main()
