import logging

import telegram
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from src.lib.db import save_object
from src.lib.decorators import need_user
from src.settings import opened_databases

logger = logging.getLogger(__name__)

open_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Yes', callback_data='open_db_yes'), InlineKeyboardButton('No', callback_data='open_db_no')]],)


@need_user
def close_db(bot, update, user_data):
    user = user_data['user']
    try:
        opened_databases[user.chat_id].close()
        del opened_databases[user.chat_id]
    except KeyError as e:
        logger.error("Key error: " + str(e))

    user.is_opened = False
    save_object(user, bot, update, user_data)
    try:
        bot.delete_message(chat_id=user.chat_id, message_id=user.interface_message_id)
    except telegram.TelegramError as e:
        logger.error(f"Can't delete message because:\n{str(e)}")

    bot.send_message(chat_id=user.chat_id, text="Database closed")
    bot.send_message(chat_id=user.chat_id, text="Open database?", reply_markup=open_markup)
