import json
import os
import urllib.request as request
import datetime
import re
import vkrine.consts as consts
import time
from vk_api.longpoll import Event as UserEvent
from vk_api.bot_longpoll import DotDict as GroupEvent
from .logger import *

class MessageBuilder(object):
    def __init__(self, bot, message=""):
        self._message_ = message
        self._attachments_ = []
        self._translate_ = []
        self._bot_ = bot
    
    def attachments(self, attachments):
        attachments_type = type(attachments)
        if attachments_type is list:
            self._attachments_ += attachments
        elif attachments_type is str:
            self._attachments_ += attachments.split(",")
        return self
    
    def attachment(self, attachment):
        self._attachments_.append(attachment)
        return self
    
    def newline(self, double=False):
        self._message_ += "\n\n" if double else "\n"
        return self

    def text(self, text, *args, **kwargs):
        self._message_ += text.format(*args, **kwargs)
        return self
    
    def translate(self, key, *args, **kwargs):
        self._translate_.append((key, args, kwargs))
        self._message_ += "{}"
        return self

    def send(self, destination):
        destination_type = type(destination)
        peer_id = 0
        if destination_type is UserEvent:
            peer_id = destination.peer_id
        elif destination_type is GroupEvent:
            peer_id = destination.peer_id
        elif destination_type is int:
            peer_id = destination
        else:
            raise TypeError("Destination must be only int (peer_id) or longpoll event")
        if self._translate_:
            self._translate_ = list(map(lambda element: self._bot_.l10n().translate(destination, element[0], *element[1], \
                **element[2]), self._translate_))
            message = self._message_.format(*self._translate_)
        else:
            message = self._message_
        attachment = self._attachments_[:10]
        if message and not attachment:
            self._bot_.vk().messages.send(peer_id=peer_id, message=message, \
                random_id=int(time.time()*1000))
        elif attachment and not message:
            self._bot_.vk().messages.send(peer_id=peer_id, attachment=attachment, \
                random_id=int(time.time()*1000))
        elif attachment and message:
            self._bot_.vk().messages.send(peer_id=peer_id, message=message, \
                attachment=attachment, random_id=int(time.time()*1000))
    
def emoji_numbers(number):
    result = ""
    for char in str(number):
        result += consts.EMOJI_NUMBERS[number]
    return result
    
def print_logo():
    print(r"===================================================")
    print(r"=            _____  _____ _   _ ______            =")
    print(r"=           |  __ \|_   _| \ | |  ____|           =")
    print(r"=           | |__) | | | |  \| | |__              =")
    print(r"=           |  _  /  | | | . ` |  __|             =")
    print(r"=           | | \ \ _| |_| |\  | |____            =")
    print(r"=           |_|  \_\_____|_| \_|______|           =")
    print(r"=                    Stickers                     =")
    print(r"=                                                 =")
    print(r"===================================================")


def init_runtime(runtime):
    if not os.path.exists(runtime) and not os.path.isdir(runtime):
        os.makedirs(runtime)


def load_json(filepath, default=None):
    if os.path.exists(filepath) and os.path.isfile(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    elif default is not None:
        with open(filepath, "w") as file:
            json.dump(default, file, indent=4)
        return default

def save_json(data, filepath):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

def load_token(filepath, is_user=False):
    if os.path.exists(filepath) and os.path.isfile(filepath):
        with open(filepath, "r") as file:
            return file.read().strip() if is_user else file.read().strip().split()
    else:
        with open(filepath, "w") as file:
            file.write("Введите токен сюда (если бот является группой, то на следующей строке введите номер группы ).")
        print('Пожалуйста, введите токен в файл "' +
              os.path.abspath(filepath) + '" и перезапустите бота.')
        quit()


def find_member(members, user_id):
    for member in members:
        if member['member_id'] == user_id:
            return member

def parse_message_event_to_string(bot, event):
    if event.user_id > 0:
        sender_type = "id"
        user = bot._vk_.users.get(user_ids=event.user_id)[0]
        name = user['first_name'] + " " + user['last_name']
        sender_id = user['id']
    else:
        sender_type = "club"
        group = bot._vk_.groups.getById(group_id=-event.user_id)[0]
        name = group["name"]
        sender_id = group['id']
    items = event.peer_id, bot._vk_.messages.getConversationsById(peer_ids=event.peer_id)['items']
    if items[0] > 2000000000:
        peer = "{} ({}) | ".format(items[0],
            items[1][0]['chat_settings']['title'])
    else:
        peer = ""
    return "{}@{}{} ({}): {}".format(peer, sender_type, sender_id, name, decode_text(event.text))


def bot_is_admin_in_chat(bot, chat_id):
    if chat_id > 2000000000:
        members = bot.vk().messages.getConversationMembers(
                peer_id=chat_id)["items"]
        return member_is_admin(find_member(members, bot.get_id()))
    
def in_level_list(src, check):
    data = ["*", check]
    split = check.split(".")
    i = len(split) - 1
    while i > 0:
        subsplit = split[:i]
        subsplit.append("*")
        data.append(".".join(subsplit))
        i -= 1
    for element in data:
        if element in src:
            return True


def member_is_admin(member, is_owner=False):
    return 'is_admin' in member and (is_owner and member['is_owner'] or member['is_admin'])


def check_connection(url):
    try:
        request.urlopen(url, timeout=5)
        return True
    except Exception:
        pass


def try_remove_prefix(text, bot, peer_id):
    mentioned = re.sub(r'^((\[(\S+?)\|\S+?\])|(@(\S+)( \(\S+?\))?))',
                       r'\3\5', text, re.IGNORECASE + re.DOTALL)
    prefix = bot.settings().get_option("chat.prefix", "/", peer_id)
    if len(mentioned) != len(text):
        domain = mentioned.split()[0].lower()
        if bot.get_architecture() == "user":
            architecture = "id"
        else:
            architecture = "club"
        if domain == "{}{}".format(architecture, bot.get_vk_id()) or domain == bot.get_vk_domain():
            return " ".join(mentioned.split()[1:])
        else:
            return text
    elif text.lower().startswith(prefix):
        return text[len(prefix):].strip()
    else:
        return text


def decode_text(text):
    return text.replace(r'&lt;', r'<').replace(r'&gt;', r'>').replace(r'&quot;', r'"').replace(r'&amp;', r'&')


def decode_quot(text):
    return text.replace(r'\"', r'"').replace(r"\'", r"'")
