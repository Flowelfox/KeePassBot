import datetime
import enum
import logging
import os

from sqlalchemy.exc import SQLAlchemyError
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from psycopg2 import IntegrityError

from src.handlers.conv import conv_fallback, conv_success
from src.handlers.resend import resend_interface
from src.lib.db import save_object
from src.lib.decorators import need_user
from src.models import User, DBSession
from src.settings import TEMP_FOLDER, exm_mark_emo, opened_databases
from io import BytesIO

logger = logging.getLogger(__name__)


class StartStates(enum.Enum):
    FIRST_LOAD = 1
    KEY = 2
    PASSWORD = 3


open_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='open_db_yes'), InlineKeyboardButton('No', callback_data='open_db_no')]],)


def start_entry(bot, update, user_data):

    user = DBSession.query(User).filter(User.chat_id == update.message.chat_id).first()
    if user is None:
        user = DBSession.query(User).filter(User.name == f"@{update.message.from_user.username if update.message.from_user.username else ''}").first()
    if user is None:
        user = DBSession.query(User).filter(User.name == f"{update.message.from_user.first_name if update.message.from_user.first_name else ''} {update.message.from_user.last_name if update.message.from_user.last_name else ''}").first()

    if not user:
        user = User()
        user.name = f"{update.message.from_user.first_name if update.message.from_user.first_name else ''} {update.message.from_user.last_name if update.message.from_user.last_name else ''}"
        user.username = f"@{update.message.from_user.username if update.message.from_user.username else ''}"
        user.join_date = datetime.datetime.now()
        user.active = True
        user.chat_id = update.message.chat_id
        save_object(user, bot, update, user_data)

        bot.send_message(chat_id=user.chat_id, text="Hi %s, now you registered." % user.username)
        bot.send_message(chat_id=user.chat_id, text="If you want remove all information about yourself send me \"/stop\".")
        bot.send_message(chat_id=user.chat_id, text="Please send me database file for start")
        return StartStates.FIRST_LOAD
    else:
        user.active = True
        user.name = f"{update.message.from_user.first_name if update.message.from_user.first_name else ''} {update.message.from_user.last_name if update.message.from_user.last_name else ''}"
        user.username = f"@{update.message.from_user.username if update.message.from_user.username else ''}"
        user.chat_id = update.message.chat_id

        save_object(user, bot, update, user_data)

        bot.send_message(chat_id=user.chat_id, text="Hi again, %s, you already registered." % user.username)
        bot.send_message(chat_id=user.chat_id, text="If you want remove all information about you send me \"/stop\".")

        if user.file:
            if user.chat_id in opened_databases and user.is_opened:
                bot.send_message(chat_id=user.chat_id, text="Your database already opened")
                resend_interface(bot, update)
                return conv_success(bot, update, user_data)
            else:
                bot.send_message(chat_id=user.chat_id, text="Open database?", reply_markup=open_markup)
            return conv_success(bot, update, user_data)
        else:
            bot.send_message(chat_id=user.chat_id, text="Please send me database file for start")
            return StartStates.FIRST_LOAD


# FIRST_LOAD
@need_user
def start_state_load(bot, update, user_data):
    """Add file to database for user"""
    user = user_data['user']

    if not update.message.document.file_name.endswith(".kdbx"):
        bot.send_message(chat_id=user.chat_id, text="Please send file KeePass database file")
        return StartStates.FIRST_LOAD

    """Write to new memory file"""
    file = BytesIO()
    file_id = update.message.document.file_id
    t_file = bot.get_file(file_id)
    t_file.download(out=file)
    file.seek(0)

    """Saving to database"""
    user.file = file.read()
    save_object(user, bot, update, user_data)

    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Yes", callback_data="YesKey"),
                                    InlineKeyboardButton(text="No", callback_data="NoKey")]])
    bot.send_message(chat_id=user.chat_id, text="Did you need file-key for opening your database?", reply_markup=markup)
    return StartStates.KEY


# KEY
@need_user
def start_state_key(bot, update, user_data):
    user = user_data['user']
    data = update.callback_query.data

    if data == "NoKey":
        user.key_file_needed = False
    if data == "YesKey":
        user.key_file_needed = True

    save_object(user, bot, update, user_data)

    bot.answer_callback_query(update.callback_query.id)
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Yes", callback_data="YesPassword"),
                                    InlineKeyboardButton(text="No", callback_data="NoPassword")]])
    bot.send_message(chat_id=user.chat_id, text="Did you need password for openning you database?", reply_markup=markup)

    return StartStates.PASSWORD


# PASSWORD
@need_user
def start_state_password(bot, update, user_data):
    user = user_data['user']
    data = update.callback_query.data

    if data == "NoPassword":
        user.password_needed = False
    if data == "YesPassword":
        user.password_needed = True
    save_object(user, bot, update, user_data)

    bot.answer_callback_query(update.callback_query.id)

    bot.send_message(chat_id=user.chat_id, text=f"{exm_mark_emo * 2}PLEASE REMOVE DATABASE FILE FROM HISTORY{exm_mark_emo * 2}")
    bot.send_message(chat_id=user.chat_id, text="Open database?", reply_markup=open_markup)
    return conv_success(bot, update, user_data)