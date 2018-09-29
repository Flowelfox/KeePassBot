from src.lib.db import save_object
from src.models import DBSession, User


def delete_database(bot, update):
    user = DBSession.query(User).filter(User.chat_id == update.message.chat_id).first()

    if user.is_opened:
        bot.send_message(chat_id=user.chat_id, text="Your database in use, first close it with \"/close\"")
    else:
        user.file = None
        save_object(user, bot, update)
        bot.send_message(chat_id=user.chat_id, text="Your database was deleted")