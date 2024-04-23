#HOME OF UNITY BOT
import telebot
import sqlite3
import config
from time import sleep
import random
import logging

db = sqlite3.connect("data.db", check_same_thread=False)
cursor = db.cursor()

bot = telebot.TeleBot(config.TOKEN)


#Logger settings
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("bot.log")
handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s | (%(levelname)s): %(message)s (Line: %(lineno)d) [%(filename)s]', datefmt='%d-%m-%Y %I:%M:%S')

handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(console_handler)


#Give username and level rules
def giveNameAndLevel(text):
	logger.debug("giveNameAndLevel...")
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

		if level >= config.ban and level <= config.developer:
			username = "".join(username)
			return [username, level]
		else:
			return False

#Get text for randomize
def randomText():
	logger.debug("random text...")
	texts = cursor.execute("SELECT text FROM texts")
	texts_list = []
	for text in texts:
		texts_list.append(text[0])
	randomTextID = random.randint(0, len(texts_list)-1)
	return str(texts_list[randomTextID])

#Notifications of baned user try use bot
def be_baned(user_id, username, command):
	logger.debug("be_baned...")
	logger.info(f"baned user {user_id} try use command \"{command}\"")
	bot.send_message(user_id, f"У вас недостаточно прав для использования этой команды.\nПожалуйста, обратитесь к лидеру или ответственному за бота.")

#Check rules of user
def check_rules(user_id):
	logger.debug("check rules level...")
	users = cursor.execute("SELECT user_id, rules FROM users")
	for user in users:
		if user[0] == str(user_id):
			return user[1]

#Check user id
def check_user_id(user_id):
	logger.debug("check user id...")
	users = cursor.execute("SELECT user_id FROM users")
	for user in users:
		if user[0] == str(user_id):
			return 1

#Check username
def check_username(username):
	logger.debug("check username...")
	users = cursor.execute("SELECT username FROM users")
	for user in users:
		if user[0] == str(username):
			return 1

#Get user id from username
def getIDFromUsername(username):
	logger.debug("get id from username...")
	users= cursor.execute("SELECT username, user_id FROM users")
	for user in users:
		if user[0] == username:
			return user[1]

#Send message
def send_level_message(text, necessary_rules, sender):
	logger.debug("sending level message...")
	count = 0
	users = cursor.execute("SELECT user_id FROM users WHERE rules >= 0")
	for user in users:
		if check_rules(user[0]) >= necessary_rules and user[0] != str(sender):
			try:
				bot.send_message(user[0], text)
				count += 1
			except Exception:
				logger.info(f"error sending message to user {user[0]}")
	logger.debug(f"send level message to {count} user(s)")
	return count


#Command start
@bot.message_handler(commands=['start'])
def start(message):
	logger.debug(f"user {message.from_user.id} tried use command \"start\"...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")
			send_level_message(f"Пользователь @{message.from_user.username} добавлен(а) в базу данных.", config.admin, message.from_user.id)

		if check_rules(message.from_user.id) >= config.default:
			bot.send_message(message.from_user.id, config.start_text)
		else:
			be_baned(message.from_user.id, message.from_user.username, "start")
	except Exception as e:
		logger.exception(e)


#Added to prays lists
@bot.message_handler(commands=['prays_lists'])
def change_state(message):
	logger.debug(f"user {message.from_user.id} tried use command \"prays_lists\"...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")

		if check_rules(message.from_user.id) >= config.default:
			if check_username(message.from_user.username) == 1 and message.from_user.username != None:
				users = cursor.execute("SELECT user_id, state FROM users WHERE rules >= 0")
				for user in users:
					if user[0] == str(message.from_user.id):
						logger.debug(f"try change state...")
						state = 0
						if user[1] == 1:
							logger.info(f"user {user[0]} has been removed from prays lists")
							send_level_message(f"Пользователь @{message.from_user.username} исключил(а) себя из молитвенных листочков.", config.admin, message.from_user.id)
							bot.send_message(user[0], "Вы исключены из молитвенных листочков.")
						else:
							state = 1
							logger.info(f"user {user[0]} added to prays lists")
							send_level_message(f"Пользователь @{message.from_user.username} добавил(а) себя в молитвенные листочки.", config.admin, message.from_user.id)
							bot.send_message(user[0], "Вы добавлены в молитвенные листочки.")
						cursor.execute("UPDATE users SET state = ? WHERE user_id = ?", (state, user[0]))
						db.commit()
			else:
				logger.debug(f"{message.from_user.id} dont have username")
				bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")
		else:
			be_baned(message.from_user.id, message.from_user.username, "prays_lists")
	except Exception as e:
		logger.exception(e)


#Added event
@bot.message_handler(commands=['event'])
def change_event_state(message):
	logger.debug(f"user {message.from_user.id} tried use command \"event\"...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")

		if check_rules(message.from_user.id) >= config.default:
			if check_username(message.from_user.username) == 1 and message.from_user.username != None:
				users = cursor.execute("SELECT user_id, event FROM users WHERE rules >= 0")
				for user in users:
					if user[0] == str(message.from_user.id):
						logger.debug(f"try change event_state...")
						bot.send_message(message.from_user.id, "Регистрация недоступна.")
#						state = 0
#						if user[1] == 1:
#							logger.info(f"user {user[0]} has been removed from event lists")
#							send_level_message(f"Пользователь @{message.from_user.username} больше не учавствует в дополнительном событии.", config.admin, message.from_user.id)
#							bot.send_message(user[0], "Вы больше не тайный ангел.")
#						else:
#							state = 1
#							logger.info(f"user {user[0]} added to event")
#							send_level_message(f"Пользователь @{message.from_user.username} учавствует в дополнительном событии.", config.admin, message.from_user.id)
#							bot.send_message(user[0], "Теперь вы тайный ангел.")
#						cursor.execute("UPDATE users SET event = ? WHERE user_id = ?", (state, user[0]))
#						db.commit()
			else:
				logger.debug(f"user {message.from_user.id} dont have username")
				bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")
		else:
			be_baned(message.from_user.id, message.from_user.username, "event")
	except Exception as e:
		logger.exception(e)


#Give rights of developer
@bot.message_handler(commands=['key'])
def giveRulesDeveloper(message):
	logger.debug(f"user {message.from_user.id} is trying to get developer rights...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")

		cursor.execute("UPDATE users SET rules = ? WHERE user_id = ?", (config.developer, message.from_user.id))
		db.commit()
		logger.info(f"user {message.from_user.id} has been granted developer rights")
		bot.send_message(message.from_user.id, "Ваши права изменены на \"Developer\"")
		send_level_message(f"Пользователь @{message.from_user.username} получил права разработчика при помощи ключа.", config.developer, message.from_user.id)
	except Exception as e:
		logger.exception(e)


#Send info
@bot.message_handler(commands=['info'])
def send_info(message):
	logger.debug(f"user {message.from_user.id} tried use command \"info\"...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")

		if check_rules(message.from_user.id) >= config.default:
			logger.debug(f"send info to user {message.from_user.id}")
			bot.send_message(message.from_user.id, config.info)
		else:
			be_baned(message.from_user.id, message.from_user.username, "info")
	except Exception as e:
		logger.exception(e)


#Update data of user in Data Base
@bot.message_handler(commands=['update'])
def update_data(message):
	logger.debug(f"user {message.from_user.id} is trying to update his username...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")

		else:
			logger.debug("updating...")
			cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (message.from_user.username, message.from_user.id))
			db.commit()
			logger.debug(f"username {message.from_user.id} update completed successfully")
			send_level_message(f"Пользователь @{message.from_user.username} успешно обновил(а) своё имя пользователя.", config.developer, message.from_user.id)
			bot.send_message(message.from_user.id, "Ваше имя пользователя обновлено.")
	except Exception as e:
		logger.exception(e)


#Who i am?
@bot.message_handler(commands=['who'])
def who_i_am(message):
	logger.debug(f"user {message.from_user.id} is trying to use command \"who\"...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")

		complete = True
		rules = check_rules(message.from_user.id)
		if rules == 1:
			rules = "Пользователь"
		elif rules == 2:
			rules = "Модератор"
		elif rules == 3:
			rules = "Администратор"
		elif rules == 4:
			rules = "Разработчик"
		elif rules == 0:
			rules = "Заблокирован"
		else:
			complete = False

		if complete == True:
			logger.debug(f"the command completed successfully!")
			bot.send_message(message.from_user.id, f"Ваш уровень доступа относится к категории \"{rules}\"")
		else:
			logger.warning(f"not found access level of user {message.from_user.id}! (@{message.from_user.username})")
			bot.send_message(message.from_user.id, "Ошибка!\nВаш уровень доступа не относится ни к одной из категорий.\nПожалуйста, обратитесь к лидеру или ответственному за бота.")
	except Exception as e:
		logger.exception(e)


#Other
@bot.message_handler(content_types=['text'])
def text(message):
	logger.debug(f"user {message.from_user.id} is trying to use command \"text\"...")
	try:
		if check_user_id(message.from_user.id) != 1:
			logger.debug("adding to the database...")
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			logger.info(f"user {message.from_user.id} added to the database")


		#CHECK USERNAME
		if check_username(message.from_user.username) == 1 and message.from_user.username != None:
			rules_level = check_rules(message.from_user.id)


			#CHECK BAN LEVEL
			if rules_level < config.default:
				be_baned(message.from_user.id, message.from_user.username, "text")

			#SET MY WISH
			elif message.text[:8] == "/my_wish" and False: #OFF
				logger.debug("try set wish...")
				text = message.text[9:]
				cursor.execute("UPDATE users SET my_wish = ? WHERE user_id = ?", (text, message.from_user.id))
				db.commit()
				logger.debug(f"set wish for {message.from_user.id}")
				bot.send_message(message.from_user.id, f"Текст успешно сохранён")


			#RANDOMIZE USERS FOR PRAYS LISTS
			elif message.text == "/randomize" and rules_level >= config.moderator:
				logger.debug("try randomize...")
				users = cursor.execute("SELECT username, state FROM users WHERE rules >= 0")
				prayers_list = []
				prayers_list_parallel = []
				users_id_in_use = []

				#Get list "only prayers"
				for user in users:
					if user[1] == 1:
						prayers_list.append(user[0])

				for i in range(len(prayers_list)):
					runRandomize = True
					while runRandomize:
						rand = True
						stop = False
						randID = random.randint(0, len(prayers_list)-1)
						for x in users_id_in_use:
							if x == randID:
								rand = False

						#Dont user1 -> user1
						if randID == i and rand == True:
							if i == len(prayers_list)-1 and i != 0:
								prayers_list_parallel.append(prayers_list_parallel[0])
								prayers_list_parallel[0] = prayers_list[i]
								stop = True
								runRandomize = False
							else:
								rand = False

						if rand == True and stop == False:
							prayers_list_parallel.append(prayers_list[randID])
							users_id_in_use.append(randID)
							runRandomize = False

				for i in range(len(prayers_list)):
					logger.debug(f"{getIDFromUsername(prayers_list[i])} -> {getIDFromUsername(prayers_list_parallel[i])}")
					try:
						bot.send_message(getIDFromUsername(prayers_list[i]), f"Привет!\nНа этой неделе ты молишься за @{prayers_list_parallel[i]}\n{randomText()}")
					except Exception:
						logger.warning(f"error sending message to user {getIDFromUsername(prayers_list[i])}")
					cursor.execute("UPDATE users SET prays_friend = ? WHERE username = ?", (prayers_list_parallel[i], prayers_list[i]))
					db.commit()


			#START EVENT (RANDOMIZE)
			elif message.text == "/start_event" and False: #OFF
				logger.debug("try start_event...")
				users = cursor.execute("SELECT username, event, my_wish FROM users WHERE rules >= 0")
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
					runRandomize = True
					while runRandomize:
						rand = True
						stop = False
						randID = random.randint(0, len(users_list)-1)
						for x in users_id_in_use:
							if x == randID:
								rand = False

						#Dont user1 -> user1
						if randID == i and rand == True:
							if i == len(users_list)-1 and i != 0:
								users_list_parallel.append(users_list_parallel[0])
								wish_of_users_parallel.append(wish_of_users_parallel[0])
								users_list_parallel[0] = users_list[i]
								wish_of_users_parallel[0] = wish_of_users[i]
								stop = True
								runRandomize = False
							else:
								rand = False

						if rand == True and stop == False:
							users_list_parallel.append(users_list[randID])
							wish_of_users_parallel.append(wish_of_users[randID])
							users_id_in_use.append(randID)
							runRandomize = False

				for i in range(len(users_list)):
					logger.debug(f"{getIDFromUsername(users_list[i])} -> {getIDFromUsername(users_list_parallel[i])}")
					try:
						bot.send_message(getIDFromUsername(users_list[i]), f"Привет!\nТы тайный ангел для @{users_list_parallel[i]}\nЕго пожелания:\n{wish_of_users_parallel[i]}")
					except Exception:
						logger.warning(f"error sending message to user {getIDFromUsername(users_list[i])}")
					cursor.execute("UPDATE users SET santa_for = ? WHERE username = ?", (users_list_parallel[i], users_list[i]))
					db.commit()


			#SEND MESSAGE TO ALL USERS
			elif message.text[:2] == "**" and rules_level >= config.moderator:
				logger.debug("try send message to all user...")
				text = message.text[2:]
				count = send_level_message(text, config.default, message.from_user.id)
				logger.info(f"user {message.from_user.id} send message to {count} user(s)")
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} пользователям.")

			#SEND MESSAGE TO ALL PRAYERS
			elif message.text[:1] == "*" and rules_level >= config.moderator:
				logger.debug("try send message to all prayer...")
				text = message.text[1:]
				count = 0
				users = cursor.execute("SELECT user_id, state FROM users WHERE rules >= 0")
				for user in users:
					if user[1] == 1 and str(message.from_user.id) != user[0]:
						try:
							bot.send_message(user[0], text)
							count += 1
						except Exception:
							logger.info(f"error sending message to user {user[0]}")
							send_level_message(f"Ошибка! Проверьте пользователя {user[0]}", config.developer, 0)
				logger.info(f"user {message.from_user.id} send message to {count} user(s):")
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} пользователям.")

			#SEND MESSAGE TO MODERATORS AND ADMINS
			elif message.text[0] == "!" and rules_level >= config.admin:
				logger.debug("try send message to all moderators and admins...")
				text = message.text[1:]
				count = send_level_message(text, config.moderator, message.from_user.id)
				logger.info(f"user {message.from_user.id} send message to {count} admin(s)")
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} админам.")


			#CHANGE RULES OF USER
			elif message.text[:9] == "/setRules" and rules_level >= config.admin:
				logger.debug(f"try change access level...")
				try:
					resours = giveNameAndLevel(message.text)
					if resours == False:
						logger.debug("change access level error! (level not found)")
						bot.send_message(message.from_user.id, "Ошибка! \nВведённое значение уровня доступа находится вне диапазона.")
					elif resours[1] == 0:
						logger.debug(f"user {message.from_user.id} tried to set access level 0 to user @{resours[0]}, but there is a /ban command for this")
						bot.send_message(message.from_user.id, "Для блокировки пользователя введите: \n/ban [username]")
					else:
						if check_username(resours[0]) == 1:
							if check_rules(message.from_user.id) >= resours[1]:
								if check_rules(message.from_user.id) >= check_rules(getIDFromUsername(resours[0])):
									logger.debug("changing access level...")
									cursor.execute("UPDATE users SET rules = ? WHERE username = ?", (resours[1], resours[0]))
									db.commit()
									logger.info(f"user {message.from_user.id} set access level {resours[1]} to user {getIDFromUsername(resours[0])}")
									if str(message.from_user.id) != str(getIDFromUsername(resours[0])):
										bot.send_message(message.from_user.id, f"Уровень доступа @{resours[0]} успешно изменён на {resours[1]}")
									if check_rules(getIDFromUsername(resours[0])) < config.developer or check_rules(getIDFromUsername(resours[0])) == config.developer and str(message.from_user.id) == str(getIDFromUsername(resours[0])):
										try:
											bot.send_message(getIDFromUsername(resours[0]), f"Ваш уровень доступа изменён на {resours[1]}")
										except Exception:
											logger.info(f"error sending message to user {getIDFromUsername(resours[0])}")
											send_level_message(f"Ошибка оповещения пользователя! Проверьте пользователя @{resours[0]}", config.developer, 0)
									send_level_message(f"Пользователь @{message.from_user.username} изменил уровень доступа пользователя @{resours[0]} на {resours[1]}", config.developer, message.from_user.id)
								else:
									logger.debug(f"user {message.from_user.id} access level is lower than user @{resours[0]}")
									bot.send_message(message.from_user.id, f"Вы не можете изменить уровень доступа этого пользователя, так как ваш уровень доступа ниже, чем уровень доступа @{resours[0]}")
							else:
								logger.debug(f"user {message.from_user.id} tries to give user {getIDFromUsername(resours[0])} an access level higher than his own")
								bot.send_message(message.from_user.id, f"У вас недостаточно прав для выполнения этой команды.")
						else:
							logger.debug(f"user @{resours[0]} not found!")
							bot.send_message(message.from_user.id, f"Пользователя @{resours[0]} нет в базе данных.")

				except Exception as e:
					logger.debug(e)
					bot.send_message(message.from_user.id, f"Ошибка изменения прав пользователя.\nПроверьте, правильно ли вы ввели команду.")

			#BAN USER
			elif message.text[:4] == "/ban" and rules_level >= config.admin:
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

						if check_username(username) == 1:
							if check_rules(message.from_user.id) >= check_rules(getIDFromUsername(username)):
								logger.debug("changing access level...")
								cursor.execute("UPDATE users SET rules = ?, state = ? WHERE username = ?", (config.ban, 0, username))
								db.commit()
								logger.info(f"user {message.from_user.id} blocked user {getIDFromUsername(username)}")
								if str(message.from_user.id) != getIDFromUsername(username):
									bot.send_message(message.from_user.id, f"Пользователь @{username} успешно заблокирован.")
								if check_rules(getIDFromUsername(username)) != config.developer:
									try:
										bot.send_message(getIDFromUsername(username), f"Вы заблокированы.")
									except Exception:
										logger.info(f"error sending message to user {getIDFromUsername(username)}")
										send_level_message(f"Ошибка оповещения пользователя! Проверьте пользователя @{getIDFromUsername(user[0])} \n({user[0]})", config.developer, 0)
								send_level_message(f"@{message.from_user.username} заблокировал @{username}", config.developer, message.from_user.id)
							else:
								logger.debug(f"user {message.from_user.id} dont have rules for ban user {getIDFromUsername(username)}")
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
				if rules_level >= config.admin:
					bot.send_message(message.from_user.id, f"{config.moderator_help_list}\n{config.admin_help_list}")
				elif rules_level >= config.moderator:
					bot.send_message(message.from_user.id, f"{config.moderator_help_list}")

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
