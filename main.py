import telebot
import pandas as pd

BOT_TOKEN= '7479339906:AAFJ0dYHhhZCoDkeIL9ObsSKSM2NSGW4dCI'

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

file_path = 'data.xlsx'
sheet_name = 'table1'

df = pd.read_excel(file_path, sheet_name=sheet_name)

column_names = df.columns
print(column_names)

column1 = df['Original']  # Замените 'Column1' на название первого столбца
column2 = df['Translate']  # Замените 'Column2' на название второго столбца

dictionary = dict()
for item, item2 in zip(column1, column2):
    dictionary[item.strip('\xa0')] = item2.strip('\xa0')

print(dictionary)

bot.infinity_polling()
