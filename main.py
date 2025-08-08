import random
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

from db import DB

db = DB()

STATE_AWAITING_ACTION = 'awaiting_action'
STATE_ADDING_WORD = 'adding_word'
STATE_DELETING_WORD = 'deleting_word'
STATE_SHOWING_WORDS = 'showing_words'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['state'] = STATE_AWAITING_ACTION

    keyboard_old_user = [[InlineKeyboardButton('Продолжить тренировку 📝', callback_data='old_user')]]
    keyboard_new_user = [[InlineKeyboardButton('Начать тренировку 📝', callback_data='new_user')]]
    markup_old_user = InlineKeyboardMarkup(keyboard_old_user)
    markup_new_user = InlineKeyboardMarkup(keyboard_new_user)

    if db.get_user(update.effective_user.id) is None:
        await update.message.reply_text(f'Привет {update.effective_user.first_name}👋.\n '
                                        f'Давай попрактикуемся в английском языке. Тренировки можешь проходить в удобном для себя темпе.'
                                        f'У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.'
                                        f'Для этого воспользуйся инструментами:\n\n'
                                        f'добавить слово ➕,\n'
                                        f'удалить слово 🔙.\n\n'
                                        f'Ну что, начнём ⬇️', reply_markup=markup_new_user)
    else:
        await update.message.reply_text(f'С возвращением {update.effective_user.first_name}👋.\n'
                                        f'Давай продолжим практиковаться в английском языке',
                                        reply_markup=markup_old_user)


async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        await db.new_user(update.effective_user.id)
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
    await show_words(update, context)


async def old_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_words(update, context)


async def show_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = STATE_AWAITING_ACTION

    words = db.trainer(update.effective_user.id)
    if not words:
        keyboard = [['Добавить слово', 'Мой словарь']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await send_message(update, "У вас пока нет слов для тренировки. Добавьте новые слова в словарь.",
                           reply_markup=reply_markup)
        return

    keyword = [[word[0] for word in words],
               ['Добавить слово', 'Удалить слово', 'Мой словарь', 'Дальше']]
    random.shuffle(keyword[0])
    ru_words = words[0][1]

    context.user_data['current_word'] = words[0][0]
    context.user_data['current_translation'] = "".join(ru_words)
    context.user_data['all_words'] = words

    reply_markup = ReplyKeyboardMarkup(keyword, resize_keyboard=True, one_time_keyboard=True)
    await send_message(
        update,
        f'Переведи слово {"".join(ru_words)}',
        reply_markup=reply_markup
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'state' not in context.user_data:
        context.user_data['state'] = STATE_AWAITING_ACTION

    state = context.user_data['state']
    text = update.message.text

    if state == STATE_AWAITING_ACTION:
        if text == 'Дальше':
            await show_words(update, context)
        elif text == 'Добавить слово':
            context.user_data['state'] = STATE_ADDING_WORD
            await update.message.reply_text("Введите новое слово в формате: английское слово - русский перевод\n"
                                            "Например: apple - яблоко")
        elif text == 'Удалить слово':
            context.user_data['state'] = STATE_DELETING_WORD
            await prepare_delete_word(update, context)
        elif text == 'Мой словарь':
            context.user_data['state'] = STATE_SHOWING_WORDS
            await show_personal_dictionary(update, context)
        elif text == 'Продолжить тренировку':
            await show_words(update, context)
        else:
            await handle_word_selection(update, context)

    elif state == STATE_ADDING_WORD:
        await add_word(update, context)

    elif state == STATE_DELETING_WORD:
        await delete_word(update, context)

    elif state == STATE_SHOWING_WORDS:
        await dictionary_actions(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == 'new_user':
        await new_user(update, context)
    elif data == 'old_user':
        await old_user(update, context)


async def handle_word_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_word = update.message.text

    if 'current_word' in context.user_data:
        correct_word = context.user_data['current_word']
        translation = context.user_data['current_translation']

        if selected_word == correct_word:

            await update.message.reply_text(f"✅ Правильно! {selected_word} - {translation}")

            await show_words(update, context)
        else:

            await update.message.reply_text(f"❌ Неверно. Правильный ответ: {correct_word} - {translation}")

            keyboard = [['Дальше']]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Попробуйте другое слово или нажмите 'Дальше'", reply_markup=reply_markup)


async def prepare_delete_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    personal_words = db.get_personal_words(update.effective_user.id)

    if not personal_words:
        await update.message.reply_text("У вас пока нет слов в персональном словаре.")
        context.user_data['state'] = STATE_AWAITING_ACTION
        await show_words(update, context)
        return

    keyboard = []
    for en_word, ru_word in personal_words:
        keyboard.append([f"{en_word} - {ru_word}"])
    keyboard.append(['Отмена'])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите слово для удаления:", reply_markup=reply_markup)


async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word_text = update.message.text

    if word_text == 'Отмена':
        await update.message.reply_text("Добавление слова отменено.")
        context.user_data['state'] = STATE_AWAITING_ACTION
        await show_words(update, context)
        return

    match = re.match(r'^([a-zA-Z\s]+)\s*-\s*([а-яА-ЯёЁ\s]+)$', word_text)

    if not match:
        await update.message.reply_text(
            "Неправильный формат. Пожалуйста, введите слово в формате: английское слово - русский перевод")
        return

    en_word = match.group(1).strip().lower()
    ru_word = match.group(2).strip().lower()

    success = db.add_personal_word(update.effective_user.id, en_word, ru_word)

    if success:
        await update.message.reply_text(f"✅ Слово '{en_word} - {ru_word}' успешно добавлено в ваш словарь!")
    else:
        await update.message.reply_text("⚠️ Это слово уже существует в вашем словаре или произошла ошибка.")

    context.user_data['state'] = STATE_AWAITING_ACTION
    await show_words(update, context)


async def delete_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word_text = update.message.text

    if word_text == 'Отмена':
        await update.message.reply_text("Удаление слова отменено.")
        context.user_data['state'] = STATE_AWAITING_ACTION
        await show_words(update, context)
        return

    match = re.match(r'^([a-zA-Z\s]+)\s*-\s*([а-яА-ЯёЁ\s]+)$', word_text)

    if not match:
        await update.message.reply_text("Ошибка формата. Пожалуйста, выберите слово из списка.")
        context.user_data['state'] = STATE_AWAITING_ACTION
        await show_words(update, context)
        return

    en_word = match.group(1).strip().lower()

    success = db.delete_personal_word(update.effective_user.id, en_word)

    if success:
        await update.message.reply_text(f"🗑️ Слово '{en_word}' удалено из вашего словаря.")
    else:
        await update.message.reply_text("⚠️ Слово не найдено или произошла ошибка при удалении.")

    context.user_data['state'] = STATE_AWAITING_ACTION
    await show_words(update, context)


async def show_personal_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    personal_words = db.get_personal_words(update.effective_user.id)

    if not personal_words:
        await update.message.reply_text("Ваш персональный словарь пуст.")
    else:
        message = "📚 Ваш персональный словарь:\n\n"
        for i, (en_word, ru_word) in enumerate(personal_words, 1):
            message += f"{i}. {en_word} - {ru_word}\n"

        await update.message.reply_text(message)

    keyboard = [['Продолжить тренировку', 'Добавить слово', 'Удалить слово']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def dictionary_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.message.text

    if action == 'Продолжить тренировку':
        context.user_data['state'] = STATE_AWAITING_ACTION
        await show_words(update, context)
    elif action == 'Добавить слово':
        context.user_data['state'] = STATE_ADDING_WORD
        await update.message.reply_text("Введите новое слово в формате: английское слово - русский перевод")
    elif action == 'Удалить слово':
        context.user_data['state'] = STATE_DELETING_WORD
        await prepare_delete_word(update, context)


async def send_message(update: Update, text: str, reply_markup=None):
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Произошла ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка, попробуйте позже")


def main():
    app = ApplicationBuilder().token("token").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    app.run_polling()


if __name__ == '__main__':
    main()
