from telegram.ext import BaseFilter

from src.models import User, DBSession


class IsUserInCreateState(BaseFilter):
    def filter(self, message):
        user = DBSession.query(User).filter(User.chat_id == message.chat_id).first()
        return user.create_state


is_user_in_create_state = IsUserInCreateState()
