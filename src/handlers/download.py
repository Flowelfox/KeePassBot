from io import BytesIO

from src.models import DBSession, User
from src.settings import opened_databases, exm_mark_emo


def download_db(bot, update):
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

    """Write to new memory file"""
    output = BytesIO()
    output.write(user.file)
    output.name = keepass.root_group.name + '.kdbx'
    output.seek(0)

    """Send to user"""
    bot.send_document(chat_id=user.chat_id, document=output)
    bot.send_message(chat_id=user.chat_id, text=f"{exm_mark_emo * 2}PLEASE REMOVE DATABASE FILE FROM HISTORY{exm_mark_emo * 2}")
    bot.answer_callback_query(update.callback_query.id)
