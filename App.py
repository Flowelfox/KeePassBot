import datetime
import logging
import os

import telegram
from io import StringIO, BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

import CustomFilters
from KeePass import KeePass, ItemType
from Models import User
from settings import *

bot = telegram.Bot(token=BOT_TOKEN)
updater = Updater(token=BOT_TOKEN)
j = updater.job_queue
distribution_text = ""
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def set_chat_id(function):
    def wrapper(*args, **kwargs):
        update = args[1]

        if not update.message.from_user.name.endswith('bot'):
            user = User.get_or_none(username=update.message.from_user.name)
            if user.chat_id == 0:
                user.chat_id = update.message.chat_id
                user.save()
        function(*args, **kwargs)

    return wrapper


# FUNCTIONS
def start(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    print(user)
    if not user:
        user = User(username=update.message.from_user.name, join_date=datetime.datetime.now(),
                    chat_id=update.message.chat_id)
        user.save()
        bot.send_message(chat_id=update.message.chat_id, text="Hi %s, now you registered." % user.username)
        bot.send_message(chat_id=update.message.chat_id,
                         text="If you want remove all information about you send me \"/stop\".")
        bot.send_message(chat_id=update.message.chat_id, text="Please send me database file for start")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Hi again, %s, you already registered." % user.username)
        bot.send_message(chat_id=update.message.chat_id,
                         text="If you want remove all information about you send me \"/stop\".")


def stop(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    if user:
        User.delete().where(User.username == update.message.from_user.name).execute()
        bot.send_message(chat_id=update.message.chat_id, text="Now all information about you, %s, are deleted.")
        bot.send_message(chat_id=update.message.chat_id, text="Have a good day.")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sorry, i don't know who you are, please send me \"/start\"")


def search(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)

    keepass = opened_databases[update.message.from_user.name]

    keepass.search(update.message.text.replace("/search ", ""))

    message_text, message_markup = keepass.get_message()

    bot.edit_message_text(chat_id=update.message.chat_id,
                          message_id=user.interface_message_id,
                          text=message_text,
                          reply_markup=message_markup)


def database_add(bot, update):
    """Creating folder"""
    if not os.path.exists(TEMP_FOLDER):
        os.mkdir(TEMP_FOLDER)

    """Downloading file"""
    file_id = update.message.document.file_id
    f = bot.get_file(file_id)
    f.download(TEMP_FOLDER + '/' + file_id + '.kdbx')

    """Saving to database"""
    user = User.get_or_none(username=update.message.from_user.name)
    with open(TEMP_FOLDER + '/' + file_id + '.kdbx', 'rb+') as file:
        user.file = file.read()
        user.save()

    """Removing downloaded file"""
    os.remove(TEMP_FOLDER + '/' + file_id + '.kdbx')

    markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Yes", callback_data="YesKey"),
                                    InlineKeyboardButton(text="No", callback_data="NoKey")]])
    bot.send_message(chat_id=update.message.chat_id, text="Did you need file-key for openning you database?",
                     reply_markup=markup)


def database_not_exist(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Please send me database file")


def not_opened(bot, update):
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
            keepass.open(username=update.message.from_user.name, password=update.message.text,
                         keyfile_path=TEMP_FOLDER + '/' + update.message.from_user.name + '.key')
        elif user.password_needed and not user.key_file_needed:
            keepass.open(username=update.message.from_user.name, password=update.message.text)
        elif not user.password_needed and user.key_file_needed:
            keepass.open(username=update.message.from_user.name,
                         keyfile_path=TEMP_FOLDER + '/' + update.message.from_user.name + '.key')

        global opened_databases
        opened_databases.update({update.message.from_user.name: keepass})
        message_text, message_markup = keepass.get_message()
        interface_message = bot.send_message(chat_id=update.message.chat_id, text=message_text,
                                             reply_markup=message_markup)

        if user.notification:
            bot.send_message(chat_id=update.message.chat_id,
                             text=exm_mark_emo * 2 + "PLEASE REMOVE YOUR PASSWORD FROM HISTORY" + exm_mark_emo * 2)

        user.is_opened = True
        user.interface_message_id = interface_message.message_id
        user.save()


    except IOError as e:
        bot.send_message(chat_id=update.message.chat_id, text=str(e))

    """Removing file in temp"""
    os.remove(TEMP_FOLDER + '/' + update.message.from_user.name + '.kdbx')
    if user.key_file_needed:
        os.remove(TEMP_FOLDER + '/' + update.message.from_user.name + '.key')

    """Sending message"""
    if not user.is_opened:
        if user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Please send me key-file and then password to open database")
        elif user.password_needed and not user.key_file_needed:
            bot.send_message(chat_id=update.message.chat_id, text="Send me password to open database")
        elif not user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.message.chat_id, text="Send me key-file to open database")


def show_group(bot, update):
    data = update.callback_query.data
    user = User.get_or_none(username=update.callback_query.from_user.name)
    chat = bot.getChat(update.callback_query.message.chat_id)

    if data == "Nothing":
        bot.answer_callback_query(update.callback_query.id)
        return
    if data == "Resend":
        keepass = opened_databases[f'@{chat.username}']

        # delete previous
        try:
            bot.delete_message(chat_id=update.callback_query.message.chat_id, message_id=user.interface_message_id)
        except Exception as e:
            print(e)

        # send new
        message_text, message_markup = keepass.get_message()
        interface_message = bot.send_message(chat_id=update.callback_query.message.chat_id, text=message_text,
                                             reply_markup=message_markup)

        user.interface_message_id = interface_message.message_id
        user.save()

    if data == "Download":
        keepass = opened_databases[f'@{chat.username}']

        """Write to new memory file"""
        output = BytesIO()
        output.write(user.file)
        output.name = keepass.root_group.name + '.kdbx'
        output.seek(0)

        """Send to user"""
        bot.send_document(chat_id=chat.id,  document=output)
        bot.send_message(chat_id=chat.id,  text=exm_mark_emo * 2 + "PLEASE REMOVE DATABASE FILE FROM HISTORY" + exm_mark_emo * 2,)
        bot.answer_callback_query(update.callback_query.id)
        return

    # File-key for database
    if data == "NoKey" or data == "YesKey":

        if data == "NoKey":
            user.key_file_needed = False
        if data == "YesKey":
            user.key_file_needed = True

        user.save()
        bot.answer_callback_query(update.callback_query.id)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Yes", callback_data="YesPassword"),
                                        InlineKeyboardButton(text="No", callback_data="NoPassword")]])
        bot.send_message(chat_id=update.callback_query.message.chat_id,
                         text="Did you need password for openning you database?",
                         reply_markup=markup)
        return

    if data == "NoPassword" or data == "YesPassword":
        if data == "NoPassword":
            user.password_needed = False
        if data == "YesPassword":
            user.password_needed = True
        user.save()
        bot.answer_callback_query(update.callback_query.id)

        bot.send_message(chat_id=update.callback_query.message.chat_id,
                         text=exm_mark_emo * 2 + "PLEASE REMOVE DATABASE FILE FROM HISTORY" + exm_mark_emo * 2)

        if user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id,
                             text="Please send me key-file and then password to open database")
        elif user.password_needed and not user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id, text="Send me password to open database")
        elif not user.password_needed and user.key_file_needed:
            bot.send_message(chat_id=update.callback_query.message.chat_id, text="Send me key-file to open database")

        return
    try:
        keepass = opened_databases[update.callback_query.from_user.name]
    except KeyError as e:
        logging.error("Key error: " + str(e))
        bot.answer_callback_query(update.callback_query.id)
        return

    if data == "Lock":
        close_proces(update.callback_query.from_user.name, update.callback_query.message.chat_id)

        bot.answer_callback_query(update.callback_query.id)
        return

    try:
        if data == "Left":
            KeePass.active_item.previous_page()
        if data == "Right":
            KeePass.active_item.next_page()
    except IOError:
        bot.answer_callback_query(update.callback_query.id)
        return

    if data == "Back":
        if KeePass.active_item:
            KeePass.active_item.deactivate()
        else:
            bot.answer_callback_query(update.callback_query.id)
            return

    if data.startswith("Edit_"):
        if KeePass.active_item:
            uuid = data.replace("Edit_", "")
            if len(uuid) == 24:
                message_text, message_markup = keepass.start_add_edit(obj=keepass.get_item_by_uuid(uuid))
                # Entering in create state
                user = keepass.get_user()
                user.create_state = True
                user.save()

                try:
                    bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                                          message_id=user.interface_message_id,
                                          text=message_text,
                                          reply_markup=message_markup,
                                          parse_mode=telegram.ParseMode.HTML)
                except Exception as e:
                    print(e)

                if user.notification:
                    bot.send_message(chat_id=update.message.chat_id,
                                     text="Click on the field name to set the value for it.\nSend the text to set the value.\nBold fields are required.\nYou can use the arrows buttons to switch between fields.")
            else:
                bot.send_message(chat_id=update.message.chat_id, text="Wrong edit uuid, try again.\nIf the problem persists, please write to administrator")

        bot.answer_callback_query(update.callback_query.id)
        return

    if data == "ReallyDelete":
        if KeePass.active_item:
            KeePass.active_item.delete()
        else:
            bot.answer_callback_query(update.callback_query.id)
            return

    if data == "NoDelete":
        try:
            del KeePass.active_item.really_delete
        except AttributeError:
            pass
        message_text, message_markup = keepass.get_message()
        try:
            bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=message_text,
                                  reply_markup=message_markup)

        except Exception as e:
            print(e)
        bot.answer_callback_query(update.callback_query.id)
        return

    if data == "Delete":
        KeePass.active_item.really_delete = True
        message_text, message_markup = keepass.get_message()
        try:
            bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=message_text,
                                  reply_markup=message_markup)

        except Exception as e:
            print(e)

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


# create item function
def create(bot, update):
    args = update.message.text.replace('/create ', '')

    keepass = opened_databases[update.message.from_user.name]
    if args.lower() in "group":
        message_text, message_markup = keepass.start_add_edit(ItemType.GROUP)
    elif args.lower() in "entry":
        message_text, message_markup = keepass.start_add_edit(ItemType.ENTRY)
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Wrong arguments, choices are: 'Entry', 'Group', 'e', 'g'\nExample: /create Group")
        return
    # Entering in create state
    user = User.get_or_none(username=update.message.from_user.name)
    user.create_state = True
    user.save()

    try:
        bot.edit_message_text(chat_id=update.message.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup,
                              parse_mode=telegram.ParseMode.HTML)
    except Exception as e:
        print(e)

    if user.notification:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Click on the field name to set the value for it.\nSend the text to set the value.\nBold fields are required.\nYou can use the arrows buttons to switch between fields.")


# create querys handler
def create_query(bot, update):
    data = update.callback_query.data.replace("create_", "")
    keepass = opened_databases[update.callback_query.from_user.name]

    if data == "done":
        for field in keepass.add_edit_state.req_fields:
            if not keepass.add_edit_state.fields[field]:
                bot.send_message(chat_id=update.callback_query.message.chat_id,
                                 text="Please fill required fields")
                bot.answer_callback_query(update.callback_query.id)
                return

        keepass.finish_add_edit()

        user = User.get_or_none(username=update.callback_query.from_user.name)
        user.create_state = False
        user.save()

        message_text, message_markup = keepass.get_message()
        bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup)
        bot.answer_callback_query(update.callback_query.id)
        return

    elif data == "Back":
        user = User.get_or_none(username=update.callback_query.from_user.name)
        user.create_state = False
        user.save()

        keepass.finish_add_edit()

        message_text, message_markup = keepass.get_message()
        bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup)

        bot.answer_callback_query(update.callback_query.id)
        return
    elif data == "Left":
        keepass.add_edit_state.prev_field()
        bot.answer_callback_query(update.callback_query.id)
    elif data == "Right":
        keepass.add_edit_state.next_field()
        bot.answer_callback_query(update.callback_query.id)
    elif data == "generate_password":
        keepass.add_edit_state.generate_password()
    else:
        keepass.add_edit_state.set_cur_field(data)

    message_text, message_markup = keepass.add_edit_state.get_message()
    try:
        user = User.get_or_none(username=update.callback_query.from_user.name)
        bot.edit_message_text(chat_id=update.callback_query.message.chat_id,
                              message_id=user.interface_message_id,
                              text=message_text,
                              reply_markup=message_markup,
                              parse_mode=telegram.ParseMode.HTML)

    except Exception as e:
        print(e)

    bot.answer_callback_query(update.callback_query.id)


def message_in_create(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    keepass = opened_databases[update.message.from_user.name]

    # length check
    if len(update.message.text) > 40:
        bot.send_message(chat_id=update.message.chat_id,
                         text="New value too long. Please send text bellow 40 chars")
        return
    try:
        keepass.add_edit_state.set_cur_field_value(update.message.text)
        keepass.add_edit_state.next_field()
        message_text, message_markup = keepass.add_edit_state.get_message()
        try:
            bot.edit_message_text(chat_id=update.message.chat_id,
                                  message_id=user.interface_message_id,
                                  text=message_text,
                                  reply_markup=message_markup,
                                  parse_mode=telegram.ParseMode.HTML)

        except Exception as e:
            print(e)
    except AttributeError:
        user.create_state = False
        user.save()


@set_chat_id
def close(bot, update):
    username = update.message.from_user.name
    chat_id = update.message.chat_id
    close_proces(username, chat_id)


def close_proces(username, chat_id):
    try:
        opened_databases[username].close()
        del opened_databases[username]
    except KeyError as e:
        logging.error("Key error: " + str(e))

    user = User.get_or_none(username=username)
    user.is_opened = False
    user.save()
    try:
        bot.delete_message(chat_id=chat_id, message_id=user.interface_message_id)
    except Exception as e:
        print(e)

    bot.send_message(chat_id=chat_id, text="Database closed")
    if user.password_needed and user.key_file_needed:
        bot.send_message(chat_id=chat_id,
                         text="Please send me key-file and then password to open database")

    elif user.password_needed and not user.key_file_needed:
        bot.send_message(chat_id=chat_id, text="Send me password to open database")
    elif not user.password_needed and user.key_file_needed:
        bot.send_message(chat_id=chat_id, text="Send me key-file to open database")


def delete_database(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    if user.is_opened:
        bot.send_message(chat_id=update.message.chat_id, text="Your database in use, first close it with \"/close\"")
    else:
        user.file = None
        user.save()
        bot.send_message(chat_id=update.message.chat_id, text="Your database was deleted")


def toogle_notifications(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    user.notification = not user.notification
    user.save()
    if user.notification:
        bot.send_message(chat_id=update.message.chat_id, text="Notifications enabled.")
    else:
        bot.send_message(chat_id=update.message.chat_id, text="Notifications disabled.")


def resend_interface(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    keepass = opened_databases[update.message.from_user.name]

    # delete previous
    try:
        bot.delete_message(chat_id=update.message.chat_id, message_id=user.interface_message_id)
    except Exception as e:
        print(e)

    # send new
    message_text, message_markup = keepass.get_message()
    interface_message = bot.send_message(chat_id=update.message.chat_id, text=message_text,
                                         reply_markup=message_markup)

    user.interface_message_id = interface_message.message_id
    user.save()


def get_database(bot, update):
    user = User.get_or_none(username=update.message.from_user.name)
    keepass = opened_databases[update.message.from_user.name]

    """Write to new memory file"""
    output = BytesIO()
    output.write(user.file)
    output.name = keepass.root_group.name + '.kdbx'
    output.seek(0)

    """Send to user"""
    bot.send_document(chat_id=update.message.chat_id, text=exm_mark_emo * 2 + "PLEASE REMOVE DATABASE FILE FROM HISTORY" + exm_mark_emo * 2,  document=output)


@set_chat_id
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def stop_distribution(bot, update):
    if update.message.from_user.name != ADMINISTRATOR:
        bot.send_message(chat_id=update.message.chat_id, text="Sorry, only administrator can use this command")
        return
    j.stop()
    bot.send_message(chat_id=update.message.chat_id, text="Distribution job stopped.")


def distribution_cmd(bot, update):
    if update.message.from_user.name != ADMINISTRATOR:
        bot.send_message(chat_id=update.message.chat_id, text="Sorry, only administrator can use this command")
        return
    global distribution_text
    distribution_text = update.message.text.replace('/' + DISTRIBUTION_COMMAND + ' ', "")
    j.run_once(distribution, DISTRIBUTION_DELAY)


def distribution(bot, job):
    for usr in User.select().where(User.file != ""):
        if usr.chat_id != 0:
            bot.send_message(chat_id=usr.chat_id, text=distribution_text.replace('<br/>', '\n'))


delete_handler = CommandHandler('delete', delete_database, filters=CustomFilters.password_database_exist)

start_handler = CommandHandler('start', start)
stop_handler = CommandHandler('stop', stop)

distribution_handler = CommandHandler(DISTRIBUTION_COMMAND, distribution_cmd)
stop_distribution_handler = CommandHandler(DISTRIBUTION_STOP_COMMAND, stop_distribution)

# user not exists
not_exists_handler = MessageHandler(~ CustomFilters.user_exists, start)

# user exists
# not document
# db not exist
database_not_exist_handler = MessageHandler(
    CustomFilters.user_exists & ~ Filters.document & ~ CustomFilters.password_database_exist, database_not_exist)

# user exists
# maybe document
# db exist
# not opened
not_opened_handler = MessageHandler(
    CustomFilters.user_exists & CustomFilters.password_database_exist & (~ CustomFilters.is_database_opened),
    not_opened)

# user exists
# document
# is database file
# not exist
database_add_handler = MessageHandler(CustomFilters.user_exists & Filters.document & CustomFilters.is_database_file & (
    ~ CustomFilters.password_database_exist), database_add)

# user exists
# not document
# db exist
# opened
# in create state
message_in_create_handler = MessageHandler(
    CustomFilters.user_exists & CustomFilters.password_database_exist & CustomFilters.is_database_opened & CustomFilters.is_user_in_create_state,
    message_in_create)

# user exists
# db exist
# opened
create_item_handler = CommandHandler("create", create,
                                     filters=CustomFilters.user_exists & CustomFilters.password_database_exist & CustomFilters.is_database_opened)

# user exists
# db exist
# opened
search_handler = CommandHandler("search", search,
                                filters=CustomFilters.user_exists & CustomFilters.password_database_exist & CustomFilters.is_database_opened)
# user exists
# db exist
# opened
resend_interface_handler = CommandHandler("resend", resend_interface,
                                          filters=CustomFilters.user_exists & CustomFilters.password_database_exist & CustomFilters.is_database_opened)

# user exists
# db exist
get_database_handler = CommandHandler("download", get_database,
                                      filters=CustomFilters.user_exists & CustomFilters.password_database_exist)

create_query_handler = CallbackQueryHandler(create_query, pattern=r"create_.*")

show_group_handler = CallbackQueryHandler(show_group)

toogle_notifications_handler = CommandHandler('toogle_notifications', toogle_notifications)

# db exists
# opened
close_handler = CommandHandler('close', close,
                               filters=CustomFilters.password_database_exist & CustomFilters.is_database_opened)

unknown_handler = MessageHandler(Filters.all, unknown)

dispatcher.add_handler(stop_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(distribution_handler)
dispatcher.add_handler(stop_distribution_handler)
dispatcher.add_handler(toogle_notifications_handler)
dispatcher.add_handler(close_handler)
dispatcher.add_handler(delete_handler)
dispatcher.add_handler(not_exists_handler)
dispatcher.add_handler(database_not_exist_handler)
dispatcher.add_handler(not_opened_handler)
dispatcher.add_handler(database_add_handler)
dispatcher.add_handler(create_item_handler)
dispatcher.add_handler(message_in_create_handler)
dispatcher.add_handler(search_handler)
dispatcher.add_handler(resend_interface_handler)
dispatcher.add_handler(get_database_handler)
dispatcher.add_handler(create_query_handler)
dispatcher.add_handler(show_group_handler)
dispatcher.add_handler(unknown_handler)

updater.start_polling(poll_interval=0.5)
updater.idle()

"""Stoping bot and closing all databases"""
logging.info("Stoping bot...")

users = User.select().where(User.is_opened == True)
for userr in users:
    try:
        opened_databases[userr.username].close()
        if userr.chat_id != 0:
            bot.send_message(chat_id=userr.chat_id, text="Bot restarting...")
            close_proces(userr.username, userr.chat_id)
    except KeyError as e:
        logging.error("Key error: " + str(e))

    userr.is_opened = False
    userr.save()
