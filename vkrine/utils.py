import json
import os
import re
import time
import urllib.request as request

from vk_api.bot_longpoll import DotDict as GroupEvent
from vk_api.longpoll import Event as UserEvent

import vkrine


class MessageBuilder(object):
    def __init__(self, message=""):
        vkrine.finer('[MessageBuilder] Created instance with base message "{}"', message)
        self.__message__ = message
        self.__attachments__ = []
        self.__translate__ = []
        self.__BOT__ = vkrine.bot

    def append_attachments(self, attachments):
        attachments_type = type(attachments)
        if attachments_type is list:
            self.__attachments__ += attachments
        elif attachments_type is str:
            self.__attachments__ += attachments.split(",")
        else:
            vkrine.warning("Trying use not allowed type of attachments in MessageBuilder: {}", attachments)
            return self
        vkrine.finer('[MessageBuilder] Appended attachment list: "{}"', attachments)
        return self

    def append_attachment(self, attachment):
        self.__attachments__.append(attachment)
        vkrine.finer('[MessageBuilder] Appended attachment: "{}"', attachment)
        return self

    def newline(self, count=1):
        self.__message__ += "\n" * count
        vkrine.finer("[MessageBuilder] Added {} empty lines", count)
        return self

    def text(self, text, *args, **kwargs):
        self.__message__ += text.format(*args, **kwargs)
        vkrine.finer('[MessageBuilder] Added simple formatted text: text "{}", args "{}", kwarg "{}"', text, args,
                     kwargs)
        return self

    def translated_text(self, key, *args, **kwargs):
        self.__translate__.append((key, args, kwargs))
        self.__message__ += "{}"
        vkrine.finer('[MessageBuilder] Added translated formatted text: key "{}", args "{}", kwargs "{}"', key, args,
                     kwargs)
        return self

    def send(self, destination):
        destination_type = type(destination)
        if destination_type is UserEvent or destination_type is GroupEvent:
            peer_id = destination.peer_id
        elif destination_type is int:
            peer_id = destination
        else:
            raise TypeError("Destination must be int (peer_id) or messages longpoll event")
        if self.__translate__:
            self.__translate__ = list(
                map(lambda element: self.__BOT__.L10N.translate(destination, element[0], *element[1], **element[2]),
                    self.__translate__))
            message = self.__message__.format(*self.__translate__)
        else:
            message = self.__message__
        attachment = self.__attachments__[:10]
        if message and not attachment:
            self.__BOT__.get_vk().messages.send(peer_id=peer_id, message=message, random_id=int(time.time() * 1000))
        elif attachment and not message:
            self.__BOT__.get_vk().messages.send(peer_id=peer_id, attachment=attachment,
                                                random_id=int(time.time() * 1000))
        elif attachment and message:
            self.__BOT__.get_vk().messages.send(peer_id=peer_id, message=message, attachment=attachment,
                                                random_id=int(time.time() * 1000))
        vkrine.finer('[MessageBuilder] Message send: peer_id "{}", message "{}", attachment "{}"', peer_id, message,
                     attachment)


def emoji_numbers(number):
    result = ""
    for char in str(number):
        result += vkrine.EMOJI_NUMBERS[int(char)]
    return result


def print_logo():
    print(r"                                                   ")
    print(r"             _____  _____ _   _ ______             ")
    print(r"            |  __ \|_   _| \ | |  ____|            ")
    print(r"            | |__) | | | |  \| | |__               ")
    print(r"            |  _  /  | | | . ` |  __|              ")
    print(r"            | | \ \ _| |_| |\  | |____             ")
    print(r"            |_|  \_\_____|_| \_|______|            ")
    print(r"                                                   ")


def create_dirs_if_not_exists(runtime):
    if not os.path.exists(runtime) and not os.path.isdir(runtime):
        os.makedirs(runtime)


def load_json_from_file(filepath, default=None):
    if os.path.exists(filepath) and os.path.isfile(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    elif default is not None:
        with open(filepath, "w") as file:
            json.dump(default, file, indent=4)
        return default


def dump_json_to_file(data, filepath):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)


def load_token(filepath, is_user=False):
    if os.path.exists(filepath) and os.path.isfile(filepath):
        with open(filepath, "r") as file:
            return file.read().strip() if is_user else file.read().strip().split()
    else:
        with open(filepath, "w") as file:
            file.write('Enter token there (if bot architecture is "group", enter group id on next lime)')
        vkrine.severe("Please, enter bot token to %s file and restart the bot" % os.path.abspath(filepath))
        quit()


def find_chat_member(members, user_id):
    for member in members:
        if member['member_id'] == user_id:
            return member


def parse_message_event_to_string(event):
    if event.user_id > 0:
        sender_type = "id"
        user = vkrine.bot.get_vk().users.get(user_ids=event.user_id)[0]
        name = user['first_name'] + " " + user['last_name']
        sender_id = user['id']
    else:
        sender_type = "club"
        group = vkrine.bot.get_vk().groups.getById(group_id=-event.user_id)[0]
        name = group["name"]
        sender_id = group['id']
    items = event.peer_id, vkrine.bot.get_vk().messages.getConversationsById(peer_ids=event.peer_id)['items']
    if items[0] > 2000000000:
        peer = "{} ({}) | ".format(items[0], items[1][0]['chat_settings']['title'])
    else:
        peer = ""
    return "{}@{}{} ({}): {}".format(peer, sender_type, sender_id, name, decode_text(event.text))


def bot_is_admin_in_chat(chat_id):
    if chat_id > 2000000000:
        # noinspection PyBroadException
        try:
            members = vkrine.bot.get_vk().messages.getConversationMembers(peer_id=chat_id)["items"]
            return chat_member_is_admin(find_chat_member(members, vkrine.bot.get_vk_id_with_type()))
        except Exception:
            pass


def element_in_dot_star_list(src, check):
    data = ["*", check]
    split = check.split(".")
    i = len(split) - 1
    while i > 0:
        sub_split = split[:i]
        sub_split.append("*")
        data.append(".".join(sub_split))
        i -= 1
    for element in data:
        if element in src:
            return True


def chat_member_is_admin(member, must_be_owner=False):
    return 'is_admin' in member and (must_be_owner and member['is_owner'] or member['is_admin'])


def check_connection(url):
    # noinspection PyBroadException
    try:
        request.urlopen(url, timeout=5)
        return True
    except Exception:
        pass


def try_remove_prefix(text, peer_id):
    bot = vkrine.bot
    mentioned = re.sub(r'^((\[(\S+)\|\S+])|(@(\S+)( \(\S+?\))?))',
                       r'\3\5', text, re.IGNORECASE + re.DOTALL)
    prefix = bot.SETTINGS.get_option("chat.prefix", "/", peer_id)
    if len(mentioned) != len(text):
        domain = mentioned.split()[0].lower()
        if bot.ARCHITECTURE == "user":
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
