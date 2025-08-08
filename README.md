# English Words Trainer Bot

## Описание проекта

English Words Trainer Bot — это Telegram-бот для изучения английских слов. Бот позволяет пользователям тренировать свой словарный запас английского языка с помощью интерактивных упражнений, а также создавать и редактировать собственный словарь.

## Основные возможности

- 📝 Тренировка английских слов в интерактивном режиме
- ➕ Добавление собственных слов в персональный словарь
- 🔙 Удаление слов из персонального словаря
- 📚 Просмотр всех слов в персональном словаре
- 🔄 Использование как общего, так и персонального словаря

## Технологии

- Python 3.9+
- python-telegram-bot 22.2+
- SQLAlchemy 2.0+
- PostgreSQL

## Требования

- Python 3.9 или выше
- PostgreSQL
- Токен Telegram-бота (получается у @BotFather в Telegram)

## Установка и запуск

### Подготовка окружения

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/english-words-trainer-bot.git
   cd english-words-trainer-bot
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создайте базу данных в PostgreSQL:
   ```sql
   CREATE DATABASE english_trainer;
   ```

### Настройка

1. Откройте файл `db.py` и измените строку подключения к базе данных на вашу:
   ```python
   self.engine = create_engine('postgresql://username:password@localhost:5432/english_trainer')
   ```

2. Откройте файл `main.py` и замените токен бота на ваш:
   ```python
   app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
   ```

3. Для обеспечения безопасности рекомендуется использовать переменные окружения для хранения чувствительных данных:
   - Создайте файл `.env` в корне проекта
   - Добавьте переменные:
     ```
     DB_USER=username
     DB_PASSWORD=password
     DB_HOST=localhost
     DB_PORT=5432
     DB_NAME=english_trainer
     TELEGRAM_BOT_TOKEN=your_token
     ```
   - Установите пакет python-dotenv и используйте его для загрузки переменных окружения

### Запуск бота