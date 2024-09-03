import telebot
from random import randint
import time
from database import Dictionary, record_exists, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from keyboard import markup_main, markup_dict, markup_quiz, markup_end_quiz
from telebot import types
import threading

BOT_TOKEN = '7479339906:AAFJ0dYHhhZCoDkeIL9ObsSKSM2NSGW4dCI'

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

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


def show_keyboard(chat_id, markup):
    return bot.send_message(chat_id, "Выберите действие: ", reply_markup=markup)


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
    show_keyboard(message.chat.id, markup_dict)


def add_new_word(message):
    bot.send_message(message.chat.id, "Напишите слово которое хотите учить и добавить в словарь: ")
    bot.register_next_step_handler(message, add_new_word_process)


def add_new_word_process(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    key = message.text

    logging.info(f'Слово {key} {key.lower()}     {loaded_obj.my_dict.keys()}')
    if key.lower() not in (item.lower() for item in loaded_obj.my_dict.keys()):

        bot.send_message(message.chat.id, 'Теперь введите перевод слова: ')
        bot.register_next_step_handler(message, add_new_word_process2, key, loaded_obj)

    else:
        bot.send_message(message.chat.id, 'Это слово уже есть у вас в словаре!')


def add_new_word_process2(message, new_word, loaded_obj):
    value = message.text

    loaded_obj.my_dict[new_word] = value
    Dictionary.save(loaded_obj)

    bot.send_message(message.chat.id, 'Слово успешно добавлено!')
    show_keyboard(message.chat.id, markup_dict)


def delete_word(message):
    bot.send_message(message.chat.id, "Напишите слово которое вы хотите удалить из словаря")
    bot.register_next_step_handler(message, delete_word_process)


def delete_word_process(message):
    loaded_obj = Dictionary.load(str(message.chat.id))
    data = loaded_obj.my_dict
    deletable_word = message.text
    print(deletable_word)
    if deletable_word.lower() in (item.lower() for item in loaded_obj.my_dict.keys()):
        for item in loaded_obj.my_dict.keys():
            if item.lower() == deletable_word.lower():
                data.pop(item)
                break

        Dictionary.save(loaded_obj)
        bot.send_message(message.chat.id, 'Слово успешно удалено!')
        show_keyboard(message.chat.id, markup_dict)
    else:
        bot.send_message(message.chat.id, 'Такого слова нет в вашем словаре!')
        delete_word(message)


def start_quiz_in_thread(chat_id):
    quiz_thread = threading.Thread(target=create_quiz, args=(chat_id,))
    quiz_thread.start()


def create_quiz(chat_id):
    print(chat_id)
    last_message = None
    loaded_obj = Dictionary.load(str(chat_id))
    logging.info(f'Пользователь {chat_id} начал квиз. {type(loaded_obj)}  {loaded_obj.chat_id}')
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
            # print(question)

            while len(options) < 3:
                length = len(words) - 1
                x = randint(0, length)
                word = my_dict[words[x]]
                words.remove(words[x])
                options.append(word)

            # print(options)
            options.insert(randint(0, 3), answer)
            # print(my_dict[question])

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


def stop_quiz(message):
    loaded_dict = Dictionary.load(str(message.chat.id))
    loaded_dict.quiz = False
    bot.send_message(message.chat.id, "Квиз остановлен")
    logging.info(f'Пользователь {message.chat.id} остановил квиз. {type(loaded_dict)}  {loaded_dict.chat_id}')
    Dictionary.save(loaded_dict)
    show_keyboard(message.chat.id, markup_quiz)
    # print(data_dict[message.chat.id]['quiz'])


def set_period(message):
    bot.send_message(message.chat.id, "Укажите в минутах, как часто вы хотите получать вопрос квиза: ")
    bot.register_next_step_handler(message, set_period_process)


def set_period_process(message):
    try:
        loaded_obj = Dictionary.load(str(message.chat.id))
        command_with_args = message.text.split()

        logging.info(f'Пользователь {message.chat.id} изменил период. {type(loaded_obj)}  {loaded_obj.chat_id}')

        if len(command_with_args) == 1:
            if int(command_with_args[0]) < 1:
                loaded_obj.period = '1'
            else:
                loaded_obj.period = int(command_with_args[0])

            loaded_obj.period = str(command_with_args[0])
            Dictionary.save(loaded_obj)
            bot.send_message(message.chat.id, "Период изменен")
            show_keyboard(message.chat.id, markup_quiz)
            print(Dictionary.load(str(message.chat.id)).period)
        else:
            bot.send_message(message.chat.id, 'Нужно указать команду и время в минутах, как часто вы хотите получать'
                                              ' вопросы с квиза. Например: /set_period 60. Тогда вы будете получать'
                                              ' 1 вопррс в час.')
            show_keyboard(message.chat.id, markup_quiz)
    except TypeError as e:
        logging.error(f'Ошибка {e}')


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
    loaded_obj = Dictionary.load(str(message.chat.id))
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
                bot.send_message(message.chat.id, f"Слово(а): {result} были пропущены, так как они уже есть в вашем "
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
        add_words_from_table(message)


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
    show_keyboard(message.chat.id, markup_main)


# def main():
#
#
#
#     active_quiz_users = session.query(Dictionary).filter(Dictionary.quiz == '1').all()
#     print(active_quiz_users)
#     # for user in active_quiz_users:
#     #     fake_callback = types.CallbackQuery(
#     #         id='12345',
#     #         from_user=types.User(id=user.chat_id, is_bot=False, first_name='TestUser'),
#     #         message=types.Message(
#     #             message_id=1,
#     #             date=0,
#     #             chat=types.Chat(id=user.chat_id, type='private'),
#     #             content_type='text',
#     #             from_user=types.User(id=user.chat_id, is_bot=False, first_name='TestUser'),
#     #             options={},
#     #             json_string=''
#     #         ),
#     #         chat_instance='instance',
#     #         data='/start_quiz',
#     #         json_string=''
#     #     )
#     #     callback_handler(fake_callback)
#
#     bot.infinity_polling()


bot.infinity_polling()

# if __name__ == "__main__":
#     main()


