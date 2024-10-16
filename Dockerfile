# Базовый образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /dead_owl

# Копируем файл requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Указываем команду для запуска бота
CMD ["python", "main.py"]
