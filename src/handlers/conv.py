import logging

from telegram.error import BadRequest
from telegram.ext import ConversationHandler

logger = logging.getLogger(__name__)


def conv_cancel(bot, update, user_data):
    if 'to_delete' in user_data:
        for m_id in user_data['to_delete']:
            try:
                bot.delete_message(chat_id=user_data['user'].chat_id, message_id=m_id)
            except BadRequest:
                logger.error(f"Can't delete message with id {m_id}")

    bot.send_message(chat_id=update.message.chat_id, text=f"Вы отменили операцию", reply_markup=user_data['markup'])
    user_data.clear()
    return ConversationHandler.END


def conv_fallback(bot, update, user_data):
    if 'to_delete' in user_data:
        for m_id in user_data['to_delete']:
            try:
                bot.delete_message(chat_id=user_data['user'].chat_id, message_id=m_id)
            except BadRequest:
                logger.error(f"Can't delete message with id {m_id}")

    if 'markup' in user_data:
        bot.send_message(chat_id=update.message.chat_id, text=f"Что-то пошло не так, попробуйте снова", reply_markup=user_data['markup'])
    else:
        bot.send_message(chat_id=update.message.chat_id, text=f"Что-то пошло не так, попробуйте снова\nНапишите /start для сброса")
    user_data.clear()
    return ConversationHandler.END


def conv_success(bot, update, user_data):
    if 'to_delete' in user_data:
        for m_id in user_data['to_delete']:
            try:
                bot.delete_message(chat_id=user_data['user'].chat_id, message_id=m_id)
            except BadRequest:
                logger.error(f"Can't delete message with id {m_id}")

    user_data.clear()
    return ConversationHandler.END
