import telebot
import pandas as pd
from random import randint
import time
from telebot import types
import pickle
from database import Dictionary, record_exists

file_path = 'data.xlsx'
sheet_name = 'table1'

df = pd.read_excel(file_path, sheet_name=sheet_name)

data_dict = {}

column_names = df.columns
# print(column_names)

column1 = df['Original']  # Замените 'Column1' на название первого столбца
column2 = df['Translate']  # Замените 'Column2' на название второго столбца

dictionary = dict()
for item, item2 in zip(column1, column2):
    dictionary[item.strip('\xa0')] = item2.strip('\xa0')

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
markup.add(button1, button2, button3, button4, button5, button6, button7, button8)


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

        loaded_obj.my_dict[key] = value
        Dictionary.save(loaded_obj)

        bot.send_message(message.chat.id, 'Слово успешно добавлено!')
        show_keyboard(message)

    else:
        bot.send_message(message.chat.id, 'Нужно только 1 слово и его перевод!')
        show_keyboard(message)


@bot.message_handler(commands=['delete_word'])
def delete_word(message):
    bot.send_message(message.chat.id, "После этого сообщения укажите пожалуйста слово которое вы хотите удалить из"
                                      " вашего словаря. Например: Dog\nНужно написать слово,а не его перевод.")
    bot.register_next_step_handler(message, delete_word_process)


def delete_word_process(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    data = loaded_obj.my_dict
    command_with_args = message.text.split()
    print(command_with_args)
    if len(command_with_args) == 1:
        if command_with_args[0] not in data:
            bot.send_message(message.chat.id, 'Такого слова нет в вашем словаре!')
        elif command_with_args[0] in data:
            data.pop(command_with_args[0])
            Dictionary.save(loaded_obj)
            bot.send_message(message.chat.id, 'Слово успешно удалено!')
            show_keyboard(message)
    else:
        bot.send_message(message.chat.id, 'Для удаления слова нужно указать команду /delete_word и слово которое'
                                          ' вы хотите удалить(не его перевод, а само слово). Пример: /delete dog')
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
        time.sleep(10)
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
