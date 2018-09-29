import logging

from psycopg2._psycopg import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from src.handlers.conv import conv_fallback
from src.models import DBSession

logger = logging.getLogger(__name__)


def save_object(object, bot=None, update=None, user_data=None):
    try:
        DBSession.add(object)
        DBSession.commit()
    except (SQLAlchemyError, IntegrityError) as e:
        DBSession.rollback()
        logger.critical("Database error")
        logger.debug(f"Error message:\n{str(e)}")
        if bot is not None and update is not None:
            bot.send_message(chat_id=update.message.chat_id, text="Ошибка базы данных, обратитесь к support@botman.com.ua")
            if user_data is None:
                user_data = {}
            return conv_fallback(bot, update, user_data)