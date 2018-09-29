import logging
from functools import wraps

from src.models import DBSession, User

logger = logging.getLogger(__name__)


def restricted(role):
    def restricted_inner(func):
        @wraps(func)
        def wrapped(bot, update, *args, **kwargs):
            if update.message:
                user = DBSession.query(User).filter(User.chat_id == update.message.chat_id).first()
                if user.role is not role:
                    logger.warning(f"Unauthorized access denied for {user.username if user.username else 'Someone'} with id {user.id} when accessing {func.__name__}")
                    bot.send_message(chat_id=update.message.chat_id, text="Извините, неверная комманда.")
                    return
            return func(bot, update, *args, **kwargs)
        return wrapped
    return restricted_inner


def need_user(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        if 'user_data' in kwargs.keys():
            user_data = kwargs['user_data']
        elif len(args) > 0 and isinstance(args[0], dict):
            user_data = args[0]
        else:
            user_data = None

        if user_data is not None:
            if 'user' not in user_data:
                if update.message is not None:
                    chat_id = update.message.chat_id
                else:
                    chat_id = update.callback_query.message.chat_id

                user_data['user'] = DBSession.query(User).filter(User.chat_id == chat_id).first()

        return func(bot, update, *args, **kwargs)
    return wrapped