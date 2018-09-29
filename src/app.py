import pprint

import coloredlogs
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, filters

from src import custom_filters
from src.handlers.add_edit import *
from src.handlers.close import *
from src.handlers.delete import *
from src.handlers.interface_buttons_query import *
from src.handlers.notifications import *
from src.handlers.open import *
from src.handlers.resend import *
from src.handlers.search import *
from src.handlers.start import *
from src.models import User
from src.settings import BOT_TOKEN, exm_mark_emo, DISTRIBUTION_COMMAND


# FUNCTIONS

def error(bot, update, error):
    """Log Errors caused by Updates."""
    pp = pprint.PrettyPrinter(indent=4)
    logger.error(f'Update "{pp.pformat(str(update))}" caused error "{error}"')


def stop(bot, update):
    user = DBSession.query(User).filter(User.chat_id == update.message.chat_id).first()

    if user:
        DBSession.delete(user)
        bot.send_message(chat_id=user.chat_id, text="Now all information about you, %s, are deleted.")
        bot.send_message(chat_id=user.chat_id, text="Have a good day.")
    else:
        bot.send_message(chat_id=user.chat_id, text="Sorry, i don't know who you are, please send me \"/start\"")


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def main():
    bot = telegram.Bot(token=BOT_TOKEN)
    updater = Updater(token=BOT_TOKEN)
    j = updater.job_queue
    dispatcher = updater.dispatcher
    coloredlogs.install()

    start_handler = ConversationHandler(entry_points=[CommandHandler('start', start_entry, pass_user_data=True)],
                                        states={
                                            StartStates.FIRST_LOAD: [MessageHandler(filters.Filters.document, start_state_load, pass_user_data=True)],
                                            StartStates.KEY: [CallbackQueryHandler(start_state_key, pass_user_data=True)],
                                            StartStates.PASSWORD: [CallbackQueryHandler(start_state_password, pass_user_data=True)],
                                        },
                                        fallbacks=[MessageHandler(filters.Filters.all, conv_fallback, pass_user_data=True)])

    open_handler = ConversationHandler(entry_points=[CallbackQueryHandler(open_entry, pattern=r"open_db_.*", pass_user_data=True), CommandHandler('open', open_entry, pass_user_data=True)],
                                       states={
                                           OpenStates.KEY: [MessageHandler(filters.Filters.document, open_state_key, pass_user_data=True)],
                                           OpenStates.PASSWORD: [MessageHandler(filters.Filters.text, open_state_password, pass_user_data=True)],
                                       },
                                       fallbacks=[MessageHandler(filters.Filters.all, conv_fallback, pass_user_data=True)])

    nots_handler = ConversationHandler(entry_points=[CommandHandler('notifications', nots_entry, pass_user_data=True)],
                                       states={
                                           NotsStates.QUERY: [CallbackQueryHandler(nots_state_query, pattern=r'nots_.*', pass_user_data=True)],
                                       },
                                       fallbacks=[MessageHandler(filters.Filters.all, conv_fallback, pass_user_data=True)])

    delete_handler = CommandHandler('delete', delete_database)

    stop_handler = CommandHandler('stop', stop)

    message_in_create_handler = MessageHandler(custom_filters.is_user_in_create_state, message_in_add_edit)

    create_new_handler = CommandHandler("create", create)

    search_handler = CommandHandler("search", search)

    resend_interface_handler = CommandHandler("resend", resend_interface)

    interface_buttons_handler = CallbackQueryHandler(interface_buttons_query, pass_user_data=True)

    download_database_handler = CommandHandler("download", download_db)

    create_query_handler = CallbackQueryHandler(add_edit_query, pattern=r"create_.*")

    close_handler = CommandHandler('close', close_db, pass_user_data=True)

    unknown_handler = MessageHandler(Filters.all, unknown)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(stop_handler)
    dispatcher.add_handler(open_handler)
    dispatcher.add_handler(search_handler)
    dispatcher.add_handler(download_database_handler)
    dispatcher.add_handler(nots_handler)
    dispatcher.add_handler(close_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(resend_interface_handler)
    dispatcher.add_handler(create_new_handler)
    dispatcher.add_handler(message_in_create_handler)
    dispatcher.add_handler(create_query_handler)
    dispatcher.add_handler(interface_buttons_handler)
    dispatcher.add_handler(unknown_handler)
    dispatcher.add_error_handler(error)

    # Start bot
    if not os.path.exists(TEMP_FOLDER):
        os.mkdir(TEMP_FOLDER)
        logger.info("Temp folder created")
    logger.info("Bot started")
    updater.start_polling(timeout=30)
    updater.idle()

    """Stoping bot and closing all databases"""
    logging.info("Stoping bot...")

    for user in DBSession.query(User).filter(User.active == True).filter(User.is_opened == True).all():
        try:
            kd = KeepassDatabases()
            kd.opened_databases[user.chat_id].close()
            bot.send_message(chat_id=user.chat_id, text="Bot restarting...\n Your database closed.")
            close_db(bot, None, {'user': user})
            user.is_opened = False
            save_object(user)
        except (telegram.error.BadRequest, telegram.error.Unauthorized) as e:
            logger.error(f"Can't send message to {user.username if user.username else 'Someone'} because:\n{str(e)}")
        except KeyError as exc:
            logging.error("Key error: " + str(exc))


if __name__ == "__main__":
    main()
