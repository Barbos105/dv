import sqlite3
import random

DATABASE_NAME = 'registration_data.db'


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
        photo BLOB,
        location TEXT,
        username TEXT  -- Новое поле для username
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registration_states (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age TEXT,
        gender TEXT,
        interests TEXT,
        about_me TEXT,
        photo BLOB,
        location TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

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



def save_user_search_data(user_id, name, age, gender, interests, about_me, photo, location, username=None):
    """Сохраняет данные пользователя в базу данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, name, age, gender, interests, about_me, photo, location, username) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, name, age, gender, interests, about_me, photo, location, username))
    conn.commit()
    conn.close()


def get_user_search_data(user_id):
    """Получает данные пользователя из базы данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, age, gender, interests, about_me, photo, location, username FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return {'user_id': data[0], 'name': data[1], 'age': data[2], 'gender': data[3], 'interests': data[4],
                'about_me': data[5], 'photo': data[6], 'location': data[7], 'username': data[8] }
    else:
        return None



def save_registration_state(user_id, name=None, age=None, gender=None, interests=None, about_me=None, location=None):
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
    if about_me is not None:
        cursor.execute("UPDATE registration_states SET about_me = ? WHERE user_id = ?", (about_me, user_id))
    if location is not None:
        cursor.execute("UPDATE registration_states SET location = ? WHERE user_id = ?", (location, user_id))

    conn.commit()
    conn.close()


def get_registration_state(user_id):
    """Получает промежуточное состояние регистрации из базы данных."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, age, gender, interests, about_me, location FROM registration_states WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    if data:
        return {'name': data[0], 'age': data[1], 'gender': data[2], 'interests': data[3], 'about_me': data[4], 'location': data[5]}
    else:
        return {}


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

    if gender == 'МЖ':
        query = "SELECT user_id, name, age, interests, about_me, location, username FROM users WHERE user_id != ?"
        cursor.execute(query, (user_id,))
    else:
        query = "SELECT user_id, name, age, interests, about_me, location, username FROM users WHERE gender = ? AND user_id != ?"
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
            'location': user[5],
            'username': user[6]
        }
        for user in users
    ]
    random.shuffle(available_users)
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