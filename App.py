import datetime
import libkeepass
import os

import math
import telegram
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter, CallbackQueryHandler
import logging
import xml.dom.minidom as minidom

from KeePass import KeePass
from Models import User
import CustomFilters
from settings import *

bot = telegram.Bot(token=BOT_TOKEN)
updater = Updater(token=BOT_TOKEN)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

opened_databases = {}

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

#FUNCTIONS
def start(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    print(user)
    if not user:
        user = User(username=update.message.from_user.name,join_date=datetime.datetime.now())
        user.save()
        bot.send_message(chat_id=update.message.chat_id, text="Hi %s, now you registered." % user.username)
        bot.send_message(chat_id=update.message.chat_id, text="If you want remove all information about you send me \"/stop\".")
        bot.send_message(chat_id=update.message.chat_id, text="Please send me database file for start")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Hi again, %s, you already registered." % user.username)
        bot.send_message(chat_id=update.message.chat_id, text="If you want remove all information about you send me \"/stop\".")






def stop(bot,update):
    user = User.get_or_none(username=update.message.from_user.name)
    if user:
        User.delete().where(User.username == update.message.from_user.name).execute()
        bot.send_message(chat_id=update.message.chat_id, text="Now all information about you, %s, are deleted.")
        bot.send_message(chat_id=update.message.chat_id, text="Have a good day.")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Sorry, i don't know who you are, please send me \"/start\"")

def search(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)

    keepass = opened_databases[update.message.from_user.name]

    keepass.search(update.message.text.replace("/search ",""))

    message_text, message_markup = keepass.get_message()

    bot.edit_message_text(chat_id=update.message.chat_id,
                          message_id=user.interface_message_id,
                          text=message_text,
                          reply_markup=message_markup)

def database_add(bot,update):

    """Creating folder"""
    if not os.path.exists(TEMP_FOLDER):
        os.mkdir(TEMP_FOLDER)

    """Downloading file"""
    file_id = update.message.document.file_id
    f = bot.get_file(file_id)
    f.download(TEMP_FOLDER + '/' + file_id + '.kdbx')

    """Saving to database"""
    user = User.get_or_none(username=update.message.from_user.name)
    with open(TEMP_FOLDER + '/' + file_id + '.kdbx','rb+') as file:
        user.file = file.read()
        user.save()

    """Removing downloaded file"""
    os.remove(TEMP_FOLDER + '/' + file_id + '.kdbx')

    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Yes",callback_data="YesKey"),InlineKeyboardButton(text="No",callback_data="NoKey")]])
    bot.send_message(chat_id=update.message.chat_id, text="Did you need file-key for openning you database?", reply_markup=markup )

def database_not_exist(bot,update):
    bot.send_message(chat_id=update.message.chat_id, text="Please send me database file")

def not_opened(bot,update):
    user = User.get_or_none(username=update.message.from_user.name)

    """Getting file-key"""
    if user.key_file_needed and not os.path.exists(TEMP_FOLDER + '/' + update.message.from_user.name + '.key'):
        if not update.message.document:
            bot.send_message(chat_id=update.message.chat_id, text="Please send me key-file first")
            return

        if update.message.document:
            file_id = update.message.document.file_id
            f = bot.get_file(file_id)
            f.download(TEMP_FOLDER + '/' + update.message.from_user.name + '.key')
            bot.send_message(chat_id=update.message.chat_id, text="Now send me your password")
            return


    """Creating file in temp"""
    with open(TEMP_FOLDER + '/' + update.message.from_user.name + '.kdbx', 'wb+') as file:
        file.write(user.file)

    """Trying to open database"""
    keepass = KeePass(TEMP_FOLDER + '/' + update.message.from_user.name + '.kdbx')
    try:
        if user.password_needed and user.key_file_needed:
            keepass.open(username=update.message.from_user.name, password=update.message.text, keyfile_path=TEMP_FOLDER + '/' + update.message.from_user.name + '.key')
        elif user.password_needed and not user.key_file_needed:
            keepass.open(username=update.message.from_user.name, password=update.message.text)
        elif not user.password_needed and user.key_file_needed:
            keepass.open(username=update.message.from_user.name,keyfile_path=TEMP_FOLDER + '/' + update.message.from_user.name + '.key')

        global opened_databases
        opened_databases.update({update.message.from_user.name: keepass})
        message_text, message_markup = keepass.get_message()
        interface_message = bot.send_message(chat_id=update.message.chat_id, text=message_text, reply_markup=message_markup)
        bot.send_message(chat_id=update.message.chat_id, text=exm_mark_emo * 2 + "PLEASE REMOVE YOUR PASSWORD FROM HISTORY" + exm_mark_emo * 2)

        user.is_opened = True
        user.interface_message_id = interface_message.message_id
        user.save()


    except IOError as e:
        bot.send_message(chat_id=update.message.chat_id, text=str(e))

    """Removing file in temp"""
    os.remove(TEMP_FOLDER + '/' + update.message.from_user.name + '.kdbx')
    os.remove(TEMP_FOLDER + '/' + update.message.from_user.name + '.key')

    """Sending message"""
    if not user.is_opened:
        if user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.message.chat_id, text="Please send me key-file and then password to open database")
        elif user.password_needed and not user.key_file_needed:
            bot.send_message(chat_id=update.message.chat_id, text="Send me password to open database")
        elif not user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.message.chat_id, text="Send me key-file to open database")



def show_group(bot,update):
    data = update.callback_query.data
    user = User.get_or_none(username=update.callback_query.from_user.name)
    #File-key for database
    if data == "NoKey" or data == "YesKey":

        if data == "NoKey":
            user.key_file_needed = False
        if data == "YesKey":
            user.key_file_needed = True

        user.save()
        bot.answer_callback_query(update.callback_query.id)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Yes", callback_data="YesPassword"),
                                        InlineKeyboardButton(text="No", callback_data="NoPassword")]])
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Did you need password for openning you database?",
                         reply_markup=markup)
        return

    if data == "NoPassword" or data == "YesPassword":
        if data == "NoPassword":
            user.password_needed = False
        if data == "YesPassword":
            user.password_needed = True
        user.save()
        bot.answer_callback_query(update.callback_query.id)

        if user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id,
                             text="Please send me key-file and then password to open database")
        elif user.password_needed and not user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id, text="Send me password to open database")
        elif not user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id, text="Send me key-file to open database")

        return






    keepass = opened_databases[update.callback_query.from_user.name]


    if data == "Lock":
        keepass.close()

        user.is_opened = False
        user.save()
        bot.send_message(chat_id=update.callback_query.message.chat_id, text="Database closed")
        if user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id, text="Please send me key-file and then password to open database")
        elif user.password_needed and not user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id, text="Send me password to open database")
        elif not user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id, text="Send me key-file to open database")

        bot.answer_callback_query(update.callback_query.id)
        return

    try:
        if data == "Left":
            if keepass.active_item:
                keepass.active_item.previous_page()
            else:
                keepass.previous_page()
        if data == "Right":
            if keepass.active_item:
                keepass.active_item.next_page()
            else:
                keepass.next_page()
    except IOError:
        bot.answer_callback_query(update.callback_query.id)
        return



    if data == "Back":
        if keepass.active_item:
            keepass.active_item.deactivate()
        else:
            bot.answer_callback_query(update.callback_query.id)
            return

    if len(data) == 24:
        keepass.get_item_by_uuid(data).activate()

    message_text, message_markup = keepass.get_message()
    try:
        bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=message_text,
                              reply_markup=message_markup)

    except Exception as e:
        print(e)

    bot.answer_callback_query(update.callback_query.id)

def close(bot,update):
    try:
        global opened_databases
        opened_databases[update.message.from_user.name].close()
    except KeyError as e:
        logging.error("Key error: " + str(e))

    user = User.get_or_none(username=update.message.from_user.name)
    user.is_opened = False
    user.save()

    bot.send_message(chat_id=update.message.chat_id, text="Database closed")
    if user.password_needed and user.key_file_needed:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Please send me key-file and then password to open database")
    elif user.password_needed and not user.key_file_needed:
        bot.send_message(chat_id=update.message.chat_id, text="Send me password to open database")
    elif not user.password_needed and user.key_file_needed:
        bot.send_message(chat_id=update.message.chat_id, text="Send me key-file to open database")

def delete_database(bot,update):
    user = User.get_or_none(username=update.message.from_user.name)
    if user.is_opened:
        bot.send_message(chat_id=update.message.chat_id, text="Your database in use, first close it with \"/close\"")
    else:
        user.file = None
        user.save()
        bot.send_message(chat_id=update.message.chat_id, text="Your database was deleted")

def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


delete_handler = CommandHandler('delete', delete_database,filters=CustomFilters.password_database_exist)

start_handler = CommandHandler('start', start)
stop_handler = CommandHandler('stop', stop)

#user not exists
not_exists_handler = MessageHandler(~ CustomFilters.user_exists,start)

#user exists
#not document
#db not exist
database_not_exist_handler = MessageHandler(CustomFilters.user_exists & ~ Filters.document & ~ CustomFilters.password_database_exist, database_not_exist)

#user exists
#maybe document
#db exist
#not opened
not_opened_handler = MessageHandler(CustomFilters.user_exists & CustomFilters.password_database_exist & (~ CustomFilters.is_database_opened) , not_opened)

#user exists
#document
#is database file
#not exist
database_add_handler = MessageHandler(CustomFilters.user_exists & Filters.document & CustomFilters.is_database_file  & (~ CustomFilters.password_database_exist), database_add)


#user exists
#not document
#db exist
#opened
search_handler = CommandHandler("search", search, filters=CustomFilters.user_exists & CustomFilters.password_database_exist & CustomFilters.is_database_opened)

show_group_handler = CallbackQueryHandler(show_group)
#db exists
#opened
close_handler = CommandHandler('close', close,filters=CustomFilters.password_database_exist & CustomFilters.is_database_opened)

unknown_handler = MessageHandler(Filters.all, unknown)


dispatcher.add_handler(stop_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(not_exists_handler)
dispatcher.add_handler(database_not_exist_handler)
dispatcher.add_handler(not_opened_handler)
dispatcher.add_handler(database_add_handler)
dispatcher.add_handler(search_handler)
dispatcher.add_handler(show_group_handler)
dispatcher.add_handler(close_handler)
dispatcher.add_handler(unknown_handler)


updater.start_polling(poll_interval=1.0)
updater.idle()

"""Stoping bot and closing all databases"""
print("Stoping bot...")


users = User.select().where(User.is_opened==True)
for user in users:
    try:
        opened_databases[user.username].close()
    except KeyError as e:
        logging.error("Key error: " + str(e))


    user.is_opened = False
    user.save()



