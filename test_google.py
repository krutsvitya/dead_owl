import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Установите ваши учетные данные
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('app/dead-owl-7c4759a624ca.json', scope)
client = gspread.authorize(creds)

# Вставьте идентификатор вашей таблицы
spreadsheet_id = '1XmezWAWkYB64nX1llWarvgrUYKr0-StjuE1jsqmkK3M'  # Замените на ваш идентификатор

# Открываем таблицу по идентификатору
try:
    sheet = client.open_by_key(spreadsheet_id).sheet1  # Используйте sheet1 или другой индекс
    column1 = sheet.col_values(1)  # Первый столбец
    column2 = sheet.col_values(2)  # Второй столбец

    # Создайте словарь из данных
    data_dict = {}
    for item, item2 in zip(column1, column2):
        data_dict[item.strip()] = item2.strip()  # Убираем пробелы

    # Выводим словарь
    print("Данные успешно получены:")
    print(data_dict)
except gspread.SpreadsheetNotFound:
    print("Таблица не найдена. Проверьте идентификатор и доступ.")
except Exception as e:
    print(f"Произошла ошибка: {e}")
