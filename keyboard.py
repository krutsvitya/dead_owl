from telebot import types


button2 = types.InlineKeyboardButton("Помощь", callback_data='/help')
button3 = types.InlineKeyboardButton("Мой словарь", callback_data='/my_dictionary')
button4 = types.InlineKeyboardButton('Добавить слово', callback_data='/add_new_word')
button5 = types.InlineKeyboardButton('Удалить слово', callback_data='/delete_word')
button6 = types.InlineKeyboardButton('Начать квиз', callback_data='/start_quiz')
button7 = types.InlineKeyboardButton('Изменить частоту вопросов', callback_data='/set_period')
button8 = types.InlineKeyboardButton('Остановить квиз', callback_data='/stop_quiz')
button9 = types.InlineKeyboardButton('Импортировать слова', callback_data='/from_table')
button10 = types.InlineKeyboardButton('Назад', callback_data='/')
button11 = types.InlineKeyboardButton('Cловарь', callback_data='/dictionary')
button12 = types.InlineKeyboardButton('Квиз', callback_data='/quiz')

markup_main = types.InlineKeyboardMarkup()
markup_main.row(button11, button12)
markup_main.row(button2)

markup_dict = types.InlineKeyboardMarkup()
markup_dict.row(button3, button4)
markup_dict.row(button5, button9)
markup_dict.row(button10)

markup_quiz = types.InlineKeyboardMarkup()
markup_quiz.row(button6, button7)
markup_quiz.row(button10)

markup_end_quiz = types.InlineKeyboardMarkup()
markup_end_quiz.add(button8, button10)
