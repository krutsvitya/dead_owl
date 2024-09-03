import telebot
import pandas as pd
from random import randint
import time
from telebot import types
import pickle
from database import Dictionary, record_exists
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('dead-owl-7c4759a624ca.json', scope)
client = gspread.authorize(creds)

# Вставьте идентификатор вашей таблицы
spreadsheet_id = '1XmezWAWkYB64nX1llWarvgrUYKr0-StjuE1jsqmkK3M'

BOT_TOKEN = '7479339906:AAFJ0dYHhhZCoDkeIL9ObsSKSM2NSGW4dCI'

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

markup = types.InlineKeyboardMarkup()

button1 = types.InlineKeyboardButton('Начать', callback_data='/start')
button2 = types.InlineKeyboardButton("Помощь", callback_data='/help')
button3 = types.InlineKeyboardButton("Мой словарь", callback_data='/dictionary')
button4 = types.InlineKeyboardButton('Добавить новое слово', callback_data='/add_new_word')
button5 = types.InlineKeyboardButton('Удалить слово', callback_data='/delete_word')
button6 = types.InlineKeyboardButton('Начать квиз', callback_data='/start_quiz')
button7 = types.InlineKeyboardButton('Изменить частоту вопросов', callback_data='/set_period')
button8 = types.InlineKeyboardButton('Остановить квиз', callback_data='/stop_quiz')
button9 = types.InlineKeyboardButton('Импортировать слова', callback_data='/from_table')
markup.add(button1, button2, button3, button4, button5, button6, button7, button8, button9)


def show_keyboard(message):
    bot.send_message(message.chat.id, "Выберите действие: ", reply_markup=markup)


# class Dictionary:
#
#     def __init__(self, chat_id):
#         self.__chat_id = chat_id
#         self._period = 60
#         self._my_dict = {}
#
#     def set_period(self, new_period):
#         self._period = new_period
#
#     def add_new_word(self, word, translate):
#         self._my_dict[word] = translate


@bot.message_handler(commands=['start'])
def start(message):
    if record_exists(message.chat.id):
        bot.send_message(message.chat.id, 'Твой словарик у меня уже есть!')
        show_keyboard(message)
    else:
        new_dictionary = Dictionary(chat_id=message.chat.id, period=60, my_dict={}, quiz=False)
        Dictionary.save(new_dictionary)
        bot.send_message(message.chat.id, 'Поехали!')
        show_keyboard(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    message = call.message
    if call.data == "/help":
        help(message)
    elif call.data == "/dictionary":
        get_dictionary(message)
    elif call.data == "/add_new_word":
        add_new_word(message)
    elif call.data == "/delete_word":
        delete_word(message)
    elif call.data == "/start":
        start(message)
    elif call.data == "/start_quiz":
        create_quiz(message)
    elif call.data == "/set_period":
        print('lalalalala')
        set_period(message)
    elif call.data == "/stop_quiz":
        stop_quiz(message)
    elif call.data == "/from_table":
        add_words_from_table(message)


@bot.message_handler(commands=['dictionary'])
def get_dictionary(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    data = loaded_obj.my_dict
    words = ''
    for item in data:
        # print(item + ": " + data[item])
        if words == '':
            words = item + ": " + data[item]
        else:
            words = words + '\n' + item + ": " + data[item]
    bot.send_message(message.chat.id, words)
    show_keyboard(message)


# def write_dict_to_file(filename, data):
#     with open(filename, 'a', encoding='utf-8') as file:
#         for key, value in data.items():
#             file.write(f"{key}: {value}\n")


# def save_data_to_file(filename, data):
#     with open(filename, 'w', encoding='utf-8') as file:
#         for key, value in data.items():
#             file.write(f"{key}: {value}\n")


@bot.message_handler(commands=['add_new_word'])
def add_new_word(message):
    bot.send_message(message.chat.id, "После этого сообщения укажите пожалуйста слово которое вы хотите выучить"
                                      " и через пробел его перевод. Например: Dog Собака\nНичего кроме слова и перевода"
                                      " писать не нужно!")
    bot.register_next_step_handler(message, add_new_word_process)


def add_new_word_process(message):
    loaded_obj = Dictionary.load(str(message.chat.id))

    command_with_args = message.text.split()

    if len(command_with_args) == 2:
        key = command_with_args[0]
        value = command_with_args[1]

        if key not in loaded_obj.my_dict.keys():
            loaded_obj.my_dict[key] = value
            Dictionary.save(loaded_obj)

            bot.send_message(message.chat.id, 'Слово успешно добавлено!')
            show_keyboard(message)
        else:
            bot.send_message(message.chat.id, 'Это слово уже есть у вас в словаре!')
    else:
        bot.send_message(message.chat.id, 'Нужно только 1 слово и его перевод!')
        show_keyboard(message)


@bot.message_handler(commands=['delete_word'])
def delete_word(message):
    bot.send_message(message.chat.id, "Напишите слово которое вы хотите удалить из словаря")
    bot.register_next_step_handler(message, delete_word_process)


def delete_word_process(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    data = loaded_obj.my_dict
    deletable_word = message.text
    print(deletable_word)
    if deletable_word in loaded_obj.my_dict.keys():
        data.pop(deletable_word)
        Dictionary.save(loaded_obj)
        bot.send_message(message.chat.id, 'Слово успешно удалено!')
        show_keyboard(message)
    else:
        bot.send_message(message.chat.id, 'Такого слова нет в вашем словаре!')
        delete_word(message)
        show_keyboard(message)


@bot.message_handler(commands=['start_quiz'])
def create_quiz(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    loaded_obj.quiz = True
    Dictionary.save(loaded_obj)
    while loaded_obj.quiz:
        # print(data_dict[message.chat.id]['quiz'])
        my_dict = loaded_obj.my_dict

        if len(my_dict) < 4:
            bot.send_message(message.chat.id, "В вашем словаре должно быть минимум 4 слова для того чтобы начать!")
            return 0

        words = list(my_dict.keys())
        length = len(my_dict) - 1
        question = words[randint(0, length)]
        answer = my_dict[question]
        words.remove(question)
        # print(question)

        options = []
        while len(options) < 3:
            length = len(words) - 1
            x = randint(0, length)
            word = my_dict[words[x]]
            words.remove(words[x])
            options.append(word)

        # print(options)
        options.insert(randint(0, 3), answer)
        # print(my_dict[question])
        bot.send_poll(
            chat_id=message.chat.id,
            question=question,
            options=options,
            type='quiz',
            correct_option_id=options.index(answer),
            is_anonymous=False
        )
        bot.send_message(message.chat.id, "Выберите действие: ", reply_markup=markup)
        time.sleep(60 * loaded_obj.period)
        loaded_obj = Dictionary.load(str(message.chat.id))


@bot.message_handler(commands=['stop_quiz'])
def stop_quiz(message):
    loaded_dict = Dictionary.load(str(message.chat.id))
    loaded_dict.quiz = False
    Dictionary.save(loaded_dict)
    bot.send_message(message.chat.id, "Квиз остановлен. Выберите следующее действие: ", reply_markup=markup)
    # print(data_dict[message.chat.id]['quiz'])


@bot.message_handler(commands=['set_period'])
def set_period(message):
    bot.send_message(message.chat.id, "Укажите в минутах, как часто вы хотите получать вопрос квиза: ")
    bot.register_next_step_handler(message, set_period_process)


def set_period_process(message):
    loaded_dict = Dictionary.load(str(message.chat.id))
    command_with_args = message.text.split()
    if len(command_with_args) == 1:
        loaded_dict.period = str(command_with_args[0])
        Dictionary.save(loaded_dict)
        bot.send_message(message.chat.id, "Период изменен.")
        show_keyboard(message)
        print(Dictionary.load(str(message.chat.id)).period)
    else:
        bot.send_message(message.chat.id, 'Нужно указать команду и время в минутах, как часто вы хотите получать'
                                          ' вопросы с квиза. Например: /set_period 60. Тогда вы будете получать'
                                          ' 1 вопррс в час.')
        show_keyboard(message)


@bot.message_handler(commands=['from_table'])
def add_words_from_table(message):
    bot.send_message(message.chat.id, "Чтобы бот мог импортировать вашу гугл таблицу вам нужно:\n"
                                      "1. Создать гугл таблицу и в первый столбец добавить слова которые вы хотите"
                                      " учить, а во второй слобец перевод этих слов.\n"
                                      "2. Теперь вам нужно дать права доступа к таблице. Нужно дать доступ - "
                                      "'Все у кого есть ссылка' с доступом читатель.\n"
                                      "3. После этого скопировать ссылку на таблицу и отправить ее в бот.\n"
                                      "4. После этого ваши слова добавятся в таблицу!")
    bot.send_message(message.chat.id, "Отправьте ссылку на гугл таблицу: ")
    bot.register_next_step_handler(message, add_words_from_table_process)


def add_words_from_table_process(message):
    loaded_dict = Dictionary.load(str(message.chat.id))
    if message.text.startswith('https://docs.google.com/spreadsheets/d/'):
        identifier = message.text.split('/')[5]
        print(identifier)
        try:
            sheet = client.open_by_key(identifier).sheet1
            column1 = sheet.col_values(1)
            column2 = sheet.col_values(2)
            old_words = []

            for item, item2 in zip(column1, column2):
                if item in loaded_dict.my_dict.keys():
                    old_words.append(item)
                    continue
                else:
                    loaded_dict.my_dict[item] = item2
            print("Данные успешно добавлены в словарь!")
            if len(old_words) > 0:
                result = ', '.join(old_words)
                bot.send_message(message.chat.id, f"Слово(а): {result} были пропущены, так как они уже есть"
                                                  f" в вашем словаре")
            bot.send_message(message.chat.id, "Данные успешно добавлены в словарь! Нажмите на 'Мой словарь'"
                                              " чтобы проверить!")
            Dictionary.save(loaded_dict)
            show_keyboard(message)
        except gspread.SpreadsheetNotFound:
            print("Таблица не найдена. Проверьте идентификатор и доступ.")
            show_keyboard(message)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            show_keyboard(message)
    else:
        bot.send_message(message.chat.id, "Неверная ссылка!")
        add_words_from_table(message)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Приветствую! Для того чтобы начать пользовать ботом вам необходимо '
                                      'добавить слова в словарь. Чтобы добавить слово в словарь вам нужно написать'
                                      ' команду: /add_new_word и указать слово и его перевод вместе с командой.'
                                      ' После команды указать новое слово и перевод этого слова чтобы'
                                      ' это выглядело так: /add_new_word dog собака \nЧтобы удалить слово'
                                      ' используйте /delete_word и указываете слово которое хотите удалить(не'
                                      ' его перевод, а само слово). Это должно выгядеть так:'
                                      ' /delete_word dog \nЧтобы посмотреть все слова в'
                                      ' словаре используйте: /dictionary \nПосле добавления минимум 4'
                                      ' слов вы можете начать Квиз! Чтобы начать квиз нужно написать команду:'
                                      ' /start_quiz. Чтобы оставновить квиз используйте команду /stop_quiz.\nТакже'
                                      ' вы можете изменить период как часто вам будут приходить вопросы с квиза.'
                                      ' Для этого нужно использовать команду /set_period и время в минутах.'
                                      ' Например: /set_period 30 тогда вам будет приходить вопрос каждые пол часа.')
    bot.send_message(message.chat.id, "Выберите действие: ", reply_markup=markup)


bot.infinity_polling()
