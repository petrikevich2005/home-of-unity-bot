#HOME OF UNITY BOT
import telebot
import sqlite3
import config
import time
import random
from datetime import *

db = sqlite3.connect("data.db", check_same_thread=False)
cursor = db.cursor()

bot = telebot.TeleBot(config.TOKEN)


#Log
def log(text):
	print(f"[{datetime.now().strftime('%d.%m.%Y | %H:%M')}]\n{text}\n\n")
	file = open(f'logs/{datetime.now().date()}.txt', 'a')
	file.write(f"[{datetime.now()}]\n{text}\n\n")

#Give username and level rules
def giveNameAndLevel(text):
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
	log("random text...")
	texts = cursor.execute("SELECT text FROM texts")
	texts_list = []
	for text in texts:
		texts_list.append(text[0])
	randomTextID = random.randint(0, len(texts_list)-1)
	return str(texts_list[randomTextID])

#Notifications of baned user try use bot
def be_baned(user_id, username, command):
	log(f"{user_id} not have rules for command \"{command}\"")
	send_level_message(f"@{username} попытался использовать команду \"{command}\" находясь в состоянии блокировки.", config.developer, 0)
	bot.send_message(user_id, f"У вас недостаточно прав для использования этой команды.\nПожалуйста, обратитесь к лидеру или дождитесь сообщения от администратора.")

#Check rules of user
def check_rules(user_id):
	log("check rules level...")
	users = cursor.execute("SELECT user_id, rules FROM users")
	for user in users:
		if user[0] == str(user_id):
			return user[1]

#Check user id
def check_user_id(user_id):
	log("check user id...")
	users = cursor.execute("SELECT user_id FROM users")
	for user in users:
		if user[0] == str(user_id):
			return 1

#Check username
def check_username(username):
	log("check username...")
	users = cursor.execute("SELECT username FROM users")
	for user in users:
		if user[0] == str(username):
			return 1

#Get user id from username
def getIDFromUsername(username):
	log("get id from username...")
	users= cursor.execute("SELECT username, user_id FROM users")
	for user in users:
		if user[0] == username:
			return user[1]

#Send message
def send_level_message(text, necessary_rules, sender):
	log("send level message...")
	count = 0
	users = cursor.execute("SELECT user_id FROM users WHERE rules >= 0")
	for user in users:
		if check_rules(user[0]) >= necessary_rules and user[0] != str(sender):
			try:
				bot.send_message(user[0], text)
				count += 1
			except Exception:
				log(f"Except in \"send_level_message\"\nCheck user {user[0]}")
	log(f"Send level message to {count} user(s):\n{text}")
	return count


#Command start
@bot.message_handler(commands=['start'])
def start(message):
	log("start try...")
	try:
		if check_user_id(message.from_user.id) != 1:
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			log(f"{message.from_user.id} appended to data base")
			send_level_message(f"@{message.from_user.username} добавлен(а) в базу данных.", config.admin, message.from_user.id)
		if check_rules(message.from_user.id) >= config.default:
			bot.send_message(message.from_user.id, config.start_text)
		else:
			be_baned(message.from_user.id, message.from_user.username, "start")
	except Exception:
		log("Except in command \"start\"")


#Added to prays lists
@bot.message_handler(commands=['prays_lists'])
def change_state(message):
	log("change_state try...")
	try:
		if check_user_id(message.from_user.id) != 1:
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			log(f"{message.from_user.id} appended to data base")

		if check_rules(message.from_user.id) >= config.default:
			if check_username(message.from_user.username) == 1 and message.from_user.username != None:
				users = cursor.execute("SELECT user_id, state FROM users WHERE rules >= 0")
				for user in users:
					if user[0] == str(message.from_user.id):
						log(f"{user[0]} try change state...")
						state = 0
						if user[1] == 1:
							log(f"@{message.from_user.username} has been removed from prays lists.")
							send_level_message(f"@{message.from_user.username} исключил(а) себя из молитвенных листочков.", config.admin, message.from_user.id)
							bot.send_message(user[0], "Вы исключены из молитвенных листочков.")
						else:
							state = 1
							log(f"{user[0]} added to prays lists")
							send_level_message(f"@{message.from_user.username} добавил(а) себя в молитвенные листочки.", config.admin, message.from_user.id)
							bot.send_message(user[0], "Вы добавлены в молитвенные листочки.")
						cursor.execute("UPDATE users SET state = ? WHERE user_id = ?", (state, user[0]))
						db.commit()
			else:
				log(f"{message.from_user.id} dont have username.")
				bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")
		else:
			be_baned(message.from_user.id, message.from_user.username, "prays_lists")
	except Exception:
		log("Except in command \"prays_lists\"")


#Added event
@bot.message_handler(commands=['event'])
def change_event_state(message):
	log("change_event_state try...")
	try:
		if check_user_id(message.from_user.id) != 1:
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			log(f"{message.from_user.id} appended to data base")

		if check_rules(message.from_user.id) >= config.default:
			if check_username(message.from_user.username) == 1 and message.from_user.username != None:
				users = cursor.execute("SELECT user_id, event FROM users WHERE rules >= 0")
				for user in users:
					if user[0] == str(message.from_user.id):
						log(f"{user[0]} try change event_state...")
						bot.send_message(message.from_user.id, "Регистрация не доступна.")
#						state = 0
#						if user[1] == 1:
#							log(f"@{message.from_user.username} has been removed from event lists.")
#							bot.send_message(user[0], "Вы больше не тайный ангел.")
#						else:
#							state = 1
#							log(f"{user[0]} added to event")
#							send_level_message(f"@{message.from_user.username} учавствует в дополнительном событии.", config.admin, message.from_user.id)
#							bot.send_message(user[0], "Теперь вы тайный ангел.")
#						cursor.execute("UPDATE users SET event = ? WHERE user_id = ?", (state, user[0]))
#						db.commit()
			else:
				log(f"{message.from_user.id} dont have username.")
				bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")
		else:
			be_baned(message.from_user.id, message.from_user.username, "event")
	except Exception:
		log("Except in command \"change_event\"")


#Give developer rules
@bot.message_handler(commands=['key'])
def giveRulesDeveloper(message):
	try:
		cursor.execute("UPDATE users SET rules = ? WHERE user_id = ?", (config.developer, message.from_user.id))
		db.commit()
		log(f"{message.from_user.id} give rules of developer")
		bot.send_message(message.from_user.id, "Ваши права изменены на \"Developer\".")
	except Exception:
		log("Except in command \"giveRulesCreator\"")


#Send info
@bot.message_handler(commands=['info'])
def send_info(message):
	log("info try...")
	try:
		if check_user_id(message.from_user.id) != 1:
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			log(f"{message.from_user.id} appended to data base")

		if check_rules(message.from_user.id) >= config.default:
			log(f"{message.from_user.username} send command \"info\"")
			bot.send_message(message.from_user.id, config.info)
		else:
			be_baned(message.from_user.id, message.from_user.username, "info")
	except Exception:
		log("Except in command \"info\"")


#Update data of user in Data Base
@bot.message_handler(commands=['update'])
def update_data(message):
	try:
		if check_user_id(message.from_user.id) != 1:
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			log(f"{message.from_user.id} appended to data base")

		log("update try...")
		cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (message.from_user.username, message.from_user.id))
		db.commit()
		log(f"{message.from_user.id} update data...")
		send_level_message(f"@{message.from_user.username} обновил(а) своё имя пользователя.", config.developer, message.from_user.id)
		bot.send_message(message.from_user.id, "Ваше имя пользователя обновлено.")
	except Exception:
		log("Except in command \"update\"")


#Who i am?
@bot.message_handler(commands=['who'])
def who_i_am(message):
	log("who i am try...")
	try:
		if check_user_id(message.from_user.id) != 1:
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			log(f"{message.from_user.id} appended to data base")

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
			log(f"Rules level of user \"{rules}\"")
			bot.send_message(message.from_user.id, f"Ваш уровень доступа относится к категории \"{rules}\"")
		else:
			log("Not found!\nError in command \"/who\"")
			bot.send_message(message.from_user.id, "Ошибка.\nВаш уровень доступа не относится ни к одной из категорий.")
	except Exception:
		log("Except in command \"who\"")


#Other
@bot.message_handler(content_types=['text'])
def text(message):
	log("text try...")
	try:
		if check_user_id(message.from_user.id) != 1:
			cursor.execute(f"INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (message.from_user.id, message.chat.id, message.from_user.username, 0, config.default, "empty", 0, "empty", "empty"))
			db.commit()
			log(f"{message.from_user.id} appended to data base")


		#CHECK USERNAME
		if check_username(message.from_user.username) == 1 and message.from_user.username != None:
			rules_level = check_rules(message.from_user.id)


			#CHECK BAN LEVEL
			if rules_level < config.default:
				be_baned(message.from_user.id, message.from_user.username, "text")

			#SET MY WISH
#			elif message.text[:8] == "/my_wish" and rules_level >= config.default:
#				text = message.text[9:]
#				users = cursor.execute("SELECT user_id, my_wish FROM users WHERE rules >= 0")
#				for user in users:
#					if str(user[0]) == str(message.from_user.id):
#						cursor.execute("UPDATE users SET my_wish = ? WHERE user_id = ?", (text, message.from_user.id))
#						db.commit()
#						log(f"Set wish for @{message.from_user.username}")
#						bot.send_message(message.from_user.id, f"Текст успешно сохранён")


			#RANDOMIZE USERS FOR PRAYS LISTS
			elif message.text == "/randomize" and rules_level >= config.moderator:
				log("randomize...")
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
					log(f"{prayers_list[i]} -> {prayers_list_parallel[i]}")
					try:
						bot.send_message(getIDFromUsername(prayers_list[i]), f"Привет!\nНа этой неделе ты молишься за @{prayers_list_parallel[i]}\n{randomText()}")
					except Exception:
						log(f"Except in \"send_message\" in randomize\nCheck user {getIDFromUsername(prayers_list[i])}")
					cursor.execute("UPDATE users SET prays_friend = ? WHERE username = ?", (prayers_list_parallel[i], prayers_list[i]))
					db.commit()


			#START EVENT (RANDOMIZE)
			elif message.text == "/start_event" and rules_level >= 10: #НЕДОСТУПНО ПО УРОВНЮ ДОСТУПА
				log("starting event...")
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
					log(f"{users_list[i]} -> {users_list_parallel[i]}")
					try:
						bot.send_message(getIDFromUsername(users_list[i]), f"Привет!\nТы тайный ангел для @{users_list_parallel[i]}\nЕго пожелания:\n{wish_of_users_parallel[i]}")
					except Exception:
						log(f"Except in \"send_message\" in randomize\nCheck user {getIDFromUsername(users_list[i])}")
					cursor.execute("UPDATE users SET santa_for = ? WHERE username = ?", (users_list_parallel[i], users_list[i]))
					db.commit()


			#SEND MESSAGE FOR ALL USERS
			elif message.text[:2] == "**" and rules_level >= config.moderator:
				log(f"Send message for all user...")
				text = message.text[2:]
				count = send_level_message(text, config.default, message.from_user.id)
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} пользователям.")

			#SEND MESSAGE FOR ALL PRAYERS
			elif message.text[:1] == "*" and rules_level >= config.moderator:
				log(f"Send message for all prayer...")
				text = message.text[1:]
				count = 0
				users = cursor.execute("SELECT user_id, state FROM users WHERE rules >= 0")
				for user in users:
					if user[1] == 1 and str(message.from_user.id) != user[0]:
						try:
							bot.send_message(user[0], text)
							count += 1
						except Exception:
							log(f"Error send message to {user[1]}")
							send_level_message(f"Ошибка! Проверьте пользователя @{getIDFromUsername(user[0])} \n({user[0]})", config.developer, 0)
				log(f"Send level message to {count} user(s):\n{text}")
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} пользователям.")

			#SEND MESSAGE FOR MODERATORS AND ADMINS
			elif message.text[0] == "!" and rules_level >= config.admin:
				text = message.text[1:]
				count = send_level_message(text, config.moderator, message.from_user.id)
				bot.send_message(message.from_user.id, f"Сообщение отправлено {count} пользователям.")


			#CHANGE RULES OF USER
			elif message.text[:9] == "/setRules" and rules_level >= config.admin:
				try:
					resours = giveNameAndLevel(message.text)
					if resours == False:
						log("Change rules error. Level not found.")
						bot.send_message(message.from_user.id, "Ошибка. \nВведённое значение уровня доступа находится вне допустимого диапазона.")
					elif resours[1] == 0:
						log("For block user enter: /ban [username]")
						bot.send_message(message.from_user.id, "Для блокировки пользователя введите: \n/ban [username]")
					else:
						if check_username(resours[0]) == 1:
							if check_rules(message.from_user.id) >= resours[1]:
								if check_rules(message.from_user.id) >= check_rules(getIDFromUsername(resours[0])):
									cursor.execute("UPDATE users SET rules = ? WHERE username = ?", (resours[1], resours[0]))
									db.commit()
									log(f"Admin @{message.from_user.username} set rules level for @{resours[0]} {resours[1]}")
									if str(message.from_user.id) != str(getIDFromUsername(resours[0])):
										bot.send_message(message.from_user.id, f"Уровень доступа @{resours[0]} успешно изменён на {resours[1]}")
									if check_rules(getIDFromUsername(resours[0])) < config.developer or check_rules(getIDFromUsername(resours[0])) == config.developer and str(message.from_user.id) == str(getIDFromUsername(resours[0])):
										try:
											bot.send_message(getIDFromUsername(resours[0]), f"Ваш уровень доступа изменён на {resours[1]}")
										except Exception:
											send_level_message(f"Ошибка оповещения пользователя! Проверьте пользователя @{getIDFromUsername(user[0])} \n({user[0]})", config.developer, 0)
									send_level_message(f"@{message.from_user.username} изменил уровень доступа @{resours[0]} на {resours[1]}", config.developer, message.from_user.id)
								else:
									log(f"Rules level of user @{message.from_user.username} < @{resours[0]}")
									bot.send_message(message.from_user.id, f"Вы не можете изменить уровень доступа этого пользователя, так как ваш уровень доступа ниже, чем уровень доступа @{resours[0]}")
							else:
								log(f"User @{message.from_user.username} dont have rules for give {resours[1]} rules level for @{resours[0]}")
								bot.send_message(message.from_user.id, f"У вас недостаточно прав для выдачи пользователю @{resours[0]} такого уровня доступа.")
						else:
							log(f"User @{resours[0]} not found.")
							bot.send_message(message.from_user.id, f"Пользователя @{resours[0]} нет в базе данных.")

				except Exception:
					log("Ошибка изменения прав пользователя.\nПроверьте, правильно ли вы ввели команду.")
					bot.send_message(message.from_user.id, f"Ошибка изменения прав пользователя.\nПроверьте, правильно ли вы ввели команду.")

			#BAN USER
			elif message.text[:4] == "/ban" and rules_level >= config.admin:
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
								cursor.execute("UPDATE users SET rules = ?, state = ? WHERE username = ?", (config.ban, 0, username))
								db.commit()
								log(f"@{message.from_user.username} baned user @{username}")
								if str(message.from_user.id) != getIDFromUsername(username):
									bot.send_message(message.from_user.id, f"Пользователь @{username} успешно заблокирован.")
								if check_rules(getIDFromUsername(username)) != config.developer:
									try:
										bot.send_message(getIDFromUsername(username), f"Вы заблокированы.")
									except Exception:
										send_level_message(f"Ошибка оповещения пользователя! Проверьте пользователя @{getIDFromUsername(user[0])} \n({user[0]})", config.developer, 0)
								send_level_message(f"@{message.from_user.username} заблокировал @{username}", config.developer, message.from_user.id)
							else:
								log(f"User @{message.from_user.username} dont have rules for ban user @{username}")
								bot.send_message(message.from_user.id, f"У вас недостаточно прав для блокировки пользователя @{username}")
						else:
							log(f"User @{username} not found!")
							bot.send_message(message.from_user.id, f"Пользователя @{username} нет в базе данных.")
					else:
						log("Error baned user!\n2")
						bot.send_message(message.from_user.id, "Ошибка блокировки пользователя.\nПроверьте, правильно ли вы ввели команду.\nПосле \"/ban\" должен стоять пробел.")
				except Exception:
					log("Error baned user!")
					bot.send_message(message.from_user.id, "Ошибка блокировки пользователя.\nПроверьте, правильно ли вы ввели команду.")


			#SEND HELP LIST
			elif message.text == "/help":
				if rules_level >= config.admin:
					log(f"{message.from_user.id} send help")
					bot.send_message(message.from_user.id, f"{config.moderator_help_list}\n{config.admin_help_list}")
				elif rules_level >= config.moderator:
					log(f"{message.from_user.id} send help")
					bot.send_message(message.from_user.id, f"{config.moderator_help_list}")

		else:
			log(f"{message.from_user.id} dont have username.")
			bot.send_message(message.from_user.id, f"Извините, но для выполнения этой команды необходимо наличие username.\nПожалуйста, установите свой username в настройках Telegram, после чего отправьте команду /update")


	except Exception:
		log("Except in text")


#RUN
runBot = True
while runBot:
	log("Run bot...")
	try:
		bot.polling()
	except Exception:
		log("RUN BOT EXCEPT!")
		time.sleep(3)

#CLOSE DATABASE
db.close()
