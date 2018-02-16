import base64
import uuid as uuidGenerator
from abc import ABC, abstractmethod
from pprint import pprint

import lxml
import os
from lxml.etree import Element, SubElement
from lxml import etree
from lxml import objectify

import datetime
import libkeepass
import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from Models import User
from settings import *


class BaseKeePass(ABC):

    def __init__(self, root, parent):
        self._root = root
        self._parent = parent
        self.page = 1
        self.size = 0
        self.type = None

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
        KeePass.active_item = self

    def deactivate(self):
        KeePass.active_item = self._parent

    def get_root(self):
        return self._root

    def get_parent(self):
        return self._parent

    def delete(self):
        raise NotImplemented("Implement this method in child")


class KeePass:
    active_item = None

    def __init__(self, path):
        self.name = "KeePassManager"
        self.type = "Manager"
        self.path = path
        self.opened = False
        self.create_state = None
        self.root_group = None
        self.username = None

    def __str__(self):
        if not self.opened:
            raise IOError("Databse not opened")

        return str(self.root_group)

    @staticmethod
    def get_active_item():
        return KeePass.active_item

    def get_user(self):
        return User.get_or_none(username=self.username)

    def __init_root_group(self):
        if not self.opened:
            raise IOError("Databse not opened")

        root_group = self._root_obj.find('./Root/Group')
        self.root_group = KeeGroup(self, None, root_group)

    def __generate_keyboard(self):
        if not self.opened:
            raise IOError("Databse not opened")

        message_buttons = []

        message_buttons.append(
            [InlineKeyboardButton(text=arrow_left_emo, callback_data="Left"),
             InlineKeyboardButton(text=arrow_up_emo, callback_data="Back"),
             InlineKeyboardButton(text=lock_emo, callback_data="Lock"),
             InlineKeyboardButton(text=arrow_right_emo, callback_data="Right")])

        if KeePass.get_active_item() and KeePass.get_active_item().type == "Entry":
            if getattr(KeePass.get_active_item(), 'really_delete', False):
                message_buttons.append([InlineKeyboardButton(text="Yes, I am sure" + x_emo, callback_data="ReallyDelete"),
                                        InlineKeyboardButton(text="No, keep it" + back_emo, callback_data="NoDelete")])
            else:
                message_buttons.append([InlineKeyboardButton(text=x_emo + "Delete" + x_emo, callback_data="Delete")])
            InlineKeyboardMarkup(message_buttons)
        else:
            i = 0
            if KeePass.get_active_item() != self.root_group:
                if getattr(KeePass.get_active_item(), 'really_delete', False):
                    message_buttons.append([InlineKeyboardButton(text="Yes, I am sure" + x_emo, callback_data="ReallyDelete"),
                                            InlineKeyboardButton(text="No, keep it" + back_emo, callback_data="NoDelete")])
                else:
                    message_buttons.append([InlineKeyboardButton(text=x_emo + "Delete current group" + x_emo, callback_data="Delete")])

            for item in KeePass.get_active_item().items:
                if KeePass.get_active_item().page * NUMBER_OF_ENTRIES_ON_PAGE >= i >= KeePass.get_active_item().page * NUMBER_OF_ENTRIES_ON_PAGE - NUMBER_OF_ENTRIES_ON_PAGE:
                    message_buttons.append([InlineKeyboardButton(text=str(item), callback_data=item.uuid)])
                i += 1

        return InlineKeyboardMarkup(message_buttons)

    def close(self):
        self.kdb.close()

    def open(self, username, password=None, keyfile_path=None):
        self.username = username
        user = self.get_user()

        try:
            with libkeepass.open(filename=self.path, password=password, keyfile=keyfile_path, unprotect=False) as kdb:
                self.kdb = kdb
                user.is_opened = True
                user.save()
                self._root_obj = kdb.obj_root
                # print(etree.tounicode(self._root_obj, pretty_print=True))

                self.opened = True
                self.__init_root_group()
                self.root_group.activate()

        except IOError:
            raise IOError("Master key or key-file wrong")

    def get_message(self):
        if not self.opened:
            raise IOError("Database not opened")

        message_text = ""

        if KeePass.get_active_item().type == "Entry":
            message_text += "_______" + key_emo + KeePass.get_active_item().name + "_______" + new_line
            i = 0
            for string in KeePass.get_active_item().strings:
                if KeePass.get_active_item().page * NUMBER_OF_ENTRIES_ON_PAGE >= i >= KeePass.get_active_item().page * NUMBER_OF_ENTRIES_ON_PAGE - NUMBER_OF_ENTRIES_ON_PAGE:
                    try:
                        message_text += str(string) + new_line
                    except TypeError:
                        continue
                i += 1
            if i > NUMBER_OF_ENTRIES_ON_PAGE:
                message_text += "_______Page {0} of {1}_______".format(KeePass.get_active_item().page, int(
                    math.ceil(KeePass.get_active_item().size / NUMBER_OF_ENTRIES_ON_PAGE))) + new_line
            else:
                message_text += "_______Page {0} of {1}_______".format(KeePass.get_active_item().page, 1) + new_line

        if KeePass.get_active_item().type == "Group":

            message_text += "_______" + str(KeePass.get_active_item()) + "_______" + new_line
            i = 0
            for item in KeePass.get_active_item().items:
                if KeePass.get_active_item().page * NUMBER_OF_ENTRIES_ON_PAGE >= i >= KeePass.get_active_item().page * NUMBER_OF_ENTRIES_ON_PAGE - NUMBER_OF_ENTRIES_ON_PAGE:
                    if item.type == "Entry":
                        message_text += key_emo + str(item) + new_line
                    if item.type == "Group":
                        message_text += folder_emo + str(item) + new_line
                i += 1
            if i > NUMBER_OF_ENTRIES_ON_PAGE:
                message_text += "_______Page {0} of {1}_______".format(KeePass.get_active_item().page, int(
                    math.ceil(KeePass.get_active_item().size / NUMBER_OF_ENTRIES_ON_PAGE))) + new_line
            else:
                message_text += "_______Page {0} of {1}_______".format(KeePass.get_active_item().page, 1) + new_line

        message_markup = self.__generate_keyboard()

        return message_text, message_markup

    def search_item(self, word):
        if not self.opened:
            raise IOError("Databse not opened")

        finded_items = []

        def __inner_find(parent_item):
            if word.lower() in parent_item.name.lower():
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

        return __inner_find(self.root_group)

    def search(self, word):
        finded_items = self.search_item(word)

        temp_group = KeeGroup(self, self, None, fake=True, items=finded_items)

        while KeePass.get_active_item() != self:
            KeePass.get_active_item().deactivate()

        temp_group.activate()

    def create_new(self, type):
        self.create_state = CreateState(type)
        return self.create_state.get_message()

    def end_creating(self):
        if self.create_state and self.get_user().create_state:

            group_item = KeePass.get_active_item()
            while not group_item.type == "Group":
                group_item = group_item.get_parent()

            if self.create_state.type == "Entry":
                entry_obj = KeeEntry.get_xml_element(icon_id=0,
                                                     strings=self.create_state.get_rawstrings())
                group_item.append(entry_obj)
            elif self.create_state.type == "Group":

                name = "None"
                for key, value in self.create_state.get_rawstrings():
                    if key == "Name":
                        name = value

                group_obj = KeeGroup.get_xml_element(name, icon_id=37)
                group_item.append(group_obj)

            group_item.activate()

            self.update_kdb_in_db()

        self.create_state = None

    def update_kdb_in_db(self):
        self.kdb.object_root = self._root_obj
        user = self.get_user()

        """Write to new file"""
        with open(TEMP_FOLDER + '/' + str(user.username) + '.kdbx', 'wb') as output:
            self.kdb.write_to(output)

        """Saving to database"""
        with open(TEMP_FOLDER + '/' + str(user.username) + '.kdbx', 'rb+') as file:
            user.file = file.read()
            user.save()

        """Removing downloaded file"""
        os.remove(TEMP_FOLDER + '/' + str(user.username) + '.kdbx')


class CreateState:
    def __init__(self,type):
        # Entry or Group
        if type != "Entry" and type != "Group":
            raise KeyError("Choises are (Entry, Group)")
        self.type = type
        if type == 'Entry':
            self.fields = {"Title": None,
                           "UserName": None,
                           "Password": None,
                           "URL": None,
                           "Notes": None}
            self.req_fields = ["Title", "UserName", "Password"]
            self.current_field = "Title"
        if type == 'Group':
            self.fields = {"Name": None,
                           "Notes": None}
            self.req_fields = ["Name", ]
            self.current_field = "Name"


    def get_rawstrings(self):
        rawstrings = []
        for key, value in self.fields.items():
            rawstrings.append((key, value))

        return rawstrings

    def get_message(self):
        message_text = self.__generate_text()
        message_markup = self.__generate_keyboard()

        return message_text, message_markup

    def set_cur_field_value(self, value):
        self.fields[self.current_field] = value

    def set_cur_field(self, field_name):
        self.current_field = field_name

    def next_field(self):
        finded = False
        for field in self.fields.keys():
            if finded:
                self.current_field = field
                break
            if self.current_field == field:
                finded = True

    def prev_field(self):
        prev_field = list(self.fields.keys())[0]
        for field in self.fields.keys():
            if self.current_field == field:
                self.current_field = prev_field
                break

            prev_field = field

    def generate_password(self):
        from random import sample as rsample

        s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        passlen = 8
        gen_password = "".join(rsample(s, passlen))

        prev_field = self.current_field
        self.set_cur_field("Password")
        self.set_cur_field_value(gen_password)
        self.set_cur_field(prev_field)

    def __generate_text(self):
        message_text = "_______Create New " + self.type + "_______" + new_line
        for field in self.fields.keys():
            if self.current_field == field:
                message_text += f"{arrow_right_emo}"
            else:
                message_text += "      "

            if field in self.req_fields:
                message_text += f"<b>{field}</b>: "
            else:
                message_text += f"{field}: "

            message_text += str(self.fields.get(field, "")) + new_line

        return message_text

    def __generate_keyboard(self):
        message_buttons = []

        message_buttons.append(
            [InlineKeyboardButton(text=arrow_left_emo, callback_data="create_Left"),
             InlineKeyboardButton(text=arrow_up_emo, callback_data="create_Back"),
             InlineKeyboardButton(text=lock_emo, callback_data="Lock"),
             InlineKeyboardButton(text=arrow_right_emo, callback_data="create_Right")])

        for field in self.fields.keys():
            if field == "Password":
                message_buttons.append([InlineKeyboardButton(text=field, callback_data=f"create_{field}"),
                                        InlineKeyboardButton(text="Generate",
                                                             callback_data="create_generate_password")])
            else:
                message_buttons.append([InlineKeyboardButton(text=field, callback_data=f"create_{field}")])

        message_buttons.append([InlineKeyboardButton(text="---Done---", callback_data="create_done")])

        return InlineKeyboardMarkup(message_buttons)


class KeeGroup(BaseKeePass):
    def __init__(self, root, parent, group_obj, fake=False, items=None, name="Search"):
        if parent is None:
            parent = self

        super().__init__(root, parent)
        if fake:
            self.type = "Group"
            self.name = name
            self.uuid = None
            self.notes = None
            self.icon_id = None
            self.items = items
            for item in self.items:
                item._parent = self
                item._root = root

            # init group object
            parser = objectify.makeparser()
            self._group_obj = objectify.fromstring(etree.tounicode(self.get_xml_element()), parser)

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
        if self.name:
            return self.name
        else:
            return " "

    def append(self,entry_obj):
        parser = objectify.makeparser()
        entry_obj = objectify.fromstring(etree.tounicode(entry_obj), parser)

        self.get_group_obj().append(entry_obj)
        self.refresh_items()

    def refresh_items(self):
        self.items = []
        self.__init_entries()
        self.__init_groups()

    def __init_entries(self):
        for entry in self._group_obj.findall('Entry'):
            self.items.append(KeeEntry(self._root, self, entry))
            self.size += 1

    def __init_groups(self):
        for group in self._group_obj.findall('Group'):
            self.items.append(KeeGroup(self._root, self, group))
            self.size += 1

    @classmethod
    def get_xml_element(cls, name, icon_id):
        uuid = (base64.b64encode(uuidGenerator.uuid4().bytes)).decode("utf-8")

        group = Element("Group")

        uuid_el = SubElement(group, 'UUID')
        uuid_el.text = uuid

        name_el = SubElement(group, 'Name')
        name_el.text = name

        notes = SubElement(group, 'Notes')
        notes.text = ""

        iconID = SubElement(group, 'IconID')
        iconID.text = str(icon_id)

        # ------Times
        times = SubElement(group, "Times")

        nowdate = datetime.datetime.now()

        cr_time = SubElement(times, "CreationTime")
        cr_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        lm_time = SubElement(times, "LastModificationTime")
        lm_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        la_time = SubElement(times, "LastAccessTime")
        la_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        et_time = SubElement(times, "ExpiryTime")
        et_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        expires = SubElement(times, "Expires")
        expires.text = "False"

        usage_count = SubElement(times, "UsageCount")
        usage_count.text = "0"

        lch_time = SubElement(times, "LocationChanged")
        lch_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Times-------------------

        is_expanded = SubElement(group, "IsExpanded")
        is_expanded.text = 'True'

        # Autotype -----------
        default_autotype_seq = SubElement(group, "DefaultAutoTypeSequence")
        default_autotype_seq.text = ''
        enable_at = SubElement(group, "EnableAutoType")
        enable_at.text = "null"

        # Searching -----------
        enable_searching = SubElement(group, "EnableSearching")
        enable_at.text = "null"

        last_top_vis_entry = SubElement(group, "LastTopVisibleEntry")
        last_top_vis_entry.text = "AAAAAAAAAAAAAAAAAAAAAA=="

        return group

    def get_group_obj(self):
        return self._group_obj


    def delete(self):
        self.deactivate()
        self._group_obj.getparent().remove(self._group_obj)
        KeePass.get_active_item().refresh_items()
        self._root.update_kdb_in_db()


class KeeEntry(BaseKeePass):

    def __init__(self, root, parent, entry_obj):
        super().__init__(root, parent)
        self.type = "Entry"
        self._entry_obj = entry_obj
        self.uuid = self._entry_obj.UUID.text
        self.icon_id = int(self._entry_obj.IconID.text)
        self.strings = []
        self.__init_strings()
        self.__set_name()
        self.__set_password()

    def __str__(self):
        return self.name

    def __init_strings(self):
        strings = self._entry_obj.findall('String')
        for string in strings:
            self.strings.append(EntryString(string.Key.text, string.Value.text))
            self.size += 1

    def __set_name(self):
        for string in self.strings:
            if string.key == "Title":
                self.name = string.value

    def __set_password(self):
        for string in self.strings:
            if string.key == "Password":
                self.password = string.value

    @classmethod
    def get_xml_element(cls, icon_id, strings):
        uuid = (base64.b64encode(uuidGenerator.uuid4().bytes)).decode("utf-8")

        entry = Element("Entry")

        uuid_el = SubElement(entry, 'UUID')
        uuid_el.text = uuid

        iconID = SubElement(entry, 'IconID')
        iconID.text = str(icon_id)

        SubElement(entry, "ForegroundColor")
        SubElement(entry, "BackgroundColor")
        SubElement(entry, "OverrideURL")
        SubElement(entry, "Tags")

        # ------Times
        times = SubElement(entry, "Times")

        nowdate = datetime.datetime.now()

        cr_time = SubElement(times, "CreationTime")
        cr_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        lm_time = SubElement(times, "LastModificationTime")
        lm_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        la_time = SubElement(times, "LastAccessTime")
        la_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        et_time = SubElement(times, "ExpiryTime")
        et_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")

        expires = SubElement(times, "Expires")
        expires.text = "False"

        usage_count = SubElement(times, "UsageCount")
        usage_count.text = "0"

        lch_time = SubElement(times, "LocationChanged")
        lch_time.text = nowdate.strftime("%Y-%m-%dT%H:%M:%SZ")
        # Times-------------------

        # Strings ----------
        for key, value in strings:
            entry.append(EntryString.get_xml_element(key, value))

        # Autotype -----------
        autotype = SubElement(entry, "AutoType")
        at_enabled = SubElement(autotype, "Enabled")
        at_enabled.text = "True"

        at_data_transfer_obfuscation = SubElement(autotype, "DataTransferObfuscation")
        at_data_transfer_obfuscation.text = "0"

        history = SubElement(entry, "History")

        return entry

    def delete(self):
        self.deactivate()
        self._entry_obj.getparent().remove(self._entry_obj)
        KeePass.get_active_item().refresh_items()
        self._root.update_kdb_in_db()


class EntryString():
    def __init__(self, key, value=None):
        self.key = key
        self.value = value

    @classmethod
    def get_xml_element(cls, key, value):
        string = Element('String')

        key_el = SubElement(string, 'Key')
        key_el.text = key

        value_el = SubElement(string, 'Value')
        value_el.text = value

        return string

    def __str__(self):
        return self.key + " = " + self.value
