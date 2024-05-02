#HOME OF UNITY BOT
import telebot
import sqlite3
import config
from time import sleep
import random
import logging

db = sqlite3.connect("data.db", check_same_thread=False)

bot = telebot.TeleBot(config.TOKEN)


#Logger settings
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler("bot.log")
handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s | (%(levelname)s): %(message)s (Line: %(lineno)d) [%(filename)s]', datefmt='%d-%m-%Y %I:%M:%S')

handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(console_handler)


def add_to_database(user_id, username):
	logger.debug("adding to the database...")
	with db as cursor:
		cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (user_id, "empty", username, 0, config.DEFAULT, "empty", 0, "empty", "empty"))
	logger.info(f"user {user_id} added to the database")
	send_message_to_specific_category_users(f"Пользователь @{username} добавлен(а) в базу данных.", config.ADMIN, user_id)

#Give username and category of user
def select_name_and_category(text):
	logger.debug("select_name_and_category...")
	if text[9] == " ":
		text = text[10:]
		username = []
		one = True
		level = -1

		for i in text:
			if i != " " and one:
				username.append(i)
			elif i == " ":
				one = False
			elif i != " ":
				level = int(i)

		if level >= config.BAN and level <= config.DEVELOPER:
			username = "".join(username)
			return [username, level]
		else:
			return False
	else:
		return False

#Get random text from the databse
def get_random_text():
	with db as cursor:
		texts = cursor.execute("SELECT text FROM texts")
	texts_list = []
	for text in texts:
		texts_list.append(text[0])
	random_text_id = random.randint(0, len(texts_list)-1)
	return str(texts_list[random_text_id])

#Notifications of baned user try use bot
def is_baned(user_id, command):
	logger.info(f"baned user {user_id} try use command \"{command}\"")
	bot.send_message(user_id, f"У вас недостаточно прав для использования этой команды.\nПожалуйста, обратитесь к лидеру или ответственному за бота.")

#Check rules of user
def get_user_category(user_id):
	with db as cursor:
		info = cursor.execute("SELECT rules FROM users WHERE user_id = ?", (user_id,)).fetchone()
	if info == None:
		logger.debug(f"not found rules of user {user_id}")
		return False
	else:
		return info[0]

#Check user id
def check_user_id(user_id):
	with db as cursor:
		info = cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
	return info is not None

#Check username
def check_username(username):
	with db as cursor:
		info = cursor.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
	return info is not None

#Get user id from username
def get_id_using_username(username):
	with db as cursor:
		info = cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,)).fetchone()
	if info == None:
		logger.debug(f"not found user @{username}")
		return False
	else:
		return info[0]


#Send a message to a specific category of users
def send_message_to_specific_category_users(text, necessary_rules, sender):
	count = 0
	with db as cursor:
		users = cursor.execute("SELECT user_id FROM users WHERE rules >= ?", (necessary_rules,))
	for user in users:
		if user[0] != str(sender):
			try:
				bot.send_message(user[0], text)
				count += 1
			except Exception:
				logger.info(f"error sending message to user {user[0]}")
				send_message_to_specific_category_users(f"Ошибка!\nПроверьте пользователя {user[0]}", config.DEVELOPER, 0)
	logger.debug(f"send a message to a specifical category to {count} user(s)")
	return count


#Command start
@bot.message_handler(commands=['start'])
def start(message):
	logger.debug(f"user {message.from_user.id} tried use command \"start\"...")
	try:
		if check_user_id(message.from_user.id) == False:
			logger.debug("pre_add")
			add_to_database(message.from_user.id, message.from_user.username)

		if get_user_category(message.from_user.id) >= config.DEFAULT:
			bot.send_message(message.from_user.id, config.START_TEXT)
		else:
			is_baned(message.from_user.id, "start")
	except Exception as e:
		logger.error(e)


#Added to prays lists
@bot.message_handler(commands=['prays_lists'])
def change_state(message):
	logger.debug(f"user {message.from_user.id} tried use command \"prays_lists\"...")
	try:
		if check_user_id(message.from_user.id) == False:
			add_to_database(message.from_user.id, message.from_user.username)

		if get_user_category(message.from_user.id) >= config.DEFAULT:
			if check_username(message.from_user.username) == True and message.from_user.username != None:
				with db as cursor:
					users = cursor.execute("SELECT user_id, state FROM users WHERE rules >= ?", (config.DEFAULT,))
				for user in users:
					if user[0] == str(message.from_user.id):
						logger.debug(f"try change state...")
						state = 0
						if user[1] == 1:
							logger.info(f"user {user[0]} has been removed from prays lists")
							send_message_to_specific_category_users(f"Пользователь @{message.from_user.username} исключил(а) себя из молитвенных листочков.", config.ADMIN, message.from_user.id)
							bot.send_message(user[0], "Вы исключены из молитвенных листочков.")
						else:
							state = 1
							logger.info(f"user {user[0]} added to prays lists")
							send_message_to_specific_category_users(f"Пользователь @{message.from_user.username} добавил(а) себя в молитвенные листочки.", config.ADMIN, message.from_user.id)
							bot.send_message(user[0], "Вы добавлены в молитвенные листочки.")
						with db as cursor:
							cursor.execute("UPDATE users SET state = ? WHERE user_id = ?", (state, user[0]))
			else:
				logger.debug(f"{message.from_user.id} dont have username")
				bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")
		else:
			is_baned(message.from_user.id, "prays_lists")
	except Exception as e:
		logger.error(e)


#Added event
@bot.message_handler(commands=['event'])
def change_event_state(message):
	logger.debug(f"user {message.from_user.id} tried use command \"event\"...")
	try:
		if check_user_id(message.from_user.id) == False:
			add_to_database(message.from_user.id, message.from_user.username)

		if get_user_category(message.from_user.id) >= config.DEFAULT:
			if check_username(message.from_user.username) == True and message.from_user.username != None:
				with db as cursor:
					users = cursor.execute("SELECT user_id, event FROM users WHERE rules >= ?", (config.DEFAULT,))
				for user in users:
					if user[0] == str(message.from_user.id):
						logger.debug(f"try change event_state...")
						bot.send_message(message.from_user.id, "Регистрация недоступна.")
#						state = 0
#						if user[1] == 1:
#							logger.info(f"user {user[0]} has been removed from event lists")
#							send_message_to_specific_category_users(f"Пользователь @{message.from_user.username} больше не учавствует в дополнительном событии.", config.ADMIN, message.from_user.id)
#							bot.send_message(user[0], "Вы больше не тайный ангел.")
#						else:
#							state = 1
#							logger.info(f"user {user[0]} added to event")
#							send_message_to_specific_category_users(f"Пользователь @{message.from_user.username} учавствует в дополнительном событии.", config.ADMIN, message.from_user.id)
#							bot.send_message(user[0], "Теперь вы тайный ангел.")
#						with db as cursor:
#							cursor.execute("UPDATE users SET event = ? WHERE user_id = ?", (state, user[0]))
			else:
				logger.debug(f"user {message.from_user.id} dont have username")
				bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")
		else:
			is_baned(message.from_user.id, "event")
	except Exception as e:
		logger.error(e)


#Set the user to developer category
@bot.message_handler(commands=['key'])
def set_the_user_to_developer_category(message):
	logger.debug(f"user {message.from_user.id} is trying to get developer rights...")
	try:
		if check_user_id(message.from_user.id) == False:
			add_to_database(message.from_user.id, message.from_user.username)

		with db as cursor:
			cursor.execute("UPDATE users SET rules = ? WHERE user_id = ?", (config.DEVELOPER, message.from_user.id))
		logger.info(f"user {message.from_user.id} has been granted developer rights")
		bot.send_message(message.from_user.id, "Ваши права изменены на \'РАЗРАБОТЧИК\'")
		send_message_to_specific_category_users(f"Пользователь @{message.from_user.username} получил права разработчика при помощи ключа.", config.DEVELOPER, message.from_user.id)
	except Exception as e:
		logger.error(e)


#Send the user information about the bot
@bot.message_handler(commands=['info'])
def send_info(message):
	logger.debug(f"user {message.from_user.id} tried use command \"info\"...")

	if check_user_id(message.from_user.id) == False:
		add_to_database(message.from_user.id, message.from_user.username)

	if get_user_category(message.from_user.id) >= config.DEFAULT:
		logger.debug(f"bot information was successfully sent to user {message.from_user.id}")
		bot.send_message(message.from_user.id, config.INFO)
	else:
		is_baned(message.from_user.id, "info")


#Update data of user in Data Base
@bot.message_handler(commands=['update'])
def update_user_data(message):
	logger.debug(f"user {message.from_user.id} is trying to update his username...")
	try:
		if check_user_id(message.from_user.id) == False:
			add_to_database(message.from_user.id, message.from_user.username)

		else:
			logger.debug("updating...")
			with db as cursor:
				cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (message.from_user.username, message.from_user.id))
			logger.debug(f"username {message.from_user.id} update completed successfully")
			send_message_to_specific_category_users(f"Пользователь @{message.from_user.username} успешно обновил(а) своё имя пользователя.", config.DEVELOPER, message.from_user.id)
			bot.send_message(message.from_user.id, "Ваше имя пользователя обновлено.")
	except Exception as e:
		logger.error(e)


#Who i am?
@bot.message_handler(commands=['who'])
def who_i_am(message):
	logger.debug(f"user {message.from_user.id} is trying to use command \"who\"...")
	try:
		if check_user_id(message.from_user.id) == False:
			add_to_database(message.from_user.id, message.from_user.username)

		complete = True
		rules = get_user_category(message.from_user.id)
		if rules == config.DEFAULT:
			rules = "ПОЛЬЗОВАТЕЛЬ"
		elif rules == config.MODERATOR:
			rules = "МОДЕРАТОР"
		elif rules == config.ADMIN:
			rules = "АДМИНИСТРАТОР"
		elif rules == config.DEVELOPER:
			rules = "РАЗРАБОТЧИК"
		elif rules == config.BAN:
			rules = "ЗАБЛОКИРОВАН"
		else:
			complete = False

		if complete == True:
			logger.debug(f"the command completed successfully!")
			bot.send_message(message.from_user.id, f"Ваш уровень доступа относится к категории \"{rules}\"")
		else:
			logger.warning(f"not found access level of user {message.from_user.id}! (@{message.from_user.username})")
			bot.send_message(message.from_user.id, "Ошибка!\nВаш уровень доступа не относится ни к одной из категорий.\nПожалуйста, обратитесь к лидеру или ответственному за бота.")
	except Exception as e:
		logger.error(e)


#Other
@bot.message_handler(content_types=['text'])
def text(message):
	logger.debug(f"user {message.from_user.id} is trying to use command \"text\"...")
	try:
		if check_user_id(message.from_user.id) == False:
			add_to_database(message.from_user.id, message.from_user.username)

		#CHECK USERNAME
		if check_username(message.from_user.username) == True and message.from_user.username != None:
			rules_level = get_user_category(message.from_user.id)


			#CHECK BAN LEVEL
			if rules_level < config.DEFAULT:
				is_baned(message.from_user.id, "text")

			#SET MY WISH
			elif message.text[:8] == "/my_wish" and False: #OFF
				logger.debug("try set wish...")
				text = message.text[9:]
				with db as cursor:
					cursor.execute("UPDATE users SET my_wish = ? WHERE user_id = ?", (text, message.from_user.id))
				logger.debug(f"set wish for {message.from_user.id}")
				bot.send_message(message.from_user.id, f"Текст успешно сохранён")


			#RANDOMIZE USERS FOR PRAYS LISTS
			elif message.text == "/randomize" and rules_level >= config.MODERATOR:
				logger.debug("try randomize...")
				with db as cursor:
					users = cursor.execute("SELECT username, state FROM users WHERE rules >= ?", (config.DEFAULT,))
				prayers_list = []
				prayers_list_parallel = []
				users_id_in_use = []

				#Get list "only prayers"
				for user in users:
					if user[1] == 1:
						prayers_list.append(user[0])

				for i in range(len(prayers_list)):
					run_randomize = True
					while run_randomize:
						rand = True
						stop = False
						random_id = random.randint(0, len(prayers_list)-1)
						for x in users_id_in_use:
							if x == random_id:
								rand = False

						#Dont user1 -> user1
						if random_id == i and rand == True:
							if i == len(prayers_list)-1 and i != 0:
								prayers_list_parallel.append(prayers_list_parallel[0])
								prayers_list_parallel[0] = prayers_list[i]
								stop = True
								run_randomize = False
							else:
								rand = False

						if rand == True and stop == False:
							prayers_list_parallel.append(prayers_list[random_id])
							users_id_in_use.append(random_id)
							run_randomize = False

				for i in range(len(prayers_list)):
					logger.debug(f"{get_id_using_username(prayers_list[i])} -> {get_id_using_username(prayers_list_parallel[i])}")
					try:
						bot.send_message(get_id_using_username(prayers_list[i]), f"Привет!\nНа этой неделе ты молишься за @{prayers_list_parallel[i]}\n{get_random_text()}")
					except Exception:
						logger.warning(f"error sending message to user {get_id_using_username(prayers_list[i])}")
					with db as cursor:
						cursor.execute("UPDATE users SET prays_friend = ? WHERE username = ?", (prayers_list_parallel[i], prayers_list[i]))


			#START EVENT (RANDOMIZE)
			elif message.text == "/start_event" and False: #OFF
				logger.debug("try start_event...")
				with db as cursor:
					users = cursor.execute("SELECT username, event, my_wish FROM users WHERE rules >= ?", (config.DEFAULT,))
				users_list = []
				users_list_parallel = []
				users_id_in_use = []
				wish_of_users = []
				wish_of_users_parallel = []

				#Get list "only angels"
				for user in users:
					if user[1] == 1:
						users_list.append(user[0])
						wish_of_users.append(user[2])

				for i in range(len(users_list)):
					run_randomize = True
					while run_randomize:
						rand = True
						stop = False
						random_id = random.randint(0, len(users_list)-1)
						for x in users_id_in_use:
							if x == random_id:
								rand = False

						#Dont user1 -> user1
						if random_id == i and rand == True:
							if i == len(users_list)-1 and i != 0:
								users_list_parallel.append(users_list_parallel[0])
								wish_of_users_parallel.append(wish_of_users_parallel[0])
								users_list_parallel[0] = users_list[i]
								wish_of_users_parallel[0] = wish_of_users[i]
								stop = True
								run_randomize = False
							else:
								rand = False

						if rand == True and stop == False:
							users_list_parallel.append(users_list[random_id])
							wish_of_users_parallel.append(wish_of_users[random_id])
							users_id_in_use.append(random_id)
							run_randomize = False

				for i in range(len(users_list)):
					logger.debug(f"{get_id_using_username(users_list[i])} -> {get_id_using_username(users_list_parallel[i])}")
					try:
						bot.send_message(get_id_using_username(users_list[i]), f"Привет!\nТы тайный ангел для @{users_list_parallel[i]}\nЕго пожелания:\n{wish_of_users_parallel[i]}")
					except Exception:
						logger.warning(f"error sending message to user {get_id_using_username(users_list[i])}")
					with db as cursor:
						cursor.execute("UPDATE users SET santa_for = ? WHERE username = ?", (users_list_parallel[i], users_list[i]))


			#SEND MESSAGE TO ALL USERS
			elif message.text[:2] == "**" and rules_level >= config.MODERATOR:
				logger.debug("try send message to all user...")
				text = message.text[2:]
				count = send_message_to_specific_category_users(text, config.DEFAULT, message.from_user.id)
				logger.info(f"user {message.from_user.id} send message to {count} user(s)")
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} пользователям.")

			#SEND MESSAGE TO ALL PRAYERS
			elif message.text[:1] == "*" and rules_level >= config.MODERATOR:
				logger.debug("try send message to all prayer...")
				text = message.text[1:]
				count = 0
				with db as cursor:
					users = cursor.execute("SELECT user_id, state FROM users WHERE rules >= ?", (config.DEFAULT,))
				for user in users:
					if user[1] == 1 and str(message.from_user.id) != user[0]:
						try:
							bot.send_message(user[0], text)
							count += 1
						except Exception:
							logger.info(f"error sending message to user {user[0]}")
							send_message_to_specific_category_users(f"Ошибка!\nПроверьте пользователя {user[0]}", config.DEVELOPER, 0)
				logger.info(f"user {message.from_user.id} send message to {count} user(s):")
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} пользователям.")

			#SEND MESSAGE TO MODERATORS AND ADMINS
			elif message.text[0] == "!" and rules_level >= config.ADMIN:
				logger.debug("try send message to all moderators and admins...")
				text = message.text[1:]
				count = send_message_to_specific_category_users(text, config.MODERATOR, message.from_user.id)
				logger.info(f"user {message.from_user.id} send message to {count} admin(s)")
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} админам.")


			#CHANGE RULES OF USER
			elif message.text[:9] == "/setRules" and rules_level >= config.ADMIN:
				logger.debug(f"try change access level...")
				try:
					resours = select_name_and_category(message.text)
					if resours == False:
						logger.debug("change access level error! (level not found)")
						bot.send_message(message.from_user.id, "Ошибка! \nВведённое значение уровня доступа находится вне диапазона.")
					elif resours[1] == 0:
						logger.debug(f"user {message.from_user.id} tried to set access level 0 to user @{resours[0]}, but there is a /ban command for this")
						bot.send_message(message.from_user.id, "Для блокировки пользователя введите: \n/ban [username]")
					else:
						if check_username(resours[0]) == True:
							if get_user_category(message.from_user.id) >= resours[1]:
								if get_user_category(message.from_user.id) >= get_user_category(get_id_using_username(resours[0])):
									logger.debug("changing access level...")
									with db as cursor:
										cursor.execute("UPDATE users SET rules = ? WHERE username = ?", (resours[1], resours[0]))
									logger.info(f"user {message.from_user.id} set access level {resours[1]} to user {get_id_using_username(resours[0])}")
									if str(message.from_user.id) != str(get_id_using_username(resours[0])):
										bot.send_message(message.from_user.id, f"Уровень доступа @{resours[0]} успешно изменён на {resours[1]}")
									if get_user_category(get_id_using_username(resours[0])) < config.DEVELOPER or get_user_category(get_id_using_username(resours[0])) == config.DEVELOPER and str(message.from_user.id) == str(get_id_using_username(resours[0])):
										try:
											bot.send_message(get_id_using_username(resours[0]), f"Ваш уровень доступа изменён на {resours[1]}")
										except Exception:
											logger.info(f"error sending message to user {get_id_using_username(resours[0])}")
											send_message_to_specific_category_users(f"Ошибка оповещения пользователя! Проверьте пользователя @{resours[0]}", config.DEVELOPER, 0)
									send_message_to_specific_category_users(f"Пользователь @{message.from_user.username} изменил уровень доступа пользователя @{resours[0]} на {resours[1]}", config.DEVELOPER, message.from_user.id)
								else:
									logger.debug(f"user {message.from_user.id} access level is lower than user @{resours[0]}")
									bot.send_message(message.from_user.id, f"Вы не можете изменить уровень доступа этого пользователя, так как ваш уровень доступа ниже, чем уровень доступа @{resours[0]}")
							else:
								logger.debug(f"user {message.from_user.id} tries to give user {get_id_using_username(resours[0])} an access level higher than his own")
								bot.send_message(message.from_user.id, f"У вас недостаточно прав для выполнения этой команды.")
						else:
							logger.debug(f"user @{resours[0]} not found!")
							bot.send_message(message.from_user.id, f"Пользователя @{resours[0]} нет в базе данных.")

				except Exception as e:
					logger.debug(e)
					bot.send_message(message.from_user.id, f"Ошибка изменения прав пользователя.\nПроверьте, правильно ли вы ввели команду.")

			#BAN USER
			elif message.text[:4] == "/ban" and rules_level >= config.ADMIN:
				logger.debug(f"try ban user...")
				try:
					if message.text[4] == " ":
						text = message.text[5:]
						username = []

						for i in text:
							if i != " ":
								username.append(i)
							elif i == " ":
								break;

						username = "".join(username)

						if check_username(username) == True:
							if get_user_category(message.from_user.id) >= get_user_category(get_id_using_username(username)):
								logger.debug("changing access level...")
								with db as cursor:
									cursor.execute("UPDATE users SET rules = ?, state = ? WHERE username = ?", (config.BAN, 0, username))
								logger.info(f"user {message.from_user.id} blocked user {get_id_using_username(username)}")
								if str(message.from_user.id) != get_id_using_username(username):
									bot.send_message(message.from_user.id, f"Пользователь @{username} успешно заблокирован.")
								if get_user_category(get_id_using_username(username)) != config.DEVELOPER:
									try:
										bot.send_message(get_id_using_username(username), f"Вы заблокированы.")
									except Exception:
										logger.info(f"error sending message to user {get_id_using_username(username)}")
										send_message_to_specific_category_users(f"Ошибка оповещения пользователя! Проверьте пользователя @{get_id_using_username(user[0])} \n({user[0]})", config.DEVELOPER, 0)
								send_message_to_specific_category_users(f"@{message.from_user.username} заблокировал @{username}", config.DEVELOPER, message.from_user.id)
							else:
								logger.debug(f"user {message.from_user.id} dont have rules for ban user {get_id_using_username(username)}")
								bot.send_message(message.from_user.id, f"У вас недостаточно прав для блокировки пользователя @{username}")
						else:
							logger.debug(f"user @{username} not found!")
							bot.send_message(message.from_user.id, f"Пользователя @{username} нет в базе данных.")
					else:
						logger.debug("user blocked error! (the command was entered incorrectly)")
						bot.send_message(message.from_user.id, "Ошибка блокировки пользователя.\nПроверьте, правильно ли вы ввели команду.\nПосле \"/ban\" должен стоять пробел.")
				except Exception as e:
					logger.debug(e)
					bot.send_message(message.from_user.id, "Ошибка блокировки пользователя.\nПроверьте, правильно ли вы ввели команду.")


			#SEND HELP LIST
			elif message.text == "/help":
				logger.debug(f"try send help...")
				if rules_level >= config.ADMIN:
					bot.send_message(message.from_user.id, f"{config.MODERATOR_HELP_LIST}\n{config.ADMIN_HELP_LIST}")
				elif rules_level >= config.MODERATOR:
					bot.send_message(message.from_user.id, f"{config.MODERATOR_HELP_LIST}")
				logger.debug(f"the list of commands was successfully sent to user {message.from_user.id}")

		else:
			logger.debug(f"user {message.from_user.id} dont have username")
			bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")

	except Exception as e:
		logger.error(e)


#RUN
runBot = True
while runBot:
	logger.info("RUN BOT...")
	try:
		bot.polling()
	except Exception as e:
		logger.critical(e)
		sleep(3)

#CLOSE DATABASE
db.close()
