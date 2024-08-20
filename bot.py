# HOME OF UNITY BOT
import os
import random
import sqlite3
from typing import Literal
from typing import Tuple

from dotenv import load_dotenv
import telebot
import yaml

from roles import Role
import user_utils
import utils


SECRET_ANGEL = False

read = load_dotenv(".env")
token = os.getenv("TOKEN")

with open("replies.yaml", encoding="utf-8") as f:
    replies = yaml.safe_load(f)

bot = telebot.TeleBot(token)

logger = utils.get_logger(__name__)


# adding data of user to database
def add_to_database(user_id: int, username: str) -> None:
    logger.debug("adding to the database...")
    with sqlite3.connect("data.db") as cursor:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, "empty", username, 0, Role.DEFAULT.value, "empty", 0, "empty", "empty", 0),
        )
    logger.info(f"user {user_id} added to the database")
    send_message_to_specific_category_users(
        replies["add_to_database"].format(username=username),
        Role.ADMIN.value,
        user_id,
    )


# give username and category of user
def select_name_and_category(text: str) -> Tuple[str, int] | Literal[False]:
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

        if level >= Role.DEFAULT.value and level <= Role.DEV.value:
            username = "".join(username)
            return username, level
        else:
            return False
    else:
        return False


# get random text from the databse
def get_random_text() -> str:
    with sqlite3.connect("data.db") as cursor:
        texts = cursor.execute("SELECT text FROM texts")
    texts_list = [text[0] for text in texts]
    random_text_id = random.randint(0, len(texts_list) - 1)
    return str(texts_list[random_text_id])


# notifications of baned user try use bot
def is_baned(user_id: int, command: str) -> bool:
    with sqlite3.connect("data.db") as cursor:
        ban = cursor.execute("SELECT ban FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
    if ban:
        logger.info(f'baned user {user_id} try use command "{command}"')
        bot.send_message(user_id, replies["is_banned"])
    return ban


# check role of user
def get_user_category(user_id: int) -> int | Literal[False]:
    with sqlite3.connect("data.db") as cursor:
        info = cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if info is None:
        logger.debug(f"not found role of user {user_id}")
        return False
    else:
        return info[0]


# get user id from username
def get_id_using_username(username: int) -> int:
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
def send_message_to_specific_category_users(text: str, necessary_role: int, sender: int) -> int:
    count = 0
    with sqlite3.connect("data.db") as cursor:
        users = cursor.execute("SELECT user_id FROM users WHERE role >= ?", (necessary_role,))
    for user in users:
        if user[0] != str(sender):
            try:
                bot.send_message(user[0], text)
                count += 1
            except telebot.apihelper.ApiTelegramException as e:
                logger.error(e)
    logger.debug(f"send a message to a specifical category to {count} user(s)")
    return count


# command start
@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message) -> None:
    logger.debug(f'user {message.from_user.id} tried use command "start"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        if is_baned(message.from_user.id, "start"):
            bot.send_message(message.from_user.id, replies["start"]["welcome"])
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(e)


@bot.message_handler(regexp="^echo ")
def echo(message: telebot.types.Message) -> None:
    bot.send_message(message.from_user.id, message.text[5:])


# adding to prays lists
@bot.message_handler(commands=["prays_lists"])
def change_state(message: telebot.types.Message) -> None:
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
                        (Role.DEFAULT.value,),
                    )
                for user in users:
                    if user[0] == str(message.from_user.id):
                        logger.debug("try change state...")
                        state = 0
                        if user[1] == 1:
                            logger.info(f"user {user[0]} has been removed from prays lists")
                            send_message_to_specific_category_users(
                                replies["prays_lists"]["removed"]["notification"].format(
                                    username=message.from_user.username
                                ),
                                Role.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], replies["prays_lists"]["removed"]["success"])
                        else:
                            state = 1
                            logger.info(f"user {user[0]} added to prays lists")
                            send_message_to_specific_category_users(
                                replies["prays_lists"]["added"]["notification"].format(
                                    username=message.from_user.username
                                ),
                                Role.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], replies["prays_lists"]["added"]["success"])
                        with sqlite3.connect("data.db") as cursor:
                            cursor.execute(
                                "UPDATE users SET state = ? WHERE user_id = ?", (state, user[0])
                            )
            else:
                logger.debug(f"{message.from_user.id} dont have username")
                bot.send_message(
                    message.from_user.id,
                    replies["other"]["none_username"],
                )
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(e)


# added event
@bot.message_handler(commands=["event"])
def change_event_state(message: telebot.types.Message) -> None:
    logger.debug(f'user {message.from_user.id} tried use command "event"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        if not is_baned(message.from_user.id, "event"):
            bot.send_message(message.from_user.id, replies["event"]["registration"])
            if (
                user_utils.check_username(message.from_user.username)
                and message.from_user.username is not None
                and SECRET_ANGEL
            ):
                with sqlite3.connect("data.db") as cursor:
                    users = cursor.execute(
                        "SELECT user_id, event FROM users WHERE role >= ?",
                        (Role.DEFAULT.value,),
                    )
                for user in users:
                    if user[0] == str(message.from_user.id):
                        logger.debug("try change event_state...")
                        state = 0
                        if user[1] == 1:
                            logger.info(f"user {user[0]} has been removed from event lists")
                            send_message_to_specific_category_users(
                                replies["event"]["removed"]["notification"].format(
                                    username=message.from_user.username
                                ),
                                Role.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], replies["event"]["removed"]["success"])
                        else:
                            state = 1
                            logger.info(f"user {user[0]} added to event")
                            send_message_to_specific_category_users(
                                replies["event"]["added"]["notification"].format(
                                    username=message.from_user.username
                                ),
                                Role.ADMIN.value,
                                message.from_user.id,
                            )
                            bot.send_message(user[0], replies["event"]["added"]["success"])
                        with sqlite3.connect("data.db") as cursor:
                            cursor.execute(
                                "UPDATE users SET event = ? WHERE user_id = ?", (state, user[0])
                            )
            else:
                logger.debug(f"user {message.from_user.id} dont have username")
                bot.send_message(
                    message.from_user.id,
                    replies["other"]["none_username"],
                )
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(e)


# set the user to developer category
@bot.message_handler(commands=[os.getenv("KEY")])
def set_the_user_to_developer_category(message: telebot.types.Message) -> None:
    logger.debug(f"user {message.from_user.id} is trying to get developer role...")
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        with sqlite3.connect("data.db") as cursor:
            cursor.execute(
                "UPDATE users SET role = ? WHERE user_id = ?",
                (Role.DEV.value, message.from_user.id),
            )
        logger.info(f"user {message.from_user.id} has been granted developer rights")
        bot.send_message(
            message.from_user.id,
            replies["set_user_developer"]["success"].format(role=Role.DEV.name),
        )
        send_message_to_specific_category_users(
            replies["set_user_developer"]["notification"].format(
                username=message.from_user.username
            ),
            Role.DEV.value,
            message.from_user.id,
        )
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(e)


# send the user information about the bot
@bot.message_handler(commands=["info"])
def send_info(message: telebot.types.Message) -> None:
    logger.debug(f'user {message.from_user.id} tried use command "info"...')

    if not user_utils.check_user_id(message.from_user.id):
        add_to_database(message.from_user.id, message.from_user.username)

    if not is_baned(message.from_user.id, "info"):
        logger.debug(f"bot information was successfully sent to user {message.from_user.id}")
        bot.send_message(message.from_user.id, replies["info"])


# update data of user in database
@bot.message_handler(commands=["update"])
def update_user_data(message: telebot.types.Message) -> None:
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
                replies["update"]["notification"].format(username=message.from_user.username),
                Role.DEV.value,
                message.from_user.id,
            )
            bot.send_message(message.from_user.id, replies["update"]["success"])
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(e)


# send to user his role
@bot.message_handler(commands=["who"])
def who_i_am(message: telebot.types.Message) -> None:
    logger.debug(f'user {message.from_user.id} is trying to use command "who"...')
    try:
        if not user_utils.check_user_id(message.from_user.id):
            add_to_database(message.from_user.id, message.from_user.username)

        complete = True
        role = get_user_category(message.from_user.id)
        if role == Role.DEFAULT.value:
            role = Role.DEFAULT.name
        elif role == Role.MOD.value:
            role = Role.MOD.name
        elif role == Role.ADMIN.value:
            role = Role.ADMIN.name
        elif role == Role.DEV.value:
            role = Role.DEV.name
        else:
            complete = False

        if complete:
            logger.debug("the command completed successfully!")
            bot.send_message(message.from_user.id, replies["who"].format(role=role))
        else:
            logger.warning(
                f"not found role of user {message.from_user.id}! (@{message.from_user.username})"
            )
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(e)


# other
@bot.message_handler(content_types=["text"])
def text(message: telebot.types.Message) -> None:
    logger.debug(f'user {message.from_user.id} is trying to use command "text"...')
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
            if message.text[:8] == "/my_wish" and SECRET_ANGEL:
                logger.debug("try set wish...")
                text = message.text[9:]
                with sqlite3.connect("data.db") as cursor:
                    cursor.execute(
                        "UPDATE users SET my_wish = ? WHERE user_id = ?",
                        (text, message.from_user.id),
                    )
                logger.debug(f"set wish for {message.from_user.id}")
                bot.send_message(message.from_user.id, replies["event"]["wish"])

            # RANDOMIZE USERS FOR PRAYS LISTS
            elif message.text == "/randomize" and role >= Role.MOD.value:
                logger.debug("try randomize...")
                with sqlite3.connect("data.db") as cursor:
                    users = cursor.execute(
                        "SELECT username, state FROM users WHERE role >= ?",
                        (Role.DEFAULT.value,),
                    )
                prayers_list_parallel = []
                users_id_in_use = []

                # Get list "only prayers"
                prayers_list = [user[0] for user in users if user[1] == 1]

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
                            replies["randomize"]["message"].format(
                                username=prayers_list_parallel[i],
                                text=get_random_text(),
                            ),
                        )
                    except telebot.apihelper.ApiTelegramException:
                        logger.warning(
                            "error sending message to user"
                            f"{get_id_using_username(prayers_list[i])}"
                        )
                    with sqlite3.connect("data.db") as cursor:
                        cursor.execute(
                            "UPDATE users SET prays_friend = ? WHERE username = ?",
                            (prayers_list_parallel[i], prayers_list[i]),
                        )

            # START EVENT (RANDOMIZE)
            elif message.text == "/start_event" and SECRET_ANGEL:  # OFF
                logger.debug("try start_event...")
                with sqlite3.connect("data.db") as cursor:
                    users = cursor.execute(
                        "SELECT username, event, my_wish FROM users WHERE role >= ?",
                        (Role.DEFAULT.value,),
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
                            replies["event"]["message"].formaet(
                                username=users_list_parallel[i], wish=wish_of_users_parallel[i]
                            ),
                        )
                    except telebot.apihelper.ApiTelegramException:
                        logger.warning(
                            f"error sending message to user {get_id_using_username(users_list[i])}"
                        )
                    with sqlite3.connect("data.db") as cursor:
                        cursor.execute(
                            "UPDATE users SET santa_for = ? WHERE username = ?",
                            (users_list_parallel[i], users_list[i]),
                        )

            # SEND MESSAGE TO ALL USERS
            elif message.text[:2] == "**" and role >= Role.MOD.value:
                logger.debug("try send message to all user...")
                text = message.text[2:]
                count = send_message_to_specific_category_users(
                    text,
                    Role.DEFAULT.value,
                    message.from_user.id,
                )
                logger.info(f"user {message.from_user.id} send message to {count} user(s)")
                bot.send_message(
                    message.from_user.id, replies["user_message"]["success"].format(count=count)
                )

            # SEND MESSAGE TO ALL PRAYERS
            elif message.text[:1] == "*" and role >= Role.MOD.value:
                logger.debug("try send message to all prayer...")
                text = message.text[1:]
                count = 0
                with sqlite3.connect("data.db") as cursor:
                    users = cursor.execute(
                        "SELECT user_id, state FROM users WHERE role >= ?",
                        (Role.DEFAULT.value,),
                    )
                for user in users:
                    if user[1] == 1 and str(message.from_user.id) != user[0]:
                        try:
                            bot.send_message(user[0], text)
                            count += 1
                        except telebot.apihelper.ApiTelegramException:
                            logger.info(f"error sending message to user {user[0]}")
                            send_message_to_specific_category_users(
                                replies["prayer_messages"]["not_found_user"].format(user=user[0]),
                                Role.DEV.value,
                                0,
                            )
                logger.info(f"user {message.from_user.id} send message to {count} user(s):")
                bot.send_message(
                    message.from_user.id,
                    replies["prayer_messages"]["success"].format(count=count),
                )

            # SEND MESSAGE TO MODERATORS AND ADMINS
            elif message.text[0] == "!" and role >= Role.ADMIN.value:
                logger.debug("try send message to all moderators and admins...")
                text = message.text[1:]
                count = send_message_to_specific_category_users(
                    text,
                    Role.MOD.value,
                    message.from_user.id,
                )
                logger.info(f"user {message.from_user.id} send message to {count} user(s)")
                bot.send_message(
                    message.from_user.id,
                    replies["admin_messages"]["success"].format(count=count),
                )

            # CHANGE ROLE OF USER
            elif message.text[:9] == "/setRole" and role >= Role.ADMIN.value:
                logger.debug("try change role...")
                try:
                    resours = select_name_and_category(message.text)
                    if not resours:
                        logger.debug("change role error! (level not found)")
                        bot.send_message(
                            message.from_user.id,
                            replies["change_role"]["level_not_found"],
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
                                            replies["change_role"]["success"].format(
                                                resours_0=resours[0],
                                                resours_1=resours[1],
                                            ),
                                        )
                                    if (
                                        get_user_category(get_id_using_username(resours[0]))
                                        < Role.DEV.value
                                        or get_user_category(get_id_using_username(resours[0]))
                                        == Role.DEV.value
                                        and str(message.from_user.id)
                                        == str(get_id_using_username(resours[0]))
                                    ):
                                        try:
                                            bot.send_message(
                                                get_id_using_username(resours[0]),
                                                replies["change_role"]["success_me"],
                                            )
                                        except telebot.apihelper.ApiTelegramException:
                                            logger.info(
                                                "error sending message to user"
                                                f"{get_id_using_username(resours[0])}"
                                            )
                                            send_message_to_specific_category_users(
                                                replies["change_role"]["notification_error"].format(
                                                    resours=resours[0]
                                                ),
                                                Role.DEV.value,
                                                0,
                                            )
                                    send_message_to_specific_category_users(
                                        replies["change_role"]["notification"].format(
                                            username=message.from_user.username,
                                            resours_0=resours[0],
                                            resours_1=resours[1],
                                        ),
                                        Role.DEV.value,
                                        message.from_user.id,
                                    )
                                else:
                                    logger.debug(
                                        f"user {message.from_user.id} role is lower than"
                                        f"user @{resours[0]}"
                                    )
                                    bot.send_message(
                                        message.from_user.id, replies["change_role"]["denied"]
                                    )
                            else:
                                logger.debug(
                                    f"user {message.from_user.id} tries to give user"
                                    f"{get_id_using_username(resours[0])}"
                                    "an role higher than his own",
                                )
                                bot.send_message(
                                    message.from_user.id,
                                    replies["change_role"]["denied"],
                                )
                        else:
                            logger.debug(f"user @{resours[0]} not found!")
                            bot.send_message(
                                message.from_user.id,
                                replies["change_role"]["user_not_found"].format(
                                    username=resours[0]
                                ),
                            )

                except telebot.apihelper.ApiTelegramException as e:
                    logger.debug(e)
                    bot.send_message(message.from_user.id, replies["change_role"]["error"])

            # BAN USER
            elif message.text[:4] == "/ban" and role >= Role.ADMIN.value:
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
                                        (0, 0, username),
                                    )
                                logger.info(
                                    f"user {message.from_user.id} blocked user"
                                    f"{get_id_using_username(username)}"
                                )
                                if str(message.from_user.id) != get_id_using_username(username):
                                    bot.send_message(
                                        message.from_user.id,
                                        replies["ban"]["success"].format(username=username),
                                    )
                                if (
                                    get_user_category(get_id_using_username(username))
                                    != Role.DEV.value
                                ):
                                    try:
                                        bot.send_message(
                                            get_id_using_username(username),
                                            replies["ban"]["user_notification"],
                                        )
                                    except telebot.apihelper.ApiTelegramException:
                                        logger.info(
                                            "error sending message to user"
                                            f"{get_id_using_username(username)}"
                                        )
                                        send_message_to_specific_category_users(
                                            replies["ban"][""].format(
                                                user_id=get_id_using_username(user[0]),
                                                user=user[0],
                                            ),
                                            Role.DEV.value,
                                            0,
                                        )
                                        raise
                                send_message_to_specific_category_users(
                                    replies["ban"]["notification"].format(
                                        my_username=message.from_user.username.username,
                                        username=username,
                                    ),
                                    Role.DEV.value,
                                    message.from_user.id,
                                )
                            else:
                                logger.debug(
                                    f"user {message.from_user.id} dont have rules"
                                    + f"for ban user {get_id_using_username(username)}",
                                )
                                bot.send_message(
                                    message.from_user.id,
                                    replies["ban"]["denied"].format(username=username),
                                )
                        else:
                            logger.debug(f"user @{username} not found!")
                            bot.send_message(
                                message.from_user.id,
                                replies["ban"]["user_not_found"].format(username=username),
                            )
                    else:
                        logger.debug("user blocked error! (the command was entered incorrectly)")
                        bot.send_message(message.from_user.id, replies["ban"]["command_error"])
                except telebot.apihelper.ApiTelegramException as e:
                    logger.debug(e)
                    bot.send_message(
                        message.from_user.id,
                        replies["ban"]["command_error"],
                    )

            # SEND HELP LIST
            elif message.text == "/help":
                logger.debug("try send help...")
                if role >= Role.ADMIN.value:
                    bot.send_message(
                        message.from_user.id,
                        f"{replies['help_lists']['moderator_help_list']}\n{replies['help_lists']['admin_help_list']}",
                    )
                elif role >= Role.MOD.value:
                    bot.send_message(
                        message.from_user.id,
                        f"{replies['help_lists']['moderator_help_list']}",
                    )
                logger.debug(
                    f"the list of commands was successfully sent to user {message.from_user.id}"
                )

        else:
            logger.debug(f"user {message.from_user.id} dont have username")
            bot.send_message(message.from_user.id, replies["other"]["none_username"])


# RUN
bot.polling()
