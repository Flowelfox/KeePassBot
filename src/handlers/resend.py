import logging

from src.lib.db import save_object
from src.lib.decorators import need_user
from src.models import DBSession, User
from src.settings import opened_databases

logger = logging.getLogger(__name__)


@need_user
def resend_interface(bot, update):
    if update.message:
        chat_id = update.message.chat_id
    else:
        chat_id = update.callback_query.message.chat_id

    user = DBSession.query(User).filter(User.chat_id == chat_id).first()

    try:
        keepass = opened_databases[user.chat_id]
    except KeyError:
        user.is_opened = False
        save_object(user, bot, update)
        bot.send_message(chat_id=user.chat_id, text="Some error happened, try to open your database with \"/open\" command")
        return

    # delete previous
    try:
        bot.delete_message(chat_id=user.chat_id, message_id=user.interface_message_id)
    except Exception as e:
        logger.error(f"Error while deleting old interface message:\n{str(e)}")

    # send new
    message_text, message_markup = keepass.get_message()
    interface_message = bot.send_message(chat_id=user.chat_id, text=message_text, reply_markup=message_markup)

    user.interface_message_id = interface_message.message_id
    save_object(user, bot, update)
