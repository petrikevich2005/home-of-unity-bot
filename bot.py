# HOME OF UNITY BOT
import os
import random
import sqlite3
from time import sleep

import config

from dotenv import load_dotenv

from roles import Roles

import telebot

import user_utils

import utils


read = load_dotenv(".env")
token = os.getenv("TOKEN")
print(read, token)

bot = telebot.TeleBot(token)

logger = utils.get_logger(__name__)


# adding data of user to database
def add_to_database(user_id, username):
    logger.debug("adding to the database...")
    with sqlite3.connect("data.db") as cursor:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, "empty", username, 0, Roles.DEFAULT.value, "empty", 0, "empty", "empty", 0),
        )
    logger.info(f"user {user_id} added to the database")
    send_message_to_specific_category_users(
        f"Пользователь @{username} добавлен(а) в базу данных.",
        Roles.ADMIN.value,
        user_id,
    )


# give username and category of user
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

        if level >= Roles.DEFAULT.value and level <= Roles.DEV.value:
            username = "".join(username)
            return [username, level]
        else:
            return False
    else:
        return False


# get random text from the databse
def get_random_text():
    with sqlite3.connect("data.db") as cursor:
        texts = cursor.execute("SELECT text FROM texts")
    texts_list = []
    for text in texts:
        texts_list.append(text[0])
    random_text_id = random.randint(0, len(texts_list) - 1)
    return str(texts_list[random_text_id])


# notifications of baned user try use bot
def is_baned(user_id, command):
    with sqlite3.connect("data.db") as cursor:
        ban = cursor.execute("SELECT ban FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
    if ban:
        logger.info(f'baned user {user_id} try use command "{command}"')
        bot.send_message(
            user_id,
            """
			У вас недостаточно прав для использования этой команды.
			Пожалуйста, обратитесь к лидеру или ответственному за бота.
		""",
        )
    return ban


# check role of user
def get_user_category(user_id):
    with sqlite3.connect("data.db") as cursor:
        info = cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if info is None:
        logger.debug(f"not found role of user {user_id}")
        return False
    else:
        return info[0]


# get user id from username
def get_id_using_username(username):
    with sqlite3.connect("data.db") as cursor:
        info = cursor.execute(
            "SELECT user_id FROM users WHERE username = ?", (username,)
        ).fetchone()
    if info is None:
        logger.debug(f"not found user @{username}")
        return False
    else:
        return info[0]


# send a message to a specific category of users
def send_message_to_specific_category_users(text, necessary_role, sender):
    count = 0
    with sqlite3.connect("data.db") as cursor:
        users = cursor.execute("SELECT user_id FROM users WHERE role >= ?", (necessary_role,))
    for user in users:
        if user[0] != str(sender):
            try:
                bot.send_message(user[0], text)
                count += 1
            except Exception:
                logger.info(f"error sending message to user {user[0]}")
    logger.debug(f"send a message to a specifical category to {count} user(s)")
    return count


# command start
@bot.message_handler(commands=["start"])
def start(message):
    logger.debug(f'user {message.from_user.id} tried use command "start"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        if is_baned(message.from_user.id, "start"):
            bot.send_message(message.from_user.id, config.START_TEXT)
    except Exception as e:
        logger.error(e)


# adding to prays lists
@bot.message_handler(commands=["prays_lists"])
def change_state(message):
    logger.debug(f'user {message.from_user.id} tried use command "prays_lists"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        if not is_baned(message.from_user.id, "prays_lists"):
            if (
                user_utils.check_username(message.from_user.username)
                and message.from_user.username is not None
            ):
                with sqlite3.connect("data.db") as cursor:
                    users = cursor.execute(
                        "SELECT user_id, state FROM users WHERE role >= ?",
                        (Roles.DEFAULT.value,),
                    )
                for user in users:
                    if user[0] == str(message.from_user.id):
                        logger.debug("try change state...")
                        state = 0
                        if user[1] == 1:
                            logger.info(f"user {user[0]} has been removed from prays lists")
                            send_message_to_specific_category_users(
                                f"Пользователь @{message.from_user.username} исключил(а) себя из молитвенных листочков.",
                                Roles.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], "Вы исключены из молитвенных листочков.")
                        else:
                            state = 1
                            logger.info(f"user {user[0]} added to prays lists")
                            send_message_to_specific_category_users(
                                f"Пользователь @{message.from_user.username} добавил(а) себя в молитвенные листочки.",
                                Roles.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], "Вы добавлены в молитвенные листочки.")
                        with sqlite3.connect("data.db") as cursor:
                            cursor.execute(
                                "UPDATE users SET state = ? WHERE user_id = ?", (state, user[0])
                            )
            else:
                logger.debug(f"{message.from_user.id} dont have username")
                bot.send_message(
                    message.from_user.id,
                    """
					Извините, но для выполнения этой команды необходимо наличие username.
					Пожалуйста, установите свой username в настройках Telegram, после чего
					отправьте команду /update
				""",
                )
    except Exception as e:
        logger.error(e)


# added event
@bot.message_handler(commands=["event"])
def change_event_state(message):
    logger.debug(f'user {message.from_user.id} tried use command "event"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        if not is_baned(message.from_user.id, "event"):
            bot.send_message(message.from_user.id, "Регистрация недоступна.")
            if (
                user_utils.check_username(message.from_user.username)
                and message.from_user.username is not None
                and False
            ):
                with sqlite3.connect("data.db") as cursor:
                    users = cursor.execute(
                        "SELECT user_id, event FROM users WHERE role >= ?",
                        (Roles.DEFAULT.value,),
                    )
                for user in users:
                    if user[0] == str(message.from_user.id):
                        logger.debug("try change event_state...")
                        state = 0
                        if user[1] == 1:
                            logger.info(f"user {user[0]} has been removed from event lists")
                            send_message_to_specific_category_users(
                                f"Пользователь @{message.from_user.username} не учавствует в дополнительном событии.",
                                Roles.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], "Вы больше не тайный ангел.")
                        else:
                            state = 1
                            logger.info(f"user {user[0]} added to event")
                            send_message_to_specific_category_users(
                                f"Пользователь @{message.from_user.username} учавствует в дополнительном событии.",
                                Roles.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], "Теперь вы тайный ангел.")
                        with sqlite3.connect("data.db") as cursor:
                            cursor.execute(
                                "UPDATE users SET event = ? WHERE user_id = ?", (state, user[0])
                            )
            else:
                logger.debug(f"user {message.from_user.id} dont have username")
                bot.send_message(
                    message.from_user.id,
                    """Извините, но для выполнения этой команды необходимо наличие username.
					Пожалуйста, установите свой username в настройках Telegram, после чего
					отправьте команду /update""",
                )
    except Exception as e:
        logger.error(e)


# set the user to developer category
@bot.message_handler(commands=[os.getenv("KEY")])
def set_the_user_to_developer_category(message):
    logger.debug(f"user {message.from_user.id} is trying to get developer role...")
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        with sqlite3.connect("data.db") as cursor:
            cursor.execute(
                "UPDATE users SET role = ? WHERE user_id = ?",
                (Roles.DEV.value, message.from_user.id),
            )
        logger.info(f"user {message.from_user.id} has been granted developer rights")
        bot.send_message(message.from_user.id, f"Ваши права изменены на '{Roles.DEV.name}'")
        send_message_to_specific_category_users(
            f"Пользователь @{message.from_user.username} получил права разработчика при помощи ключа.",
            Roles.DEV.value,
            message.from_user.id,
        )
    except Exception as e:
        logger.error(e)


# send the user information about the bot
@bot.message_handler(commands=["info"])
def send_info(message):
    logger.debug(f'user {message.from_user.id} tried use command "info"...')

    if not user_utils.check_user_id(message.from_user.id):
        add_to_database(message.from_user.id, message.from_user.username)

    if not is_baned(message.from_user.id, "info"):
        logger.debug(f"bot information was successfully sent to user {message.from_user.id}")
        bot.send_message(message.from_user.id, config.INFO)


# update data of user in database
@bot.message_handler(commands=["update"])
def update_user_data(message):
    logger.debug(f"user {message.from_user.id} is trying to update his username...")
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        else:
            logger.debug("updating...")
            with sqlite3.connect("data.db") as cursor:
                cursor.execute(
                    "UPDATE users SET username = ? WHERE user_id = ?",
                    (message.from_user.username, message.from_user.id),
                )
            logger.debug(f"username {message.from_user.id} update completed successfully")
            send_message_to_specific_category_users(
                f"Пользователь @{message.from_user.username} успешно обновил(а) своё имя пользователя.",
                Roles.DEV.value,
                message.from_user.id,
            )
            bot.send_message(message.from_user.id, "Ваше имя пользователя обновлено.")
    except Exception as e:
        logger.error(e)


# send to user his role
@bot.message_handler(commands=["who"])
def who_i_am(message):
    logger.debug(f'user {message.from_user.id} is trying to use command "who"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        complete = True
        role = get_user_category(message.from_user.id)
        if role == Roles.DEFAULT.value:
            role = Roles.DEFAULT.name
        elif role == Roles.MOD.value:
            role = Roles.MOD.name
        elif role == Roles.ADMIN.value:
            role = Roles.ADMIN.name
        elif role == Roles.DEV.value:
            role = Roles.DEV.name
        else:
            complete = False

        if complete:
            logger.debug("the command completed successfully!")
            bot.send_message(message.from_user.id, f'Ваша роль: "{role}"')
        else:
            logger.warning(
                f"not found role of user {message.from_user.id}! (@{message.from_user.username})"
            )
            bot.send_message(
                message.from_user.id,
                """
				Ошибка!
				Ваша роль неопознанна.
				Пожалуйста, обратитесь к лидеру или ответственному за бота.
				""",
            )
    except Exception as e:
        logger.error(e)


# other
@bot.message_handler(content_types=["text"])
def text(message):
    logger.debug(f'user {message.from_user.id} is trying to use command "text"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        # CHECK USERNAME
        if (
            user_utils.check_username(message.from_user.username)
            and message.from_user.username is not None
        ):
            role = get_user_category(message.from_user.id)

            # CHECK BAN LEVEL
            if not is_baned(message.from_user.id, "text"):
                # SET MY WISH
                if message.text[:8] == "/my_wish" and False:  # OFF
                    logger.debug("try set wish...")
                    text = message.text[9:]
                    with sqlite3.connect("data.db") as cursor:
                        cursor.execute(
                            "UPDATE users SET my_wish = ? WHERE user_id = ?",
                            (text, message.from_user.id),
                        )
                    logger.debug(f"set wish for {message.from_user.id}")
                    bot.send_message(message.from_user.id, "Текст успешно сохранён")

                # RANDOMIZE USERS FOR PRAYS LISTS
                elif message.text == "/randomize" and role >= Roles.MOD.value:
                    logger.debug("try randomize...")
                    with sqlite3.connect("data.db") as cursor:
                        users = cursor.execute(
                            "SELECT username, state FROM users WHERE role >= ?",
                            (Roles.DEFAULT.value,),
                        )
                    prayers_list = []
                    prayers_list_parallel = []
                    users_id_in_use = []

                    # Get list "only prayers"
                    for user in users:
                        if user[1] == 1:
                            prayers_list.append(user[0])

                    for i in range(len(prayers_list)):
                        run_randomize = True
                        while run_randomize:
                            rand = True
                            stop = False
                            random_id = random.randint(0, len(prayers_list) - 1)
                            for id_n in users_id_in_use:
                                if id_n == random_id:
                                    rand = False

                            # Dont user1 -> user1
                            if random_id == i and rand:
                                if i == len(prayers_list) - 1 and i != 0:
                                    prayers_list_parallel.append(prayers_list_parallel[0])
                                    prayers_list_parallel[0] = prayers_list[i]
                                    stop = True
                                    run_randomize = False
                                else:
                                    rand = False

                            if rand and not stop:
                                prayers_list_parallel.append(prayers_list[random_id])
                                users_id_in_use.append(random_id)
                                run_randomize = False

                    for i in range(len(prayers_list)):
                        logger.debug(
                            f"{get_id_using_username(prayers_list[i])} ->"
                            + f"{get_id_using_username(prayers_list_parallel[i])}",
                        )
                        try:
                            bot.send_message(
                                get_id_using_username(prayers_list[i]),
                                f"""
								Привет!
								На этой неделе ты молишься за @{prayers_list_parallel[i]}
								{get_random_text()}
								""",
                            )
                        except Exception:
                            logger.warning(
                                f"error sending message to user {get_id_using_username(prayers_list[i])}"
                            )
                        with sqlite3.connect("data.db") as cursor:
                            cursor.execute(
                                "UPDATE users SET prays_friend = ? WHERE username = ?",
                                (prayers_list_parallel[i], prayers_list[i]),
                            )

                # START EVENT (RANDOMIZE)
                elif message.text == "/start_event" and False:  # OFF
                    logger.debug("try start_event...")
                    with sqlite3.connect("data.db") as cursor:
                        users = cursor.execute(
                            "SELECT username, event, my_wish FROM users WHERE role >= ?",
                            (Roles.DEFAULT.value,),
                        )
                    users_list = []
                    users_list_parallel = []
                    users_id_in_use = []
                    wish_of_users = []
                    wish_of_users_parallel = []

                    # Get list "only angels"
                    for user in users:
                        if user[1] == 1:
                            users_list.append(user[0])
                            wish_of_users.append(user[2])

                    for i in range(len(users_list)):
                        run_randomize = True
                        while run_randomize:
                            rand = True
                            stop = False
                            random_id = random.randint(0, len(users_list) - 1)
                            for id_n in users_id_in_use:
                                if id_n == random_id:
                                    rand = False

                            # Dont user1 -> user1
                            if random_id == i and rand:
                                if i == len(users_list) - 1 and i != 0:
                                    users_list_parallel.append(users_list_parallel[0])
                                    wish_of_users_parallel.append(wish_of_users_parallel[0])
                                    users_list_parallel[0] = users_list[i]
                                    wish_of_users_parallel[0] = wish_of_users[i]
                                    stop = True
                                    run_randomize = False
                                else:
                                    rand = False

                            if rand and not stop:
                                users_list_parallel.append(users_list[random_id])
                                wish_of_users_parallel.append(wish_of_users[random_id])
                                users_id_in_use.append(random_id)
                                run_randomize = False

                    for i in range(len(users_list)):
                        logger.debug(
                            f"{get_id_using_username(users_list[i])} ->"
                            + f"{get_id_using_username(users_list_parallel[i])}",
                        )
                        try:
                            bot.send_message(
                                get_id_using_username(users_list[i]),
                                f"""
								Привет!
								Ты тайный ангел для @{users_list_parallel[i]}
								Его пожелания:
								{wish_of_users_parallel[i]}
								""",
                            )
                        except Exception:
                            logger.warning(
                                f"error sending message to user {get_id_using_username(users_list[i])}"
                            )
                        with sqlite3.connect("data.db") as cursor:
                            cursor.execute(
                                "UPDATE users SET santa_for = ? WHERE username = ?",
                                (users_list_parallel[i], users_list[i]),
                            )

                # SEND MESSAGE TO ALL USERS
                elif message.text[:2] == "**" and role >= Roles.MOD.value:
                    logger.debug("try send message to all user...")
                    text = message.text[2:]
                    count = send_message_to_specific_category_users(
                        text,
                        Roles.DEFAULT.value,
                        message.from_user.id,
                    )
                    logger.info(f"user {message.from_user.id} send message to {count} user(s)")
                    bot.send_message(
                        message.from_user.id, f"Сообщение отправлено {count} пользователям."
                    )

                # SEND MESSAGE TO ALL PRAYERS
                elif message.text[:1] == "*" and role >= Roles.MOD.value:
                    logger.debug("try send message to all prayer...")
                    text = message.text[1:]
                    count = 0
                    with sqlite3.connect("data.db") as cursor:
                        users = cursor.execute(
                            "SELECT user_id, state FROM users WHERE role >= ?",
                            (Roles.DEFAULT.value,),
                        )
                    for user in users:
                        if user[1] == 1 and str(message.from_user.id) != user[0]:
                            try:
                                bot.send_message(user[0], text)
                                count += 1
                            except Exception:
                                logger.info(f"error sending message to user {user[0]}")
                                send_message_to_specific_category_users(
                                    f"Ошибка!\nПроверьте пользователя {user[0]}",
                                    Roles.DEV.value,
                                    0,
                                )
                    logger.info(f"user {message.from_user.id} send message to {count} user(s):")
                    bot.send_message(
                        message.from_user.id, f"Сообщение отправлено {count} пользователям."
                    )

                # SEND MESSAGE TO MODERATORS AND ADMINS
                elif message.text[0] == "!" and role >= Roles.ADMIN.value:
                    logger.debug("try send message to all moderators and admins...")
                    text = message.text[1:]
                    count = send_message_to_specific_category_users(
                        text, Roles.MOD.value, message.from_user.id
                    )
                    logger.info(f"user {message.from_user.id} send message to {count} admin(s)")
                    bot.send_message(message.from_user.id, f"Сообщение отправлено {count} админам.")

                # CHANGE ROLE OF USER
                elif message.text[:9] == "/setRole" and role >= Roles.ADMIN.value:
                    logger.debug("try change role...")
                    try:
                        resours = select_name_and_category(message.text)
                        if not resours:
                            logger.debug("change role error! (level not found)")
                            bot.send_message(
                                message.from_user.id,
                                """
								Ошибка!
								Введённое значение уровня доступа находится вне диапазона.
								""",
                            )
                        else:
                            if user_utils.check_username(resours[0]):
                                if get_user_category(message.from_user.id) >= resours[1]:
                                    if get_user_category(message.from_user.id) >= get_user_category(
                                        get_id_using_username(resours[0])
                                    ):
                                        logger.debug("changing role...")
                                        with sqlite3.connect("data.db") as cursor:
                                            cursor.execute(
                                                "UPDATE users SET role = ? WHERE username = ?",
                                                (resours[1], resours[0]),
                                            )
                                        logger.info(
                                            f"user {message.from_user.id} set role {resours[1]}"
                                            + f"to user {get_id_using_username(resours[0])}",
                                        )
                                        if str(message.from_user.id) != str(
                                            get_id_using_username(resours[0])
                                        ):
                                            bot.send_message(
                                                message.from_user.id,
                                                f"Уровень доступа @{resours[0]} успешно изменён на {resours[1]}",
                                            )
                                        if (
                                            get_user_category(get_id_using_username(resours[0]))
                                            < Roles.DEV.value
                                            or get_user_category(get_id_using_username(resours[0]))
                                            == Roles.DEV.value
                                            and str(message.from_user.id)
                                            == str(get_id_using_username(resours[0]))
                                        ):
                                            try:
                                                bot.send_message(
                                                    get_id_using_username(resours[0]),
                                                    f"Ваш уровень доступа изменён на {resours[1]}",
                                                )
                                            except Exception:
                                                logger.info(
                                                    f"error sending message to user {get_id_using_username(resours[0])}"
                                                )
                                                send_message_to_specific_category_users(
                                                    f"Ошибка оповещения пользователя! Проверьте пользователя @{resours[0]}",
                                                    Roles.DEV.value,
                                                    0,
                                                )
                                        send_message_to_specific_category_users(
                                            f"Пользователь @{message.from_user.username} изменил уровень доступа пользователя"
                                            + f"@{resours[0]} на {resours[1]}",
                                            Roles.DEV.value,
                                            message.from_user.id,
                                        )
                                    else:
                                        logger.debug(
                                            f"user {message.from_user.id} role is lower than user @{resours[0]}"
                                        )
                                        bot.send_message(
                                            message.from_user.id,
                                            "Вы не можете изменить уровень доступа этого пользователя,"
                                            + f"так как ваш уровень доступа ниже, чем уровень доступа @{resours[0]}",
                                        )
                                else:
                                    logger.debug(
                                        f"user {message.from_user.id} tries to give user {get_id_using_username(resours[0])}"
                                        + "an role higher than his own",
                                    )
                                    bot.send_message(
                                        message.from_user.id,
                                        "У вас недостаточно прав для выполнения этой команды.",
                                    )
                            else:
                                logger.debug(f"user @{resours[0]} not found!")
                                bot.send_message(
                                    message.from_user.id,
                                    f"Пользователя @{resours[0]} нет в базе данных.",
                                )

                    except Exception as e:
                        logger.debug(e)
                        bot.send_message(
                            message.from_user.id,
                            """
							Ошибка изменения прав пользователя.
							Проверьте, правильно ли вы ввели команду.
							""",
                        )

                # BAN USER
                elif message.text[:4] == "/ban" and role >= Roles.ADMIN.value:
                    logger.debug("try ban user...")
                    try:
                        if message.text[4] == " ":
                            text = message.text[5:]
                            username = []

                            for i in text:
                                if i != " ":
                                    username.append(i)
                                elif i == " ":
                                    break

                            username = "".join(username)

                            if user_utils.check_username(username):
                                if get_user_category(message.from_user.id) >= get_user_category(
                                    get_id_using_username(username)
                                ):
                                    logger.debug("blocking...")
                                    with sqlite3.connect("data.db") as cursor:
                                        cursor.execute(
                                            "UPDATE users SET ban = ?, state = ? WHERE username = ?",
                                            (1, 0, username),
                                        )
                                    logger.info(
                                        f"user {message.from_user.id} blocked user {get_id_using_username(username)}"
                                    )
                                    if str(message.from_user.id) != get_id_using_username(username):
                                        bot.send_message(
                                            message.from_user.id,
                                            f"Пользователь @{username} успешно заблокирован.",
                                        )
                                    if (
                                        get_user_category(get_id_using_username(username))
                                        != Roles.DEV.value
                                    ):
                                        try:
                                            bot.send_message(
                                                get_id_using_username(username), "Вы заблокированы."
                                            )
                                        except Exception:
                                            logger.info(
                                                f"error sending message to user {get_id_using_username(username)}"
                                            )
                                            send_message_to_specific_category_users(
                                                f"""
												Ошибка оповещения пользователя!
												Проверьте пользователя @{get_id_using_username(user[0])} ({user[0]})""",
                                                Roles.DEV.value,
                                                0,
                                            )
                                    send_message_to_specific_category_users(
                                        f"@{message.from_user.username} заблокировал @{username}",
                                        Roles.DEV.value,
                                        message.from_user.id,
                                    )
                                else:
                                    logger.debug(
                                        f"user {message.from_user.id} dont have rules"
                                        + f"for ban user {get_id_using_username(username)}",
                                    )
                                    bot.send_message(
                                        message.from_user.id,
                                        f"У вас недостаточно прав для блокировки пользователя @{username}",
                                    )
                            else:
                                logger.debug(f"user @{username} not found!")
                                bot.send_message(
                                    message.from_user.id,
                                    f"Пользователя @{username} нет в базе данных.",
                                )
                        else:
                            logger.debug(
                                "user blocked error! (the command was entered incorrectly)"
                            )
                            bot.send_message(
                                message.from_user.id,
                                """
								Ошибка блокировки пользователя.
								Проверьте, правильно ли вы ввели команду.
								После \"/ban\" должен стоять пробел.
								""",
                            )
                    except Exception as e:
                        logger.debug(e)
                        bot.send_message(
                            message.from_user.id,
                            """
							Ошибка блокировки пользователя.
							Проверьте, правильно ли вы ввели команду.
							""",
                        )

                # SEND HELP LIST
                elif message.text == "/help":
                    logger.debug("try send help...")
                    if role >= Roles.ADMIN.value:
                        bot.send_message(
                            message.from_user.id,
                            f"{config.MODERATOR_HELP_LIST}\n{config.ADMIN_HELP_LIST}",
                        )
                    elif role >= config.MODERATOR:
                        bot.send_message(message.from_user.id, f"{config.MODERATOR_HELP_LIST}")
                    logger.debug(
                        f"the list of commands was successfully sent to user {message.from_user.id}"
                    )

        else:
            logger.debug(f"user {message.from_user.id} dont have username")
            bot.send_message(
                message.from_user.id,
                """
				Извините, но для выполнения этой команды необходимо наличие username.
				Пожалуйста, установите свой username в настройках Telegram, после чего
				отправьте команду /update
				""",
            )

    except Exception as e:
        logger.error(e)


# RUN
run_bot = True
bot.polling()

# while run_bot:
# 	logger.info("RUN BOT...")
# 	try:
# 		bot.polling()
# 	except Exception as e:
# 		# logger.critical(e)
# 		# sleep(3)
# 		raise
