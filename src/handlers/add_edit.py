import logging

import telegram

from src.KeePass import ItemType
from src.lib.db import save_object
from src.models import DBSession, User
from src.settings import opened_databases

logger = logging.getLogger(__name__)


def add_edit_query(bot, update):
    user = DBSession.query(User).filter(User.chat_id == update.callback_query.message.chat_id).first()
    data = update.callback_query.data.replace("create_", "")
    keepass = opened_databases[user.chat_id]

    if data == "done":
        for field in keepass.add_edit_state.req_fields:
            if not keepass.add_edit_state.fields[field]:
                bot.send_message(chat_id=user.chat_id, text="Please fill required fields")
                bot.answer_callback_query(update.callback_query.id)
                return

        keepass.finish_add_edit()

        user.create_state = False
        save_object(user, bot, update, user)

        message_text, message_markup = keepass.get_message()
        bot.edit_message_text(chat_id=user.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup)
        bot.answer_callback_query(update.callback_query.id)
        return

    elif data == "Back":
        user.create_state = False
        save_object(user, bot, update, user)

        keepass.finish_add_edit()

        message_text, message_markup = keepass.get_message()
        bot.edit_message_text(chat_id=user.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup)

        bot.answer_callback_query(update.callback_query.id)
        return
    elif data == "Left":
        keepass.add_edit_state.prev_field()
        bot.answer_callback_query(update.callback_query.id)
    elif data == "Right":
        keepass.add_edit_state.next_field()
        bot.answer_callback_query(update.callback_query.id)
    elif data == "generate_password":
        keepass.add_edit_state.generate_password()
    else:
        keepass.add_edit_state.set_cur_field(data)

    message_text, message_markup = keepass.add_edit_state.get_message()
    try:
        bot.edit_message_text(chat_id=user.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup,
                              parse_mode=telegram.ParseMode.HTML)

    except telegram.TelegramError as e:
        logger.error(str(e))

    bot.answer_callback_query(update.callback_query.id)


def message_in_add_edit(bot, update):
    user = DBSession.query(User).filter(User.chat_id == update.message.chat_id).first()
    text = update.message.text
    keepass = opened_databases[user.chat_id]

    # length check
    if len(text) > 40:
        bot.send_message(chat_id=user.chat_id, text="New value too long. Please send text bellow 40 chars")
        return
    try:
        if text == '-':
            keepass.add_edit_state.set_cur_field_value(None)
        else:
            keepass.add_edit_state.set_cur_field_value(text)
        keepass.add_edit_state.next_field()
        message_text, message_markup = keepass.add_edit_state.get_message()
        try:
            bot.edit_message_text(chat_id=user.chat_id,
                                  message_id=user.interface_message_id,
                                  text=message_text,
                                  reply_markup=message_markup,
                                  parse_mode=telegram.ParseMode.HTML)

        except telegram.TelegramError as e:
            logger.error(str(e))
    except AttributeError:
        user.create_state = False
        save_object(user, bot, update)


def create(bot, update):
    if update.message:
        chat_id = update.message.chat_id
    else:
        chat_id = update.callback_query.message.chat_id

    user = DBSession.query(User).filter(User.chat_id == chat_id).first()

    args = update.message.text.replace('/create ', '')
    keepass = opened_databases[user.chat_id]

    if "group".startswith(args.lower()):
        message_text, message_markup = keepass.start_add_edit(ItemType.GROUP)
    elif "entry".startswith(args.lower()):
        message_text, message_markup = keepass.start_add_edit(ItemType.ENTRY)
    else:
        bot.send_message(chat_id=user.chat_id, text="Wrong arguments, choices are: 'Entry', 'Group', 'e', 'g'\nExample: /create Group")
        return
    # Entering in create state
    user.create_state = True
    save_object(user, bot, update)

    try:
        bot.edit_message_text(chat_id=user.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup,
                              parse_mode=telegram.ParseMode.HTML)
    except telegram.TelegramError as e:
        logger.error(str(e))

    if user.notification:
        bot.send_message(chat_id=user.chat_id, text="Click on the field name to set the value for it.\nSend the text to set the value.\nBold fields are required.\nYou can use the arrows buttons to switch between fields.")