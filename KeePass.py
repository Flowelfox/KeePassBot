from abc import ABC, abstractmethod

import libkeepass
import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from Models import User
from settings import *


class BaseKeePass(ABC):

    def __init__(self,root,parent):
        self._root = root
        self._parent = parent
        self.page = 1
        self.size = 0
        self.is_active = False
        self.active_item = None

    def next_page(self):

        if self.page < self.size / NUMBER_OF_ENTRIES_ON_PAGE:
            self.page += 1
        else:
            self.page = 1

    def previous_page(self):

        if self.page > 1:
            self.page -= 1
        else:
            self.page = int(math.ceil(self.size / NUMBER_OF_ENTRIES_ON_PAGE))


    def activate(self):
        self._root.active_item = self
        self.is_active = True

    def deactivate(self):
        self._root.active_item = self._parent
        self.is_active = False


class KeePass(BaseKeePass):
    def __init__(self, path):
        super().__init__(self,self)
        self.name = "KeePassBot"
        self.type = "Group"
        self.active_item = self
        self.is_active = True
        self.path = path
        self.opened = False
        self.items = []

    def __str__(self):
        if not self.opened:
            raise IOError("Databse not opened")

        string = ""
        for item in self.items:
            string += str(item)

        return string

    def __init_items(self):
        if not self.opened:
            raise IOError("Databse not opened")

        for item in self._root_obj.findall('./Root/Group/Group'):
            self.items.append(KeeGroup(self,self, item))
            self.size += 1

    def __generate_keyboard(self):
        if not self.opened:
            raise IOError("Databse not opened")

        message_buttons = []

        message_buttons.append(
            [InlineKeyboardButton(text=arrow_left_emo, callback_data="Left"),
             InlineKeyboardButton(text=arrow_up_emo, callback_data="Back"),
             InlineKeyboardButton(text=lock_emo, callback_data="Lock"),
             InlineKeyboardButton(text=arrow_right_emo, callback_data="Right")])


        if self.active_item and self.active_item.type == "Entry":
            InlineKeyboardMarkup(message_buttons)
        else:
            i = 0
            for item in self.active_item.items:
                if self.active_item.page * NUMBER_OF_ENTRIES_ON_PAGE >= i >= self.active_item.page * NUMBER_OF_ENTRIES_ON_PAGE - NUMBER_OF_ENTRIES_ON_PAGE:
                    message_buttons.append([InlineKeyboardButton(text=item.name, callback_data=item.uuid)])
                i += 1

        return InlineKeyboardMarkup(message_buttons)

    def close(self):
        self.kdb.close()

    def open(self,username,password=None,keyfile_path = None):
        user = User.get_or_none(username=username)

        try:
            with libkeepass.open(filename=self.path, password=password,keyfile=keyfile_path, unprotect=False) as kdb:
                self.kdb = kdb
                user.is_opened = True
                user.save()
                self._root_obj = kdb.obj_root

                self.opened = True
                self.__init_items()
                self.uuid = self._root_obj.find('./Root/Group')

        except IOError:
            raise IOError("Master key or key-file wrong")

    def get_message(self):
        if not self.opened:
            raise IOError("Database not opened")

        message_text = ""

        if self.active_item.type == "Entry":
            message_text += "_______" + key_emo + self.active_item.name + "_______" + new_line
            i = 0
            for string in self.active_item.strings:
                if self.active_item.page * NUMBER_OF_ENTRIES_ON_PAGE >= i >= self.active_item.page * NUMBER_OF_ENTRIES_ON_PAGE - NUMBER_OF_ENTRIES_ON_PAGE:
                    try:
                        message_text += str(string) + new_line
                    except TypeError:
                        continue
                i += 1
            if i > NUMBER_OF_ENTRIES_ON_PAGE:
                message_text += "_______Page {0} of {1}_______".format(self.active_item.page, int(math.ceil(self.active_item.size / NUMBER_OF_ENTRIES_ON_PAGE))) + new_line
            else:
                message_text += "_______Page {0} of {1}_______".format(self.active_item.page, 1) + new_line

        if self.active_item.type == "Group":

            message_text += "_______" + self.active_item.name + "_______" + new_line
            i = 0
            for item in self.active_item.items:
                if self.active_item.page * NUMBER_OF_ENTRIES_ON_PAGE >= i >= self.active_item.page * NUMBER_OF_ENTRIES_ON_PAGE - NUMBER_OF_ENTRIES_ON_PAGE:
                    if item.type == "Entry":
                        message_text += key_emo + str(item) + new_line
                    if item.type == "Group":
                        message_text += folder_emo + str(item) + new_line
                i += 1
            if i > NUMBER_OF_ENTRIES_ON_PAGE:
                message_text += "_______Page {0} of {1}_______".format(self.active_item.page, int(math.ceil(self.active_item.size / NUMBER_OF_ENTRIES_ON_PAGE))) + new_line
            else:
                message_text += "_______Page {0} of {1}_______".format(self.active_item.page, 1) + new_line


        message_markup = self.__generate_keyboard()

        return message_text, message_markup

    def search_item(self, word):
        if not self.opened:
            raise IOError("Databse not opened")

        finded_items = []

        def __inner_find(parent_item):
            if word.lower() in parent_item.name.lower() :
                finded_items.append(parent_item)
            for item in parent_item.items:
                if item.type == "Group":
                    __inner_find(item)
                if word.lower() in item.name.lower():
                    finded_items.append(item)

        __inner_find(self)

        return finded_items

    def get_item_by_uuid(self, word):
        if not self.opened:
            raise IOError("Databse not opened")

        def __inner_find(parent_item):
            if parent_item.uuid == word:
                return parent_item
            for item in parent_item.items:
                if item.type == "Group":
                    finded_elem = __inner_find(item)
                    if finded_elem:
                        return finded_elem
                if item.uuid == word:
                    return item

        return __inner_find(self)



    def search(self,word):
        finded_items = self.search_item(word)

        temp_group = KeeGroup(self,self,None,fake=True,items=finded_items)

        while self.active_item != self:
            self.active_item.deactivate()

        temp_group.activate()


class KeeGroup(BaseKeePass):
    def __init__(self, root, parent,group_obj,fake=False,items=None):
        super().__init__(root,parent)
        if fake:
            self.type = "Group"
            self.name = "Search"
            self.uuid = None
            self.notes = None
            self.icon_id = None
            self.items = items
            for item in self.items:
                item._parent = self
                item._root = root
        else:
            self.type = "Group"
            self._group_obj = group_obj
            self.name = group_obj.Name.text
            self.uuid = group_obj.UUID.text
            self.notes = group_obj.Notes.text
            self.icon_id = int(group_obj.IconID.text)
            self.items = []
            self.__init_entries()
            self.__init_groups()

    def __str__(self):
        return self.name

    def __init_entries(self):
        for entry in self._group_obj.findall('Entry'):
            self.items.append(KeeEntry(self._root,self, entry))
            self.size += 1

    def __init_groups(self):
        for group in self._group_obj.findall('Group'):
            self.items.append(KeeGroup(self._root,self, group))
            self.size += 1


class KeeEntry(BaseKeePass):
    def __init__(self, root,parent, entry_obj):
        super().__init__(root,parent)
        self.type = "Entry"
        self._entry_obj = entry_obj
        self.uuid = entry_obj.UUID.text
        self.icon_id = int(entry_obj.IconID.text)
        self.strings = []
        self.__init_strings()
        self.__set_name()
        self.__set_password()

    def __str__(self):
        return self.name

    def __init_strings(self):
        for string in self._entry_obj.findall('String'):
            self.strings.append(EntryString(string))
            self.size += 1

    def __set_name(self):
        for string in self.strings:
            if string.key == "Title":
                self.name = string.value

    def __set_password(self):
        for string in self.strings:
            if string.key == "Password":
                self.password = string.value

    def next_page(self):
        if self.page < self.size / NUMBER_OF_ENTRIES_ON_PAGE:
            self.page += 1
        else:
            raise IOError("Already last page")

    def previous_page(self):
        if self.page > 1:
            self.page -= 1
        else:
            raise IOError("Already first page")


class EntryString():
    def __init__(self, string_obj):
        self._string_obj = string_obj
        self.key = string_obj.Key.text
        self.value = string_obj.Value.text

    def __str__(self):
        return self.key + " = " + self.value
