#user_utils_module
import sqlite3

db = sqlite3.connect("data.db", check_same_thread=False)

def check_user_id(user_id):
	with db as cursor:
		info = cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
	return info is not None

def check_username(username):
	with db as cursor:
		info = cursor.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
	return info is not None