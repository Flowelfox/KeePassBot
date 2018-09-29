from src.models import DBSession, User
from src.settings import opened_databases


def search(bot, update):
    if update.message:
        chat_id = update.message.chat_id
    else:
        chat_id = update.callback_query.message.chat_id

    user = DBSession.query(User).filter(User.chat_id == chat_id).first()

    try:
        keepass = opened_databases[user.chat_id]
    except KeyError as e:
        bot.send_message(chat_id=user.chat_id, text="Database not opened, try open database with \"/open\" command")
        return

    keepass.search(update.message.text.replace("/search ", ""))

    message_text, message_markup = keepass.get_message()

    bot.edit_message_text(chat_id=user.chat_id,
                          message_id=user.interface_message_id,
                          text=message_text,
                          reply_markup=message_markup)