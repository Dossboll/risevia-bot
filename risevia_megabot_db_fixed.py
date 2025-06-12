
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import random
import sqlite3
import json
import os

TOKEN = "8080949850:AAFWpIMJAzOCc6XifshXVaNgFsdZwFwIIQg"
bot = telebot.TeleBot(TOKEN)

# === Задания ===
brain_tasks = [
    "🔢 Назови числа от 100 до 1 с шагом -7",
    "🧠 Вспомни и запиши 10 вещей, которые ты видишь вокруг",
    "📷 Представь свой завтрак. Что ты ел 3 дня назад?",
    "💭 Закрой глаза и постарайся вспомнить всё, что ты делал вчера после 16:00",
    "🔡 Назови 10 слов на букву 'П'"
]

discipline_tasks = [
    "⏰ Проснись на 30 минут раньше обычного",
    "📴 Не заходи в соцсети до 12:00",
    "🚿 Прими холодный душ",
    "📓 Напиши 3 цели на день",
    "🍎 Съешь что-то полезное вместо сладкого"
]

books = [
    ("«Атомные привычки»", "Выбери 1 привычку, которую хочешь внедрить, и начни с малого."),
    ("«Психология влияния»", "Наблюдай сегодня, как на тебя влияют другие — реклама, друзья, соцсети."),
    ("«Думай медленно — решай быстро»", "Замечай, когда ты принимаешь решение на автомате."),
    ("«Богатый папа, бедный папа»", "Подумай, чему ты хочешь научиться о деньгах в ближайший месяц.")
]

coach_questions = [
    "💬 Какая цель для тебя сейчас самая важная?",
    "💬 Что мешает тебе двигаться вперёд?",
    "💬 Назови один шаг, который ты можешь сделать сегодня?",
    "💬 Как бы ты чувствовал себя, если бы уже достиг цели?",
    "💬 Кто тебя поддерживает, когда трудно?"
]

cat_quotes = [
    "🐱 Иногда, чтобы найти путь, нужно хорошенько выспаться.",
    "🐱 Ты не опаздываешь. Ты просто ещё не проснулся как личность.",
    "🐱 Сначала поешь, потом спасай мир.",
    "🐱 Если всё бесит — шипи. Или игнорируй.",
    "🐱 Не все дороги ведут к смыслу. Но все ведут к опыту."
]

# === Уровни по баллам ===
def get_level(score):
    if score >= 20:
        return "🧠 Гуру Risevia"
    elif score >= 10:
        return "💡 Мастер дисциплины"
    elif score >= 5:
        return "🚀 В пути"
    else:
        return "🌱 Новичок"

# === Создание БД ===
DB_FILE = "risevia.db"
if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE users (
        chat_id INTEGER PRIMARY KEY,
        score INTEGER DEFAULT 0,
        used_tasks TEXT DEFAULT '{}'
    )""")
    conn.commit()
    conn.close()

# === Работа с БД ===
def get_user(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT score, used_tasks FROM users WHERE chat_id=?", (chat_id,))
    row = c.fetchone()
    if row:
        score, used = row
        used = json.loads(used)
    else:
        score = 0
        used = {"brain": [], "discipline": [], "books": [], "coach": [], "cat": []}
        c.execute("INSERT INTO users (chat_id, score, used_tasks) VALUES (?, ?, ?)",
                  (chat_id, score, json.dumps(used)))
        conn.commit()
    conn.close()
    return score, used

def update_user(chat_id, score, used):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET score=?, used_tasks=? WHERE chat_id=?",
              (score, json.dumps(used), chat_id))
    conn.commit()
    conn.close()

# === Главное меню ===
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("🧠 Прокачать мозг"),
    KeyboardButton("🎯 Дисциплина"),
    KeyboardButton("💬 Наставник"),
)
main_menu.add(
    KeyboardButton("📚 Книга дня"),
    KeyboardButton("😌 Настроение"),
    KeyboardButton("🐱 Кот-Сенсей")
)

# === /start ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    score, used = get_user(chat_id)
    level = get_level(score)
    bot.send_message(chat_id, f"👋 Привет! Я Risevia MegaBot.\nТы — {level} (баллы: {score})", reply_markup=main_menu)

# === /score ===
@bot.message_handler(commands=["score"])
def show_score(message):
    chat_id = message.chat.id
    score, _ = get_user(chat_id)
    bot.send_message(chat_id, f"🏆 У тебя {score} баллов! Уровень: {get_level(score)}")

# === Получение уникального задания ===
def get_unique_task(chat_id, category, pool):
    score, used = get_user(chat_id)
    used_ids = set(used.get(category, []))
    available = [i for i in range(len(pool)) if i not in used_ids]
    if not available:
        return None, score, used
    i = random.choice(available)
    used[category].append(i)
    score += 1
    update_user(chat_id, score, used)
    return pool[i], score, used

# === Обработка всех режимов ===
@bot.message_handler(func=lambda message: True)
def handle_mode(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🧠 Прокачать мозг":
        task, score, _ = get_unique_task(chat_id, "brain", brain_tasks)
        bot.send_message(chat_id, f"🧩 Твое задание:\n\n{task}" if task else "🎉 Все задания пройдены!")
    elif text == "🎯 Дисциплина":
        task, score, _ = get_unique_task(chat_id, "discipline", discipline_tasks)
        bot.send_message(chat_id, f"🔥 Задание дня:\n\n{task}" if task else "🎉 Все задания пройдены!")
    elif text == "📚 Книга дня":
        task, score, _ = get_unique_task(chat_id, "books", books)
        if task:
            book, action = task
            bot.send_message(chat_id, f"📚 {book}\n📌 Задание: {action}")
        else:
            bot.send_message(chat_id, "📖 Ты прочёл всё! Жди новинки.")
    elif text == "💬 Наставник":
        task, score, _ = get_unique_task(chat_id, "coach", coach_questions)
        bot.send_message(chat_id, task if task else "🧘 Все вопросы заданы.")
    elif text == "🐱 Кот-Сенсей":
        task, score, _ = get_unique_task(chat_id, "cat", cat_quotes)
        bot.send_message(chat_id, task if task else "🐾 Кот больше молчит.")
    elif text == "😌 Настроение":
        bot.send_message(chat_id, "😌 Сделай глубокий вдох. Как ты сейчас?")

# === Запуск ===
print("Risevia MegaBot (с базой и уровнями) запущен!")
bot.infinity_polling()
