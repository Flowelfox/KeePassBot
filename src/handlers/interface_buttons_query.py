import enum
import logging
from io import BytesIO

import telegram

from src.KeePass import KeePass
from src.handlers.close import close_db
from src.handlers.download import download_db
from src.handlers.resend import resend_interface
from src.lib.db import save_object
from src.lib.decorators import need_user
from src.models import DBSession, User
from src.settings import opened_databases, exm_mark_emo

logger = logging.getLogger(__name__)


class InterfaceStates(enum.Enum):
    ADD_EDIT = 1


@need_user
def interface_buttons_query(bot, update, user_data):
    data = update.callback_query.data
    user = user_data['user']
    try:
        keepass = opened_databases[user.chat_id]
    except KeyError as e:
        bot.send_message(chat_id=user.chat_id, text="Database not opened, try open database with \"/open\" command")
        return

    if data == "Nothing":
        bot.answer_callback_query(update.callback_query.id, text="Cannot delete root group", show_alert=False)
        return

    elif data == "Resend":
        resend_interface(bot, update)

    elif data == "Download":
        download_db(bot, update)
        return

    elif data == "Lock":
        close_db(bot, None, {'user': user})
        bot.answer_callback_query(update.callback_query.id)
        return

    elif data == "Back":
        keepass = opened_databases[user.chat_id]
        if keepass.active_item != keepass.active_item.get_root().root_group:
            keepass.active_item.deactivate()
            bot.answer_callback_query(update.callback_query.id)
        else:
            bot.answer_callback_query(update.callback_query.id, text="Already in root group", show_alert=False)
            return

    elif data.startswith("Edit_"):
        keepass = opened_databases[user.chat_id]
        if keepass.active_item:
            uuid = data.replace("Edit_", "")
            if len(uuid) == 24:
                message_text, message_markup = keepass.start_add_edit(obj=keepass.get_item_by_uuid(uuid))
                # Entering in create state
                user.create_state = True
                save_object(user, bot, update, user_data)

                try:
                    bot.edit_message_text(chat_id=user.chat_id,
                                          message_id=user.interface_message_id,
                                          text=message_text,
                                          reply_markup=message_markup,
                                          parse_mode=telegram.ParseMode.HTML)
                except telegram.TelegramError as e:
                    logger.error(str(e))

                if user.notification:
                    bot.send_message(chat_id=user.chat_id, text="Click on the field name to set the value for it.\nSend the text to set the value.\nBold fields are required.\nYou can use the arrows buttons to switch between fields.\n If you want to clear field send \"-\" (minus) symbol.")
            else:
                bot.send_message(chat_id=user.chat_id, text="Wrong edit uuid, try again.\nIf the problem persists, please write to administrator")
        bot.answer_callback_query(update.callback_query.id)
        return

    elif data == "ReallyDelete":
        keepass = opened_databases[user.chat_id]
        if keepass.active_item:
            keepass.active_item.delete()
        else:
            bot.answer_callback_query(update.callback_query.id)
            return

    elif data == "NoDelete":
        keepass = opened_databases[user.chat_id]
        try:
            del keepass.active_item.really_delete
        except AttributeError:
            pass
        message_text, message_markup = keepass.get_message()
        try:
            bot.edit_message_text(chat_id=user.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=message_text,
                                  reply_markup=message_markup)

        except telegram.TelegramError as e:
            logger.error(str(e))

        bot.answer_callback_query(update.callback_query.id)
        return

    elif data == "Delete":
        keepass = opened_databases[user.chat_id]
        keepass.active_item.really_delete = True
        message_text, message_markup = keepass.get_message()
        try:
            bot.edit_message_text(chat_id=user.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=message_text,
                                  reply_markup=message_markup)

        except telegram.TelegramError as e:
            logger.error(str(e))

        bot.answer_callback_query(update.callback_query.id)
        return
    elif len(data) == 24:
        keepass.get_item_by_uuid(data).activate()
        bot.answer_callback_query(update.callback_query.id)


    else:
        keepass = opened_databases[user.chat_id]
        try:
            if data == "Left":
                keepass.active_item.previous_page()
                bot.answer_callback_query(update.callback_query.id)
            if data == "Right":
                keepass.active_item.next_page()
                bot.answer_callback_query(update.callback_query.id)
        except IOError:
            bot.answer_callback_query(update.callback_query.id)
            return

    message_text, message_markup = keepass.get_message()
    try:
        bot.edit_message_text(chat_id=user.chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=message_text,
                              reply_markup=message_markup)
    except telegram.TelegramError as e:
        logger.error(str(e))


