import enum
import logging
import os
from io import BytesIO

from src.KeePass import KeePass
from src.handlers.conv import conv_success, conv_fallback
from src.handlers.resend import resend_interface
from src.lib.db import save_object
from src.lib.decorators import need_user
from src.settings import exm_mark_emo, TEMP_FOLDER, opened_databases


class OpenStates(enum.Enum):
    KEY = 1
    PASSWORD = 2


logger = logging.getLogger(__name__)


@need_user
def open_entry(bot, update, user_data):
    user = user_data['user']
    if update.callback_query:
        data = update.callback_query.data
        bot.answer_callback_query(update.callback_query.id)
        if data == "open_db_no":
            return conv_success(bot, update, user_data)

    """Sending message"""
    if user.chat_id in opened_databases and user.is_opened:
        bot.send_message(chat_id=user.chat_id, text="Your database already opened")
        resend_interface(bot, update)
        return conv_success(bot, update, user_data)
    else:
        if user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=user.chat_id, text="Please send me key-file and then password to open database")
            return OpenStates.KEY
        elif user.password_needed and not user.key_file_needed:
            bot.send_message(chat_id=user.chat_id, text="Send me password to open database")
            return OpenStates.PASSWORD
        elif not user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=user.chat_id, text="Send me key-file to open database")
            return OpenStates.KEY



# KEY
@need_user
def open_state_key(bot, update, user_data):
    user = user_data['user']
    file_path = os.path.join(TEMP_FOLDER, f"{user.chat_id}.key")
    file = open(file_path, 'wb')
    file_id = update.message.document.file_id
    t_file = bot.get_file(file_id)
    t_file.download(out=file)
    file.seek(0)
    user_data['key'] = file_path

    if user.password_needed:
        bot.send_message(chat_id=user.chat_id, text="Now send me your password")
        return OpenStates.PASSWORD
    else:
        open_db(bot, update, user_data)


# PASSWORD
@need_user
def open_state_password(bot, update, user_data):
    text = update.message.text
    user_data['pass'] = text
    return open_db(bot, update, user_data)


@need_user
def open_db(bot, update, user_data):
    user = user_data['user']

    """Creating file in temp"""
    # with open(os.path.join(TEMP_FOLDER, f"{user.chat_id}.key"), 'wb') as key_file:
    #     key_file.write(user_data['key'].read())

    db_path = os.path.join(TEMP_FOLDER, f"{user.chat_id}.db")
    with open(db_path, 'wb') as db_file:
        db_file.write(user.file)


    # file_id = update.message.document.file_id
    # f = bot.get_file(file_id)
    # f.download(TEMP_FOLDER + '/' + update.message.from_user.name + '.key')

    """Trying to open database"""
    keepass = KeePass(db_path)
    try:
        if user.password_needed and user.key_file_needed:
            keepass.open(chat_id=user.chat_id, password=user_data['pass'], keyfile_path=user_data['key'])
        elif user.password_needed and not user.key_file_needed:
            keepass.open(chat_id=user.chat_id, password=user_data['pass'])
        elif not user.password_needed and user.key_file_needed:
            keepass.open(chat_id=user.chat_id, keyfile_path=user_data['key'])

        opened_databases.update({update.message.chat_id: keepass})
        message_text, message_markup = keepass.get_message()
        interface_message = bot.send_message(chat_id=user.chat_id, text=message_text, reply_markup=message_markup)

        if user.notification:
            bot.send_message(chat_id=user.chat_id, text=f"{exm_mark_emo * 2}PLEASE REMOVE YOUR PASSWORD FROM HISTORY{exm_mark_emo * 2}")

        user.is_opened = True
        user.interface_message_id = interface_message.message_id
        save_object(user, bot, update, user_data)

    except IOError as e:
        logger.error(str(e))
        if user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=user.chat_id, text=f"Password or key-file wrong")
            return OpenStates.KEY
        elif user.password_needed and not user.key_file_needed:
            bot.send_message(chat_id=user.chat_id, text=f"Password is wrong")
            return OpenStates.PASSWORD
        elif not user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=user.chat_id, text=f"Key-file is wrong")
            return OpenStates.KEY
    finally:
        if user.key_file_needed:
            os.remove(user_data['key'])

    """Removing file in temp"""
    os.remove(db_path)

    return conv_success(bot, update, user_data)


