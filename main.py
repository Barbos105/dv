import telebot
from telebot import types
import sqlite3
import random
import time
from datetime import datetime, timedelta

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
BOT_TOKEN = '8183538061:AAHaQmTPa85qlbHkcIuNcygwkOzP8jBgaMs'

bot = telebot.TeleBot(BOT_TOKEN)

# --- Работа с базой данных SQLite ---
DATABASE_NAME = 'registration_data.db'  # Имя файла базы данных


def create_table():
    """Создает таблицы users, registration_states, likes, matches, если они не существуют."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        interests TEXT,
        about_me TEXT,
        username TEXT  -- Новое поле для username
    )
    """)

    # Таблица для хранения промежуточных данных регистрации
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registration_states (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age TEXT,
        gender TEXT,
        interests TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    # Таблица для хранения лайков
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        liker_id INTEGER,
        likee_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (liker_id, likee_id),
        FOREIGN KEY (liker_id) REFERENCES users(user_id),
        FOREIGN KEY (likee_id) REFERENCES users(user_id)
    )
    """)

    # Таблица для хранения совпадений
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        user_id1 INTEGER,
        user_id2 INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id1, user_id2),
        FOREIGN KEY (user_id1) REFERENCES users(user_id),
        FOREIGN KEY (user_id2) REFERENCES users(user_id)
    )
    """)

    conn.commit()
    conn.close()


def save_user_data(user_id, name, age, gender, interests, about_me, username=None):
    """Сохраняет данные пользователя в базу данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, name, age, gender, interests, about_me, username) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, name, age, gender, interests, about_me, username))
    conn.commit()
    conn.close()


def get_user_data(user_id):
    """Получает данные пользователя из базы данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, age, gender, interests, about_me, username FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return {'name': data[0], 'age': data[1], 'gender': data[2], 'interests': data[3], 'about_me': data[4],
                'username': data[5]}
    else:
        return None


def save_registration_state(user_id, name=None, age=None, gender=None, interests=None):
    """Сохраняет промежуточное состояние регистрации в базу данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    if name is not None:
        cursor.execute("INSERT OR REPLACE INTO registration_states (user_id, name) VALUES (?, ?)", (user_id, name))
    if age is not None:
        cursor.execute("UPDATE registration_states SET age = ? WHERE user_id = ?", (age, user_id))
    if gender is not None:
        cursor.execute("UPDATE registration_states SET gender = ? WHERE user_id = ?", (gender, user_id))
    if interests is not None:
        cursor.execute("UPDATE registration_states SET interests = ? WHERE user_id = ?", (interests, user_id))

    conn.commit()
    conn.close()


def get_registration_state(user_id):
    """Получает промежуточное состояние регистрации из базы данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, age, gender, interests FROM registration_states WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return {'name': data[0], 'age': data[1], 'gender': data[2], 'interests': data[3]}
    else:
        return {}  # Возвращаем пустой словарь, если нет записи


def clear_registration_state(user_id):
    """Удаляет промежуточное состояние регистрации из базу данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registration_states WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_available_users(user_id, gender):
    """Получает всех пользователей определенного пола, исключая себя."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Исключаем себя из поиска
    query = "SELECT user_id, name, age, interests, about_me, username FROM users WHERE gender = ? AND user_id != ?"
    cursor.execute(query, (gender, user_id))
    users = cursor.fetchall()
    conn.close()

    available_users = [
        {
            'user_id': user[0],
            'name': user[1],
            'age': user[2],
            'interests': user[3],
            'about_me': user[4],
            'username': user[5]  # Добавляем username
        }
        for user in users
    ]

    random.shuffle(available_users)  # Перемешиваем список пользователей
    return available_users


def save_like(liker_id, likee_id):
    """Сохраняет информацию о лайке в базу данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO likes (liker_id, likee_id) VALUES (?, ?)", (liker_id, likee_id))
        conn.commit()
        print(f"User {liker_id} liked user {likee_id}")
    except sqlite3.IntegrityError:
        print(f"User {liker_id} already liked user {likee_id}")
    finally:
        conn.close()


def check_match(user_id1, user_id2):
    """Проверяет, есть ли взаимный лайк между пользователями."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM likes WHERE liker_id = ? AND likee_id = ?", (user_id1, user_id2))
    like1 = cursor.fetchone()
    cursor.execute("SELECT 1 FROM likes WHERE liker_id = ? AND likee_id = ?", (user_id2, user_id1))
    like2 = cursor.fetchone()
    conn.close()
    return like1 and like2


def save_match(user_id1, user_id2):
    """Сохраняет информацию о взаимном лайке (матче) в базе данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO matches (user_id1, user_id2) VALUES (?, ?)", (user_id1, user_id2))
        conn.commit()
        print(f"Match saved between user {user_id1} and user {user_id2}")
    except sqlite3.IntegrityError:
        print(f"Match already saved between user {user_id1} and user {user_id2}")
    finally:
        conn.close()


def get_liked_by(user_id):
    """Получает список пользователей, которые поставили лайк данному пользователю."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT liker_id FROM likes WHERE likee_id = ?", (user_id,))
    liked_by = [row[0] for row in cursor.fetchall()]
    conn.close()
    return liked_by


def main_buttons_menu():
        btn_search = types.KeyboardButton("🔍Поиск🔍")
        btn_likes = types.KeyboardButton("💘Кто меня лайкнул💘")  # Новая кнопка
        btn_edit_profile = types.KeyboardButton("👤Изменить профиль👤")  # Новая кнопка
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(btn_search, btn_likes, btn_edit_profile)
    return markup

# --- Обработчики команд ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение и инструкция."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_register = types.KeyboardButton("Регистрация")
    markup.add(btn_register)
    bot.reply_to(message, """
🤗 Привет! Добро пожаловать в бота для знакомств школы 1518!
Здесь ты сможешь найти себе людей для общения, совместного время препровождения,
а может и нечто большее.. В любом случае желаю удачи! 🤗
    """, reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Регистрация")
def register_start(message):
    """Начинает процесс регистрации."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if existing_data:
        bot.reply_to(message, "Вы уже зарегистрированы.")
        # Как только зарегистрировались - добавляется кнопка поиска и кнопка с лайками
        markup = main_buttons_menu()
        bot.send_message(message.chat.id, "Теперь вы можете начать поиск", reply_markup=markup)
        return

    bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя:")
    bot.register_next_step_handler(message, process_name)


@bot.message_handler(func=lambda message: message.text == "Поиск")
def search_command(message):
    """Запускает процесс поиска пользователей по полу."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь.")
        return

    # Отправляем клавиатуру с кнопками выбора пола
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('М', 'Ж')
    bot.send_message(message.chat.id, "Кого вы ищете?", reply_markup=markup)
    bot.register_next_step_handler(message, process_search_gender)


@bot.message_handler(func=lambda message: message.text == "Кто меня лайкнул")
def show_likers(message):
    """Показывает пользователей, которые лайкнули данного пользователя."""
    user_id = message.from_user.id
    likers = get_liked_by(user_id)

    if likers:
        # Сохраняем список лайкнувших в user_data
        bot.user_data[user_id] = {
            'likers': likers,
            'current_index': 0
        }
        show_liker_profile(message, user_id)  # Показываем профиль первого лайкнувшего
    else:
        bot.send_message(message.chat.id, "Пока что вами никто не заинтересовался.")


def show_liker_profile(message, user_id):
    """Показывает профиль лайкнувшего пользователя с кнопками Лайк и Дизлайк."""
    user_data = bot.user_data.get(user_id)
    if not user_data or 'likers' not in user_data:
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    likers = user_data['likers']
    current_index = user_data.get('current_index', 0)

    if current_index < len(likers):
        liker_id = likers[current_index]
        liker_data = get_user_data(liker_id)

        if liker_data:
            markup = types.InlineKeyboardMarkup()
            btn_like = types.InlineKeyboardButton("❤️ Лайк", callback_data=f"like_liker:{liker_id}")
            btn_dislike = types.InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike_liker:{liker_id}")
            markup.add(btn_like, btn_dislike)

            # Показываем профиль лайкнувшего
            bot.send_message(message.chat.id,
                             f"Пользователь {liker_data['name']} (Возраст: {liker_data['age']}) лайкнул вас.\n"
                             f"Интересы: {liker_data['interests']}\n"
                             f"О себе: {liker_data['about_me']}",
                             reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Данные пользователя недоступны.")
    else:
        bot.send_message(message.chat.id, "Больше нет пользователей, которые вас лайкнули.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('like_liker:'))
def like_liker_callback(call):
    """Обрабатывает нажатие кнопки "Лайк" на профиле лайкнувшего."""
    try:
        user_id = call.from_user.id
        liker_id = int(call.data.split(':')[1])

        # Удаляем сообщение бота
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        # Удаляем лайк из базы данных
        remove_like(liker_id, user_id)

        # Показываем username лайкнувшего
        liker_data = get_user_data(liker_id)
        if liker_data:
            username_text = f"@{liker_data['username']}" if liker_data.get('username') else "Нет username"
            bot.send_message(user_id,
                             f"Вы поставили лайк пользователю {liker_data['name']}. Его username: {username_text}")

        # Переходим к следующему лайкнувшему
        show_next_liker(call.message, user_id)

    except Exception as e:
        print(f"Ошибка в like_liker_callback: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('dislike_liker:'))
def dislike_liker_callback(call):
    """Обрабатывает нажатие кнопки "Дизлайк" на профиле лайкнувшего."""
    try:
        user_id = call.from_user.id
        liker_id = int(call.data.split(':')[1])

        # Удаляем сообщение бота
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        # Удаляем лайк из базы данных
        remove_like(liker_id, user_id)

        # Переходим к следующему лайкнувшему
        show_next_liker(call.message, user_id)

    except Exception as e:
        print(f"Ошибка в dislike_liker_callback: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")


def remove_like(liker_id, likee_id):
    """Удаляет лайк из базы данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM likes WHERE liker_id = ? AND likee_id = ?", (liker_id, likee_id))
    conn.commit()
    conn.close()


def show_next_liker(message, user_id):
    """Переходит к следующему лайкнувшему пользователю."""
    user_data = bot.user_data.get(user_id)
    if not user_data or 'likers' not in user_data:
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    likers = user_data['likers']
    current_index = user_data.get('current_index', 0)

    if current_index + 1 < len(likers):
        user_data['current_index'] = current_index + 1
        show_liker_profile(message, user_id)  # Показываем следующего лайкнувшего
    else:
        bot.send_message(message.chat.id, "Больше нет пользователей, которые вас лайкнули.")
        del bot.user_data[user_id]  # Очищаем данные


@bot.message_handler(func=lambda message: message.text == "Изменить профиль")
def edit_profile(message):
    """Начинает процесс изменения профиля."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь.")
        return

    bot.send_message(message.chat.id, "Введите новое имя:")
    bot.register_next_step_handler(message, process_edit_name)


def process_edit_name(message):

    """Сохраняет новое имя пользователя и переходит к запросу возраста."""
    try:
        user_id = message.from_user.id
        name = message.text
        if name:
            save_registration_state(user_id, name=name)  # Сохраняем имя в базе данных
            bot.send_message(message.chat.id, "Спасибо! Теперь введите ваш возраст:")
            bot.register_next_step_handler(message, process_edit_age)
        else:
            bot.register_next_step_handler(message, process_edit_name)

            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести имя')
    except Exception as e:
        print(f"Ошибка в process_edit_name: {e}")
        bot.reply_to(message, "Произошла ошибка. Пожалуйста, введите имя.")
        bot.register_next_step_handler(message, process_edit_name)


def process_edit_age(message):
    """Сохраняет новый возраст пользователя и переходит к запросу пола."""
    try:
        user_id = message.from_user.id
        age = message.text
        if age:
            age = int(message.text)
            if age < 7 or age > 105:
                bot.reply_to(message, "Пожалуйста, введите корректный возраст (от 7 до 105).")
                bot.register_next_step_handler(message, process_edit_age)
                return
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('М', 'Ж')
            bot.send_message(message.chat.id, "Какой у вас пол?", reply_markup=markup)
            bot.register_next_step_handler(message, process_edit_gender)

            save_registration_state(user_id, age=age)  # Сохраняем возраст в базе данных
        else:
            bot.register_next_step_handler(message, process_edit_age)
            bot.reply_to(message, "Пожалуйста, введите возраст цифрами.")

    except Exception as e:
        print(f"Ошибка в process_edit_age: {e}")
        bot.reply_to(message, "Произошла ошибка. Пожалуйста, введите возраст цифрами.")
        bot.register_next_step_handler(message, process_edit_age)


def process_edit_gender(message):
    """Сохраняет новый пол пользователя и переходит к запросу интересов."""
    try:
        user_id = message.from_user.id
        gender = message.text

        # Проверка на допустимые варианты пола

        if gender:
            if gender not in ['М', 'Ж']:
                bot.reply_to(message, "Пожалуйста, выберите пол из предложенных вариантов.")
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add('М', 'Ж')
                bot.send_message(message.chat.id, "Какой у вас пол?", reply_markup=markup)
                bot.register_next_step_handler(message, process_edit_gender)
                return
            else:

                save_registration_state(user_id, gender=gender)

                bot.send_message(message.chat.id, "Расскажите о своих интересах (в нескольких словах):")
                bot.register_next_step_handler(message, process_edit_interests)
        else:
            bot.register_next_step_handler(message, process_edit_gender)

            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, нажмите на одну из кнопок')
    except Exception as e:
        print(f"Ошибка в process_edit_gender: {e}")
        bot.reply_to(message, "Произошла ошибка. Пожалуйста, нажмите на одну из кнопок")
        bot.register_next_step_handler(message, process_edit_gender)


def process_edit_interests(message):
    """Сохраняет новые интересы пользователя и переходит к запросу 'о себе'."""
    try:
        user_id = message.from_user.id
        interests = message.text
        if interests:
            save_registration_state(user_id, interests=interests)

            bot.send_message(message.chat.id, "Напишите немного о себе:")
            bot.register_next_step_handler(message, process_edit_about_me)
        else:
            bot.register_next_step_handler(message, process_edit_interests)

            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')
    except Exception as e:
        print(f"Ошибка в process_edit_interests: {e}")
        bot.reply_to(message, "Произошла ошибка. Пожалуйста, введите свои интересы еще раз.")
        bot.register_next_step_handler(message, process_edit_interests)


def process_edit_about_me(message):
    """Сохраняет новое 'о себе' пользователя и завершает изменение профиля."""
    try:
        user_id = message.from_user.id
        about_me = message.text
        if about_me:
            registration_state = get_registration_state(user_id)
            name = registration_state.get('name')
            age = registration_state.get('age')
            gender = registration_state.get('gender')
            interests = registration_state.get('interests')

            # Получаем username пользователя
            username = message.from_user.username

            save_user_data(user_id, name, age, gender, interests, about_me, username)  # Сохраняем в таблицу users
            clear_registration_state(user_id)  # Удаляем промежуточные данные
            # После регистрации добавляем кнопку поиска и кнопку "Кто меня лайкнул"
            markup = main_buttons_menu()
            bot.send_message(message.chat.id, "Ваш профиль успешно обновлен.", reply_markup=markup)

        else:
            bot.register_next_step_handler(message, process_edit_about_me)
            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')

    except Exception as e:
        print(f"Ошибка в process_edit_about_me: {e}")
        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз рассказать о себе')

        bot.register_next_step_handler(message, process_edit_about_me)


# --- Остальные функции и обработчики ---

def go_back_to_main_menu(message):
    """Возвращает пользователя в главное меню."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)

    if existing_data:  # Пользователь зарегистрирован
        markup = main_buttons_menu()
        bot.send_message(message.chat.id, "Возвращаемся в главное меню.", reply_markup=markup)
    else:  # Пользователь не зарегистрирован
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("Регистрация")
        markup.add(btn_register)
        bot.send_message(message.chat.id, "Пожалуйста, зарегистрируйтесь.", reply_markup=markup)


def process_search_gender(message):
    """Сохраняет выбранный пол для поиска и начинает показ пользователей."""
    try:
        gender = message.text
        if gender not in ['М', 'Ж']:
            bot.reply_to(message, "Пожалуйста, выберите пол из предложенных вариантов.")
            bot.register_next_step_handler(message, process_search_gender)  # Повторяем запрос пола
            return

        user_id = message.from_user.id
        available_users = get_available_users(user_id, gender)

        if available_users:
            # Инициализируем список пользователей для текущего пользователя
            bot.user_data[user_id] = {
                'gender': gender,
                'users': available_users,
                'current_index': 0,
                'last_message_id': None  # Добавляем поле для хранения ID последнего сообщения
            }

            # Убираем клавиатуру с кнопками выбора пола
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, "Принято, начинаю поиск...", reply_markup=markup)
            show_user(message, user_id)

        else:
            # Если пользователей не найдено, возвращаемся в главное меню
            bot.send_message(message.chat.id,
                             "К сожалению, больше пользователей с такими параметрами не найдено. Возвращаемся в главное меню.")
            go_back_to_main_menu(message)  # Используем функцию для возврата в главное меню

    except Exception as e:
        print(f"Ошибка в process_search_gender: {e}")
        bot.reply_to(message, 'Произошла ошибка при поиске. Подождите пока в боте появятся люди этого пола')


def show_user(message, user_id):
    """Показывает информацию о пользователе."""
    user_data = bot.user_data.get(user_id)
    if not user_data:
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, начните поиск заново.")
        return

    users = user_data['users']
    current_index = user_data['current_index']

    # Зацикливание поиска
    if not users:
        bot.send_message(message.chat.id, "К сожалению, больше пользователей не найдено. Начинаем заново.")
        gender = user_data['gender']  # Получаем пол из user_data
        users = get_available_users(user_id, gender)  # Получаем новый список
        user_data['users'] = users
        user_data['current_index'] = 0
        current_index = 0  # Reset index

    if current_index < len(users):
        user = users[current_index]
        markup = types.InlineKeyboardMarkup()
        btn_like = types.InlineKeyboardButton("❤️", callback_data=f"like:{user['user_id']}")
        btn_dislike = types.InlineKeyboardButton("👎", callback_data=f"dislike:{user['user_id']}")
        btn_back_to_menu = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")  # Кнопка "Назад в меню"
        markup.add(btn_like, btn_dislike, btn_back_to_menu)  # Добавляем кнопку в markup

        sent_message = bot.send_message(message.chat.id, "Нашел вот кого:\n"
                                                         f"Имя: {user['name']}\n"
                                                         f"Возраст: {user['age']}\n"
                                                         f"Интересы: {user['interests']}\n"
                                                         f"О себе: {user['about_me']}\n",
                                        reply_markup=markup)

        # Сохраняем ID последнего сообщения
        user_data['last_message_id'] = sent_message.message_id
        bot.user_data[user_id] = user_data  # Обновляем данные пользователя
    else:  # Этот блок больше не должен вызываться
        bot.send_message(message.chat.id, "К сожалению, больше пользователей не найдено. Начинаем заново.")
        gender = user_data['gender']  # Получаем пол из user_data
        users = get_available_users(user_id, gender)  # Получаем новый список
        user_data['users'] = users
        user_data['current_index'] = 0
        show_user(message, user_id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu_callback(call):
    """Обработчик для кнопки "Назад в меню"."""
    try:
        # Удаляем сообщение бота
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Вместо прямого вызова go_back_to_main_menu, отправляем новое сообщение с нужной клавиатурой:
    user_id = call.from_user.id
    existing_data = get_user_data(user_id)

    if existing_data:  # Пользователь зарегистрирован
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_search = types.KeyboardButton("Поиск")
        btn_likes = types.KeyboardButton("Кто меня лайкнул")
        btn_edit_profile = types.KeyboardButton("Изменить профиль")  # Новая кнопка
        markup.add(btn_search, btn_likes, btn_edit_profile)
        bot.send_message(call.message.chat.id, "Что дальше?", reply_markup=markup)  # Отправляем сообщение с клавиатурой
    else:  # Пользователь не зарегистрирован (логически это вряд ли произойдет, но лучше обработать)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("Регистрация")
        markup.add(btn_register)
        bot.send_message(call.message.chat.id, "Пожалуйста, зарегистрируйтесь.", reply_markup=markup)

    # Очищаем данные поиска
    if user_id in bot.user_data:
        del bot.user_data[user_id]

    bot.answer_callback_query(call.id, "Возвращаемся...")


@bot.callback_query_handler(func=lambda call: call.data.startswith('dislike:'))
def dislike_callback(call):
    """Обрабатывает нажатие кнопки "Дизлайк", удаляет пользователя из списка и показывает следующего."""
    try:
        # Удаляем сообщение бота
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    user_id = call.from_user.id
    disliked_user_id = call.data.split(':')[1]  # Получаем id пользователя, которого дизлайкнули

    user_data = bot.user_data.get(user_id)
    if user_data:
        users = user_data['users']
        current_index = user_data['current_index']

        # Удаляем дизлайкнутого пользователя из списка
        if users and current_index < len(users):
            del users[current_index]  # Удаляем элемент на текущем индексе

            user_data['users'] = users  # Обновляем список пользователей
            bot.user_data[user_id] = user_data  # Обновляем данные пользователя

        bot.answer_callback_query(call.id, "Удаляем пользователя и ищем следующего...")
        show_next_user(call.message, user_id)  # Показываем следующего
    else:
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, начните поиск заново.")


def show_next_user(message, user_id):
    """Показывает следующего пользователя, обеспечивая зацикленный поиск."""
    user_data = bot.user_data.get(user_id)
    if user_data:
        users = user_data['users']
        if users:  # Проверка, что список не пуст
            # Переходим к следующему индексу
            user_data['current_index'] = (user_data['current_index'] + 1) % len(users)  # Инкрементируем индекс
            bot.user_data[user_id] = user_data  # Обновляем данные пользователя
            show_user(message, user_id)
        else:
            # Если список пуст, получаем новый список и показываем первого
            user_data['users'] = get_available_users(user_id, user_data['gender'])  # Получаем новый список
            if user_data['users']:
                user_data['current_index'] = 0
                bot.user_data[user_id] = user_data  # Обновляем данные пользователя
                show_user(message, user_id)
            else:
                bot.send_message(message.chat.id, "К сожалению, больше нет доступных пользователей.")
                # Если новых пользователей не нашлось, возвращаемся в главное меню
                go_back_to_main_menu(message)
    else:
        bot.send_message(message.chat.id, "Произошла ошибка. Начните поиск заново.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('like:'))
def like_callback(call):
    """Обрабатывает нажатие кнопки "Лайк"."""
    try:
        # Удаляем сообщение бота
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    user_id = call.from_user.id
    likee_id = int(call.data.split(':')[1])

    save_like(user_id, likee_id)  # Сохраняем лайк в базе данных

    if check_match(user_id, likee_id):  # Проверяем взаимность
        save_match(user_id, likee_id)
        # Уведомляем обоих пользователей о взаимной симпатии

        # Показываем username после мэтча
        user_data = get_user_data(likee_id)
        if user_data:
            username_text = f"@{user_data['username']}" if user_data.get('username') else "Нет username"
            bot.send_message(user_id, f"Username пользователя: {username_text}")

    bot.answer_callback_query(call.id, "Лайк поставлен")
    show_next_user(call.message, user_id)  # Показываем следующего пользователя


# --- Обработчики шагов регистрации ---

def process_name(message):
    """Сохраняет имя пользователя и переходит к запросу возраста."""
    try:
        user_id = message.from_user.id
        name = message.text
        if name:
            save_registration_state(user_id, name=name)  # Сохраняем имя в базе данных
            bot.send_message(message.chat.id, "Спасибо! Теперь введите ваш возраст:")
            bot.register_next_step_handler(message, process_age)
        else:
            bot.register_next_step_handler(message, process_name)

            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести имя')

    except Exception as e:
        print(f"Ошибка в process_name: {e}")
        bot.register_next_step_handler(message, process_name)

        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


def process_age(message):
    """Сохраняет возраст пользователя и переходит к запросу пола."""
    try:
        user_id = message.from_user.id
        age = message.text
        if age:
            age = int(message.text)
            if age < 7 or age > 105:
                bot.reply_to(message, "Пожалуйста, введите корректный возраст (от 7 до 105).")
                bot.register_next_step_handler(message, process_age)
                return
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('М', 'Ж')
            bot.send_message(message.chat.id, "Какой у вас пол?", reply_markup=markup)
            bot.register_next_step_handler(message, process_gender)

            save_registration_state(user_id, age=age)  # Сохраняем возраст в базе данных
        else:
            bot.register_next_step_handler(message, process_age)
            bot.reply_to(message, "Пожалуйста, введите возраст цифрами.")

    except Exception as e:
        print(f"Ошибка в process_age: {e}")
        bot.register_next_step_handler(message, process_age)
        bot.reply_to(message, "Пожалуйста, введите возраст цифрами.")


def process_gender(message):
    """Сохраняет пол пользователя и переходит к запросу интересов."""
    try:
        user_id = message.from_user.id
        gender = message.text

        # Проверка на допустимые варианты пола

        if gender:
            if gender not in ['М', 'Ж']:
                bot.reply_to(message, "Пожалуйста, выберите пол из предложенных вариантов.")
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add('М', 'Ж')
                bot.send_message(message.chat.id, "Какой у вас пол?", reply_markup=markup)
                bot.register_next_step_handler(message, process_gender)
                return
            else:

                save_registration_state(user_id, gender=gender)

                bot.send_message(message.chat.id, "Расскажите о своих интересах (в нескольких словах):")
                bot.register_next_step_handler(message, process_interests)
        else:
            bot.register_next_step_handler(message, process_gender)

            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, нажмите на одну из кнопок')
    except Exception as e:
        print(f"Ошибка в process_gender: {e}")
        bot.register_next_step_handler(message, process_gender)

        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, нажмите на одну из кнопок')


def process_interests(message):
    """Сохраняет интересы пользователя и переходит к запросу 'о себе'."""
    try:
        user_id = message.from_user.id
        interests = message.text
        if interests:
            save_registration_state(user_id, interests=interests)

            bot.send_message(message.chat.id, "Напишите немного о себе:")
            bot.register_next_step_handler(message, process_about_me)
        else:
            bot.register_next_step_handler(message, process_interests)

            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')
    except Exception as e:
        print(f"Ошибка в process_interests: {e}")
        bot.register_next_step_handler(message, process_interests)

        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


def process_about_me(message):
    """Сохраняет 'о себе' пользователя и завершает регистрацию."""
    try:
        user_id = message.from_user.id
        about_me = message.text
        if about_me:
            registration_state = get_registration_state(user_id)
            name = registration_state.get('name')
            age = registration_state.get('age')
            gender = registration_state.get('gender')
            interests = registration_state.get('interests')

            # Получаем username пользователя
            username = message.from_user.username

            save_user_data(user_id, name, age, gender, interests, about_me, username)  # Сохраняем в таблицу users
            clear_registration_state(user_id)  # Удаляем промежуточные данные
            # После регистрации добавляем кнопку поиска и кнопку "Кто меня лайкнул"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn_search = types.KeyboardButton("Поиск")
            btn_likes = types.KeyboardButton("Кто меня лайкнул")
            btn_edit_profile = types.KeyboardButton("Изменить профиль")  # Новая кнопка
            markup.add(btn_search, btn_likes, btn_edit_profile)
            bot.send_message(message.chat.id, "Спасибо за регистрацию! Теперь вы можете начать поиск",
                             reply_markup=markup)

        else:
            bot.register_next_step_handler(message, process_about_me)
            bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')
    except Exception as e:
        print(f"Ошибка в process_about_me: {e}")
        bot.register_next_step_handler(message, process_about_me)
        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


# --- Запуск бота ---
if __name__ == '__main__':
    bot.user_data = {}  # Инициализируем хранилище данных
    create_table()  # Создаем таблицы при запуске бота

    print("Бот запущен...")
    bot.infinity_polling()
