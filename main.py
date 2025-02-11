import random

import telebot
from telebot.types import ReplyKeyboardRemove
from telebot import types
from db import *
import os

BOT_TOKEN = open('token.txt').readline()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='MARKDOWN')


def main_buttons_menu():
    btn_search = types.KeyboardButton("🔍 Поиск 🔍")
    btn_likes = types.KeyboardButton("💘 Кто меня лайкнул 💘")
    btn_edit_profile = types.KeyboardButton("👤 Изменить профиль 👤")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(btn_search, btn_likes, btn_edit_profile)
    return markup


def gender_menu(searching: bool, age: int):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    if searching:
        if age > 12:
            markup.add('Парней', 'Парней и Девушек', 'Девушек')
        else:
            markup.add('Мальчиков', 'Мальчиков и Девочек', 'Девочек')
    else:
        if age > 12:
            markup.add('👱‍♂️ Парень', '👱‍♀️ Девушка')
        else:
            markup.add('👦 Мальчик', '👧 Девочка')
    return  markup


def location_menu(searching: bool,):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('проспект', 'цандера')
    return  markup

# --- Обработчики команд ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение и инструкция."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if existing_data:
        print(2)
        bot.reply_to(message, "Вы уже зарегистрированы.")
        markup = main_buttons_menu()
        bot.send_message(message.chat.id, "Теперь вы можете начать поиск", reply_markup=markup)
    else:
        print(1)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("Регистрация")
        markup.add(btn_register)
        bot.reply_to(message, """
        🤗 Привет! Добро пожаловать в бота для знакомств школы 1518!
        Здесь ты сможешь найти себе людей для общения, совместного время препровождения,
        а может и нечто большее.. В любом случае желаю удачи! 🤗
            """, reply_markup=markup)


@bot.message_handler(func=lambda message: "регистрация" in message.text.lower())
def register_start(message):
    """Начинает процесс регистрации."""
    bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя:", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_name)


@bot.message_handler(func=lambda message: "поиск" in message.text.lower())
def search_command(message):
    """Запускает процесс поиска пользователей по полу."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь 🙏")
        return

    markup = gender_menu(searching=True, age=13)
    bot.send_message(message.chat.id, "Кого вы ищете?", reply_markup=markup)
    bot.register_next_step_handler(message, process_search_gender)


@bot.message_handler(func=lambda message: "кто меня лайкнул" in message.text.lower())
def show_likers(message):
    """Показывает пользователей, которые лайкнули данного пользователя."""
    user_id = message.from_user.id
    likers = get_liked_by(user_id)

    if likers:
        bot.user_search_data[user_id] = {
            'likers': likers,
            'current_index': 0
        }
        show_liker_profile(message, user_id)
    else:
        bot.send_message(message.chat.id, "Пока что вами никто не заинтересовался.")


def show_liker_profile(message, user_id):
    """Показывает профиль лайкнувшего пользователя с кнопками Лайк и Дизлайк."""
    user_search_data = bot.user_search_data.get(user_id)
    if not user_search_data or 'likers' not in user_search_data:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    likers = user_search_data['likers']
    current_index = user_search_data.get('current_index', 0)

    if current_index < len(likers):
        liker_id = likers[current_index]
        liker_data = get_user_data(liker_id)

        if liker_data:
            markup = types.InlineKeyboardMarkup()
            btn_like = types.InlineKeyboardButton("❤️ Лайк", callback_data=f"like_liker:{liker_id}")
            btn_dislike = types.InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike_liker:{liker_id}")
            markup.add(btn_like, btn_dislike)
            text = (f"Вы понравились:\n\n<b>{liker_data['name']}</b><i>, {liker_data['age']} лет.</i> Интересы: {liker_data['interests']}."
                    f"\n{liker_data['about_me']}")
            bot.send_photo(message.chat.id, photo=open(f'images/image{liker_data["user_id"]}.jpg', 'rb'),
                                          caption=text, reply_markup=markup, parse_mode='HTML')

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

        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        remove_like(liker_id, user_id)

        liker_data = get_user_data(liker_id)
        user_data = get_user_data(user_id)
        if liker_data:
            user_ping = f"@{user_data['username']}" if user_data.get('username') else "{ошибка получения лс}"
            bot.send_message(liker_id,f"🤩 Взаимная симпатия с {user_data['name']}!\n Начинай общаться {user_ping}")
            liker_ping = f"@{liker_data['username']}" if liker_data.get('username') else "{ошибка получения лс}"
            bot.send_message(user_id,f"🤩 Взаимная симпатия с {liker_data['name']}!\n Начинай общаться {liker_ping}")

        show_next_liker(call.message, user_id)

    except Exception as e:
        print(f"Ошибка в like_liker_callback: {e}")
        bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('dislike_liker:'))
def dislike_liker_callback(call):
    """Обрабатывает нажатие кнопки "Дизлайк" на профиле лайкнувшего."""
    try:
        user_id = call.from_user.id
        liker_id = int(call.data.split(':')[1])

        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        remove_like(liker_id, user_id)

        show_next_liker(call.message, user_id)

    except Exception as e:
        print(f"Ошибка в dislike_liker_callback: {e}")
        bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.")


def remove_like(liker_id, likee_id):
    """Удаляет лайк из базы данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM likes WHERE liker_id = ? AND likee_id = ?", (liker_id, likee_id))
    conn.commit()
    conn.close()


def show_next_liker(message, user_id):
    """Переходит к следующему лайкнувшему пользователю."""
    user_search_data = bot.user_search_data.get(user_id)
    if not user_search_data or 'likers' not in user_search_data:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return

    likers = user_search_data['likers']
    current_index = user_search_data.get('current_index', 0)

    if current_index + 1 < len(likers):
        user_search_data['current_index'] = current_index + 1
        show_liker_profile(message, user_id)
    else:
        bot.send_message(message.chat.id, "Больше нет пользователей, которые вас лайкнули.")
        del bot.user_search_data[user_id]


@bot.message_handler(func=lambda message: "изменить профиль" in message.text.lower())
def edit_profile(message):
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь 🙏")
        return
    bot.send_message(message.chat.id, "Ваше новое имя?", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_name)

# --- Остальные функции и обработчики ---

def go_back_to_main_menu(message):
    user_id = message.chat.id
    existing_data = get_user_data(user_id)
    if existing_data:
        markup = main_buttons_menu()
        bot.send_message(message.chat.id, "Возвращаемся в главное меню", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("Регистрация")
        markup.add(btn_register)
        bot.send_message(message.chat.id, "Пожалуйста, зарегистрируйтесь 🙏", reply_markup=markup)


def process_search_gender(message):
    """Сохраняет выбранный пол для поиска и начинает показ пользователей."""
    try:
        gender = message.text
        if gender.lower() not in ['парней', 'парней и девушек', 'девушек', 'мальчиков', 'мальчиков и девочек', 'девочек']:
            bot.reply_to(message, "⚠️ Пожалуйста, сделайте выбор из предложенных вариантов")
            bot.register_next_step_handler(message, process_search_gender)
            return

        user_id = message.from_user.id
        search_gender = ''
        if gender.lower() in ['парней', 'мальчиков']:
            available_users = get_available_users(user_id, 'М')
            search_gender = 'М'
        elif gender.lower() in ['девушек', 'девочек']:
            available_users = get_available_users(user_id, 'Ж')
            search_gender = 'Ж'
        else:
            available_users = get_available_users(user_id, 'МЖ')
            search_gender = 'МЖ'

        if available_users:
            bot.user_search_data[user_id] = {
                'gender': search_gender,
                'users': available_users,
                'last_message_id': None
            }
            markup = types.ReplyKeyboardRemove()
            bot.send_message(message.chat.id, "🔍 Принято, начинаю поиск...", reply_markup=markup)
            show_user(message, user_id)
        else:
            bot.send_message(message.chat.id,
                             "💔 К сожалению, больше пользователей с такими параметрами не найдено. Возвращаемся в главное меню.")
            go_back_to_main_menu(message)

    except Exception as e:
        print(f"Ошибка в process_search_gender: {e}")
        bot.reply_to(message, '💔 Произошла ошибка при поиске. Подождите пока в боте появятся люди этого пола')
        go_back_to_main_menu(message)


def show_user(message, user_id):
    user_search_data = bot.user_search_data.get(user_id)
    if not user_search_data:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, начните поиск заново.")
        return
    users = user_search_data['users']
    # random.shuffle(users)

    if not users:
        gender = user_search_data['gender']
        users = get_available_users(user_id, gender)
        user_search_data['users'] = users

    user = random.choice(users)
    markup = types.InlineKeyboardMarkup()
    btn_like = types.InlineKeyboardButton("❤️", callback_data=f"like:{user['user_id']}")
    btn_dislike = types.InlineKeyboardButton("👎", callback_data=f"dislike:{user['user_id']}")
    btn_back_to_menu = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
    markup.add(btn_like, btn_dislike, btn_back_to_menu)
    text = f"Нашел вот кого:\n\n<b>{user['name']}</b><i>, {user['age']} лет, {user['location']}.</i> \nИнтересы: {user['interests']}\n{user['about_me']}"
    sent_message = bot.send_photo(message.chat.id, photo=open(f'images/image{user["user_id"]}.jpg', 'rb'),
                                  caption=text, reply_markup=markup, parse_mode='HTML')

    user_search_data['last_message_id'] = sent_message.message_id
    bot.user_search_data[user_id] = user_search_data


@bot.callback_query_handler(func=lambda call: call.data.startswith('like:'))
def like_callback(call):
    """Обрабатывает нажатие кнопки "Лайк"."""
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    user_id = call.from_user.id
    likee_id = int(call.data.split(':')[1])

    bot.send_message(likee_id, '💘 Тебя кто-то лайкнул! Нажми <i>кто меня лайкнул</i>, чтобы посмотреть 👀',
                     parse_mode='HTML')

    save_like(user_id, likee_id)

    if check_match(user_id, likee_id):
        save_match(user_id, likee_id)

        user_data = get_user_data(user_id)
        liker_data = get_user_data(likee_id)
        if user_data is not None:

            user_ping = f"@{user_data['username']}" if user_data.get('username') else "{ошибка получения лс}"
            bot.send_message(likee_id,f"🤩 Взаимная симпатия с {user_data['name']}!\n Начинай общаться {user_ping}")
            liker_ping = f"@{liker_data['username']}" if liker_data.get('username') else "{ошибка получения лс}"
            bot.send_message(user_id,f"🤩 Взаимная симпатия с {liker_data['name']}!\n Начинай общаться {liker_ping}")

    bot.answer_callback_query(call.id, "Лайк поставлен")
    show_user(call.message, user_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('dislike:'))
def dislike_callback(call):
    """Обрабатывает нажатие кнопки "Дизлайк", удаляет пользователя из списка и показывает следующего."""
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    user_id = call.from_user.id
    disliked_user_id = int(call.data.split(':')[1])

    user_search_data = bot.user_search_data.get(user_id)
    if user_search_data is not None:
        users = user_search_data['users']
        index_disliked_user = [i for i in range(len(users)) if users[i]['user_id'] == disliked_user_id][0]
        del users[index_disliked_user]
        user_search_data['users'] = users
        bot.user_search_data[user_id] = user_search_data
        show_user(call.message, user_id)
    else:
        bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, начните поиск заново.")


@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu_callback(call):
    """Обработчик для кнопки "Назад в меню"."""
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    user_id = call.from_user.id
    existing_data = get_user_data(user_id)

    if existing_data:
        markup = main_buttons_menu()
        bot.send_message(call.message.chat.id, "Что дальше?", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("Регистрация")
        markup.add(btn_register)
        bot.send_message(call.message.chat.id, "Пожалуйста, зарегистрируйтесь 🙏", reply_markup=markup)

    if user_id in bot.user_search_data:
        del bot.user_search_data[user_id]

    bot.answer_callback_query(call.id, "Возвращаемся...")


# --- Обработчики шагов регистрации ---

def process_name(message):
    try:
        user_id = message.from_user.id
        name = message.text
        if name is None:
            raise Exception("Name is empty")
        save_registration_state(user_id, name=name)
        bot.send_message(message.chat.id, "Сколько вам лет?")
        bot.register_next_step_handler(message, process_age)
    except Exception as e:
        print(f"Ошибка в process_name: {e}")
        bot.register_next_step_handler(message, process_name)
        bot.reply_to(message, '️⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


def process_age(message):
    try:
        user_id = message.from_user.id
        age = int(message.text)
        if 10 <= age <= 18:
            save_registration_state(user_id, age=age)
            markup = gender_menu(searching=False, age=age)
            bot.send_message(message.chat.id, "Кто вы?", reply_markup=markup)
            bot.register_next_step_handler(message, process_gender)
        else:
            bot.reply_to(message, "К сожалению вы не можете пользоваться нашим ботом 😔 По нашим правилам пользоваться нашим ботом можно только от 10 до 18 лет")
            bot.register_next_step_handler(message, process_age)
            return
    except Exception as e:
        print(f"Ошибка в process_age: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка. Пожалуйста, введите возраст цифрами.")
        bot.register_next_step_handler(message, process_age)


def process_gender(message):
    try:
        user_id = message.from_user.id
        gender = message.text
        if gender is None:
            raise Exception("Gender is empty")
        parsed_gender = gender.lower().split()[1]
        if parsed_gender not in ['парень', 'девушка', 'мальчик', 'девочка']:
            bot.reply_to(message, "⚠️ Пожалуйста, сделайте выбор из предложенных опций")
            bot.register_next_step_handler(message, process_gender)
            return
        else:
            if parsed_gender in ['парень', 'мальчик']:
                save_registration_state(user_id, gender='М')
            else:
                save_registration_state(user_id, gender='Ж')
            bot.send_message(message.chat.id, "Расскажите о своих интересах (перечислите через запятую):")
            bot.register_next_step_handler(message, process_interests)
    except Exception as e:
        print(f"Ошибка в process_gender: {e}")
        bot.register_next_step_handler(message, process_gender)

        bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, нажмите на одну из кнопок')


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

            bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')
    except Exception as e:
        print(f"Ошибка в process_interests: {e}")
        bot.register_next_step_handler(message, process_interests)

        bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


def process_about_me(message):
    """Сохраняет 'о себе' пользователя и завершает регистрацию."""
    try:
        user_id = message.from_user.id
        about_me = message.text
        if about_me:
            save_registration_state(user_id, about_me=about_me)

            markup = location_menu(searching=False)
            bot.send_message(message.chat.id, "В каком корпусе 1518 Вы учитесь?", reply_markup=markup)
            bot.register_next_step_handler(message, process_location)

        else:
            bot.register_next_step_handler(message, process_about_me)
            bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')
    except Exception as e:
        print(f"Ошибка в process_about_me: {e}")
        bot.register_next_step_handler(message, process_about_me)
        bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


def process_location(message):
    """Сохраняет 'о себе' пользователя и завершает регистрацию."""
    try:
        user_id = message.from_user.id
        location = message.text
        if location is None:
            raise Exception("Location is empty")
        parsed_location = location.lower()
        if 'цандер' not in parsed_location and 'проспект' not in parsed_location and 'мир' not in parsed_location:
            bot.reply_to(message, "⚠️ Пожалуйста, сделайте выбор из предложенных опций")
            bot.register_next_step_handler(message, process_location)
            return
        else:
            if 'цандер' in parsed_location:
                save_registration_state(user_id, location='Цандера')
            else:
                save_registration_state(user_id, location='Проспект мира')
            bot.send_message(message.chat.id, "Ваше фото:")
            bot.register_next_step_handler(message, process_photo)

    except Exception as e:
        print(f"Ошибка в process_location: {e}")
        bot.register_next_step_handler(message, process_location)
        bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


def process_photo(message):
    """Сохраняет интересы пользователя и переходит к запросу 'о себе'."""
    try:
        user_id = message.from_user.id
        photo = message.photo[-1].file_id
        file_info = bot.get_file(photo)
        downloaded_file = bot.download_file(file_info.file_path)
        if not os.path.exists('images'):
            os.mkdir('images')

        with open(f"images/image{user_id}.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
        if photo:
            registration_state = get_registration_state(user_id)
            name = registration_state.get('name')
            age = registration_state.get('age')
            gender = registration_state.get('gender')
            interests = registration_state.get('interests')
            about_me = registration_state.get('about_me')
            location = registration_state.get('location')

            username = message.from_user.username

            save_user_data(user_id, name, age, gender, interests, about_me, downloaded_file, location, username)
            clear_registration_state(user_id)
            markup = main_buttons_menu()
            bot.send_message(message.chat.id, "Спасибо за регистрацию! Теперь вы можете начать поиск",
                             reply_markup=markup)
            text = f"Ваша анкета выглядит так:\n\n<b>{name}</b><i>, {age} лет, {location}.</i> \nИнтересы: {interests}\n{about_me}"
            bot.send_photo(message.chat.id, photo=open(f'images/image{user_id}.jpg', 'rb'),
                                          caption=text, reply_markup=markup, parse_mode='HTML')
        else:
            bot.register_next_step_handler(message, process_photo)

            bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')
    except Exception as e:
        print(f"Ошибка в process_photo: {e}")
        bot.register_next_step_handler(message, process_photo)

        bot.reply_to(message, '⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз ввести данные')


# --- Запуск бота ---
if __name__ == '__main__':
    bot.user_search_data = {}
    create_table()

    print("Бот запущен...")
    bot.infinity_polling()