import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    referrer_id INTEGER,
    points INTEGER DEFAULT 0
)
""")

conn.commit()


def add_user(user_id, username=None, referrer_id=None):

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    if user:
        return False

    cursor.execute(
        """
        INSERT INTO users (
            user_id,
            username,
            referrer_id
        )
        VALUES (?, ?, ?)
        """,
        (user_id, username, referrer_id)
    )

    conn.commit()

    return True


def add_points(user_id, points):

    cursor.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (points, user_id)
    )

    conn.commit()


def get_points(user_id):

    cursor.execute(
        "SELECT points FROM users WHERE user_id=?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result:
        return result[0]

    return 0


def get_top_users():

    cursor.execute("""
    SELECT username, points
    FROM users
    ORDER BY points DESC
    LIMIT 5
    """)

    return cursor.fetchall()


def get_all_users():

    cursor.execute(
        "SELECT user_id FROM users"
    )

    return cursor.fetchall()