# user_utils_module
import sqlite3


# checking for user_id in the database
def check_user_id(user_id: int) -> bool:
    with sqlite3.connect("data.db") as cursor:
        info = cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()

    return info is not None


# checking for username in the database
def check_username(username: str) -> bool:
    with sqlite3.connect("data.db") as cursor:
        info = cursor.execute(
            "SELECT username FROM users WHERE username = ?", (username,)
        ).fetchone()

    return info is not None and info[0] is not None
