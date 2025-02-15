import random
import telebot
from telebot.types import ReplyKeyboardRemove
from telebot import types
from db import *
import os

BOT_TOKEN = open('token.txt').readline()
if '\n' in BOT_TOKEN:
    BOT_TOKEN = BOT_TOKEN[:-1]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='MARKDOWN')


def main_buttons_menu():
    btn_search = types.KeyboardButton("🔍 Поиск 🔍")
    btn_likes = types.KeyboardButton("💘 Кто меня лайкнул 💘")
    btn_settings_profile = types.KeyboardButton("👤 Управление аккаунтом 👤")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(btn_search, btn_likes, btn_settings_profile)
    return markup


def settings_buttons_menu():
    btn_edit_profile = types.KeyboardButton("✏️ Изменить профиль ✏️")
    btn_delete_profile = types.KeyboardButton("❌ Удалить аккаунт ❌")
    btn_settings_profile = types.KeyboardButton("🔙 Назад 🔙")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(btn_edit_profile, btn_delete_profile, btn_settings_profile)
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


def location_menu():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('🏫 Проспект', '🏢 Цандера')
    return  markup


def send_user_profile(header: str, data, message, markup):
    text = f"{header}\n\n<b>{data['name']}</b><i>, {data['age']} лет, {data['location']}.</i> \nИнтересы: {data['interests']}\n{data['about_me']}"
    sent_message = bot.send_photo(message.chat.id, photo=open(f'images/image{data["user_id"]}.jpg', 'rb'), caption=text,
                                  reply_markup=markup, parse_mode='HTML')
    return sent_message


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Приветственное сообщение и инструкция."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if existing_data and existing_data['status'] != 'banned':
        bot.reply_to(message, "Твои данные найдены 🗂")
        markup = main_buttons_menu()
        bot.send_message(message.chat.id, "Теперь ты можете начать поиск 💫", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("🚀 Регистрация 🚀")
        markup.add(btn_register)
        bot.reply_to(message, "🤗 Привет! Добро пожаловать в бота для знакомств школы 1518! "
                              "Здесь ты сможешь найти себе людей для общения, "
                              "совместного время препровождения, а может и нечто большее.. "
                              "В любом случае желаю удачи! 🤗", reply_markup=markup)


@bot.message_handler(func=lambda message: "регистрация" in message.text.lower())
def register_start(message):
    """Начинает процесс регистрации."""
    bot.send_message(message.chat.id, "📄 Регистрируясь, Вы принимаете правила: https://t.me/barboslyandiya/41")
    link = '<a href="https://core.telegram.org/bots/api#markdown-style">для возможности Вашего пинга</a>'
    bot.send_message(message.chat.id, f"✔️ Так же обратите Ваше внимание: для корректной работы бота вы должны разрешить пересылку сообщений ({link})\n"
                                      "(Настройки > Конфиденциальность > Пересылка сообщений > Все)", parse_mode="HTML", disable_web_page_preview=True)
    fr = open('ban.txt', 'r')
    ban_data = list(map(str.strip, fr.readlines()))
    if str(message.chat.id) not in ban_data:
        bot.send_message(message.chat.id, "Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_name)
    else:
        ping = f"[choco_p1e](https://t.me/choco_p1e)"
        bot.send_message(message.chat.id, f"Прости друг, но на тебя поступила жалоба и ты был забанен. Разбан: {ping}", reply_markup=ReplyKeyboardRemove())


@bot.message_handler(func=lambda message: "поиск" in message.text.lower())
def search_command(message):
    """Запускает процесс поиска пользователей по полу."""
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь 🙏")
        return
    else:
        markup = gender_menu(searching=True, age=existing_data['age'])
        bot.send_message(message.chat.id, "Кого ты хочешь найти?", reply_markup=markup)
        bot.register_next_step_handler(message, process_search_gender)


@bot.message_handler(func=lambda message: "кто меня лайкнул" in message.text.lower())
def show_likers(message):
    """Показывает пользователей, которые лайкнули данного пользователя."""
    user_id = message.from_user.id
    likers = get_liked_by(user_id)
    existing_data = get_user_data(user_id)
    if likers:
        bot.user_search_data[user_id] = {
            'likers': likers,
            'current_index': 0
        }
        show_liker_profile(message, user_id)
    else:
        bot.send_message(message.chat.id, "Сейчас здесь пусто, подожди пока тобой кто-то заинтересуется...")


def show_liker_profile(message, user_id):
    """Показывает профиль лайкнувшего пользователя с кнопками Лайк и Дизлайк."""
    user_search_data = bot.user_search_data.get(user_id)
    if not user_search_data or 'likers' not in user_search_data:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз", reply_markup=main_buttons_menu)
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
            send_user_profile("Твоя анкета понравилась:", liker_data, message, markup)
        else:
            bot.send_message(message.chat.id, "⚠️ Данные пользователя недоступны. Скорее всего он её удалил")


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
            bot.register_next_step_handler(call.message, go_back_to_main_menu)

            bot.send_animation(liker_id, open('resources/happy_gif.mp4', 'rb'))
            bot.send_animation(user_id, open('resources/happy_gif.mp4', 'rb'))

            user_ping = f"[{user_data['username']}](tg://user?id={user_data['user_id']})"
            bot.send_message(liker_id,f"🤩 Взаимная симпатия с {user_data['name']}!\n Начинай общаться {user_ping}")
            liker_ping = f"[{liker_data['username']}](tg://user?id={liker_data['user_id']})"
            bot.send_message(user_id,f"🤩 Взаимная симпатия с {liker_data['name']}!\n Начинай общаться {liker_ping}")
        show_next_liker(call.message, user_id)
    except Exception as e:
        print(f"Ошибка в like_liker_callback: {e}")
        bot.send_message(call.message.chat.id, "⚠️ Произошла неизвестная ошибка. Если для вас это критично сообщите об этом @mutiilat1on")


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
        bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, попробуйте еще раз.",reply_markup=main_buttons_menu())


def show_next_liker(message, user_id):
    """Переходит к следующему лайкнувшему пользователю."""
    user_search_data = bot.user_search_data.get(user_id)
    if not user_search_data or 'likers' not in user_search_data:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, попробуйте ещеё раз.", )
        return

    likers = user_search_data['likers']
    current_index = user_search_data.get('current_index', 0)

    if current_index + 1 < len(likers):
        user_search_data['current_index'] = current_index + 1
        show_liker_profile(message, user_id)
    else:
        del bot.user_search_data[user_id]


@bot.message_handler(func=lambda message: "управление аккаунтом" in message.text.lower())
def setting_profile(message):
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь 🙏")
        return
    else:
        settings_buttons_menu()
        markup = settings_buttons_menu()
        send_user_profile("Сейчас твоя анкета выглядит так:", existing_data, message, markup)
        bot.send_message(message.chat.id, "Ну давай поуправляем", reply_markup=markup)


@bot.message_handler(func=lambda message: "изменить профиль" in message.text.lower())
def edit_profile(message):
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь 🙏")
        return
    else:
        bot.send_message(message.chat.id, "Как теперь тебя стоит называть?", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(message, process_name)


@bot.message_handler(func=lambda message: "удалить аккаунт" in message.text.lower())
def delete_profile(message):
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь 🙏")
        return
    else:
        delete_user(user_id)
        delete_likes(user_id)
        main_buttons_menu()
        bot.send_animation(message.chat.id, open('resources/sad_gif.mp4', 'rb'))
        bot.send_message(message.chat.id, "☑️ Твой аккаунт успешно удалён 🗑", reply_markup=ReplyKeyboardRemove())


@bot.message_handler(func=lambda message: "назад" in message.text.lower())
def setting_exit_profile(message):
    user_id = message.from_user.id
    existing_data = get_user_data(user_id)
    if not existing_data:
        bot.reply_to(message, "Пожалуйста, сначала зарегистрируйтесь 🙏")
        return
    else:
        main_buttons_menu()
        markup = main_buttons_menu()
        bot.send_message(message.chat.id, "Возвращаемся назад ◀️", reply_markup=markup)


# --- Остальные функции и обработчики ---

def go_back_to_main_menu(message):
    user_id = message.chat.id
    existing_data = get_user_data(user_id)
    if existing_data:
        markup = main_buttons_menu()
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("🚀 Регистрация 🚀")
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
        if gender.lower() in ['парней', 'мальчиков']:   # Гендер фильтр
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
                             "💔 К сожалению, больше пользователей с такими параметрами не найдено", reply_markup=main_buttons_menu())

    except Exception as e:
        print(f"Ошибка в process_search_gender: {e}")
        bot.reply_to(message, '💔 Произошла ошибка при поиске. Прости, но пользователей подходящих под параметры указанные не найдено', reply_markup=main_buttons_menu())


def show_user(message, user_id):
    user_search_data = bot.user_search_data.get(user_id)
    if not user_search_data:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, начните поиск заново" , reply_markup=main_buttons_menu())
        return
    users = user_search_data['users']
    if not users:
        gender = user_search_data['gender']
        users = get_available_users(user_id, gender)
        user_search_data['users'] = users

    user = random.choice(users)
    markup = types.InlineKeyboardMarkup()
    btn_like = types.InlineKeyboardButton("❤️", callback_data=f"like:{user['user_id']}")
    btn_dislike = types.InlineKeyboardButton("👎", callback_data=f"dislike:{user['user_id']}")
    btn_complaint = types.InlineKeyboardButton("Жалоба", callback_data=f"complaint:{user['user_id']}")
    btn_back_to_menu = types.InlineKeyboardButton("Назад", callback_data="back_to_menu")
    markup.add(btn_like, btn_dislike, btn_complaint, btn_back_to_menu)
    sent_message = send_user_profile("Нашел вот кого:", user, message, markup)
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
    likes_sp = check_like(user_id)
    if likee_id not in likes_sp:
        bot.send_message(likee_id, '💘 Тебя кто-то лайкнул! Нажми <i>кто меня лайкнул</i>, чтобы посмотреть 👀',
                     parse_mode='HTML')

    save_like(user_id, likee_id)

    if check_match(user_id, likee_id):
        save_match(user_id, likee_id)

        user_data = get_user_data(user_id)
        liker_data = get_user_data(likee_id)
        if user_data is not None:
            remove_like(likee_id, user_id)
            remove_like(user_id, likee_id)
            bot.register_next_step_handler(call.message, go_back_to_main_menu)

            bot.send_animation(likee_id, open('resources/happy_gif.mp4', 'rb'))
            bot.send_animation(user_id, open('resources/happy_gif.mp4', 'rb'))

            user_ping = f"@{user_data['username']}" if user_data.get('username') else "{ошибка получения лс}"
            bot.send_message(likee_id,f"🤩 Взаимная симпатия с {user_data['name']}!\n Начинай общаться {user_ping}")
            liker_ping = f"@{liker_data['username']}" if liker_data.get('username') else "{ошибка получения лс}"
            bot.send_message(user_id,f"🤩 Взаимная симпатия с {liker_data['name']}!\n Начинай общаться {liker_ping}")

            bot.register_next_step_handler(call.message, go_back_to_main_menu)

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
        bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка. Пожалуйста, начните поиск заново", reply_markup=main_buttons_menu())


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
        btn_register = types.KeyboardButton("🚀 Регистрация 🚀")
        markup.add(btn_register)
        bot.send_message(call.message.chat.id, "Пожалуйста, зарегистрируйтесь 🙏", reply_markup=markup)

    if user_id in bot.user_search_data:
        del bot.user_search_data[user_id]

    bot.answer_callback_query(call.id, "Возвращаемся...")


@bot.callback_query_handler(func=lambda call: call.data.startswith('complaint:'))
def complaint_callback(call):
    user_id = call.from_user.id
    existing_data = get_user_data(user_id)
    complaint_user_id = int(call.data.split(':')[1])
    data_user = get_user_data(complaint_user_id)
    if existing_data:
        markup = types.InlineKeyboardMarkup()
        btn_ban = types.InlineKeyboardButton("Бан", callback_data=f"user_id_ban:{data_user['user_id']}:{data_user['username']}")
        btn_skip = types.InlineKeyboardButton("Пощада", callback_data=f"user_id_not_ban:{data_user['user_id']}:{data_user['username']}")
        markup.add(btn_ban, btn_skip)
        bot.send_message(call.message.chat.id, "Ваша жалоба отправлена барбосам")
        text = f'[{get_user_data(call.from_user.id)['username']}](tg://user?id={call.from_user.id}) наябидничал на [{data_user['username']}](tg://user?id={data_user['user_id']}):\n\n' + '\n'.join(str(call.message.caption).split('\n')[2:])
        bot.send_photo(chat_id='@qweoqw', caption=text, photo=open(f'images/image{data_user["user_id"]}.jpg', 'rb'), reply_markup=markup)
        check_complaint(complaint_user_id)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_register = types.KeyboardButton("🚀 Регистрация 🚀")
        markup.add(btn_register)
        bot.send_message(call.message.chat.id, "Пожалуйста, зарегистрируйтесь 🙏", reply_markup=markup)

    if user_id in bot.user_search_data:
        del bot.user_search_data[user_id]

    bot.answer_callback_query(call.id, "Возвращаемся...")


@bot.callback_query_handler(func=lambda call: call.data.startswith('user_id_ban:'))
def ban_callback(call):
    ban_user_id = int(call.data.split(':')[1])
    ban_username = call.data.split(':')[2]
    check_ban(ban_user_id)
    fr = open('./ban.txt', 'r')
    ban_data = list(map(str.strip, fr.readlines()))
    if ban_user_id not in ban_data:
        ban_data.append(str(ban_user_id))
    fw = open('./ban.txt', 'w')
    print('\n'.join(ban_data), file=fw)
    delete_user(ban_user_id)
    user_ban_ping = f"[{ban_username}](tg://user?id={ban_user_id})"
    user_ping = f"[{get_user_data(call.from_user.id)['username']}](tg://user?id={call.from_user.id})"
    bot.reply_to(call.message, f'{user_ping} забанил {user_ban_ping} 😈')


@bot.callback_query_handler(func=lambda call: call.data.startswith('user_id_not_ban:'))
def ban_callback(call):
    unban_user_id = int(call.data.split(':')[1])
    unban_username = call.data.split(':')[2]
    check_unban(unban_user_id)
    fr = open('./ban.txt', 'r')
    ban_data = list(map(str.strip, fr.readlines()))
    if str(unban_user_id) in ban_data:
        ban_data.remove(str(unban_user_id))
    fw = open('./ban.txt', 'w')
    print('\n'.join(ban_data), file=fw)
    user_unban_ping = f"[{unban_username}](tg://user?id={unban_user_id})"
    user_ping = f"[{get_user_data(call.from_user.id)['username']}](tg://user?id={call.from_user.id})"
    bot.reply_to(call.message, f'{user_ping} пощадил {user_unban_ping} 😇')


# --- Обработчики шагов регистрации ---

def process_name(message):
    try:
        user_id = message.from_user.id
        name = message.text
        if name is None or len(name) > 100 or 'https:/' in name:
            raise Exception("Name is empty")
        save_registration_state(user_id, name=name)
        bot.send_message(message.chat.id, "Сколько тебе лет?")
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
            bot.send_message(message.chat.id, "Кто ты?", reply_markup=markup)
            bot.register_next_step_handler(message, process_gender)
        else:
            bot.reply_to(message, "К сожалению Вы не можете пользоваться нашим ботом 😔 По нашим правилам пользоваться нашим ботом можно только от 10 до 18 лет")
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
        if interests and len(interests) < 1000 and 'https:/' not in interests:
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
        if about_me and len(about_me) < 1000 and 'https:/' not in about_me:
            save_registration_state(user_id, about_me=about_me)

            markup = location_menu()
            bot.send_message(message.chat.id, "В каком корпусе 1518 ты учишься?", reply_markup=markup)
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
            send_user_profile("Твоя анкета выглядит так:", get_user_data(user_id), message, markup)

            bot.send_message(message.chat.id, "Спасибо за регистрацию! Теперь ты можешь начать поиск",
                             reply_markup=markup)
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




