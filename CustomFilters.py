#FILTERS
from telegram.ext import BaseFilter

from Models import User


class UserExists(BaseFilter):
    def filter(self, message):
        user = User.get_or_none(username=message.from_user.name)
        return bool(user)

class PasswordDatabaseExist(BaseFilter):
    def filter(self, message):
        user = User.get_or_none(username=message.from_user.name)
        if user:
            return bool(user.file)
        else:
            return False

class IsDatabaseOpened(BaseFilter):
    def filter(self, message):
        user = User.get_or_none(username=message.from_user.name)

        return user.is_opened

class IsUserInCreateState(BaseFilter):
    def filter(self, message):
        user = User.get_or_none(username=message.from_user.name)

        return user.create_state


class IsDatabaseFile(BaseFilter):
    def filter(self, message):
        return message.document.file_name.endswith(".kdbx")




user_exists = UserExists()
password_database_exist = PasswordDatabaseExist()
is_database_opened = IsDatabaseOpened()
is_database_file = IsDatabaseFile()
is_user_in_create_state = IsUserInCreateState()