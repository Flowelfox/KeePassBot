import enum

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from src.handlers.conv import conv_success
from src.lib.db import save_object
from src.lib.decorators import need_user


class NotsStates(enum.Enum):
    QUERY = 1


@need_user
def nots_entry(bot, update, user_data):
    user = user_data['user']

    if user.notification == True:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Turn off", callback_data='nots_off'), InlineKeyboardButton("Leave enabled", callback_data='nots_nothing')]])
        mes = bot.send_message(chat_id=user.chat_id, text="Notifications are now enabled", reply_markup=markup)
        user_data['to_delete'] = [mes.message_id]
    else:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Turn on", callback_data='nots_on'), InlineKeyboardButton("Leave disabled", callback_data='nots_nothing')]])
        mes = bot.send_message(chat_id=user.chat_id, text="Notifications are now disabled", reply_markup=markup)
        user_data['to_delete'] = [mes.message_id]

    return NotsStates.QUERY


# QUERY
@need_user
def nots_state_query(bot, update, user_data):
    user = user_data['user']
    data = update.callback_query.data

    bot.answer_callback_query(update.callback_query.id)
    if data == 'nots_nothing':
        pass
    elif data == 'nots_on':
        bot.send_message(chat_id=user.chat_id, text="Notifications turned on.")
        user.notification = True
    elif data == 'nots_off':
        bot.send_message(chat_id=user.chat_id, text="Notifications turned off.")
        user.notification = False

    save_object(user, bot, update, user_data)

    return conv_success(bot, update, user_data)
