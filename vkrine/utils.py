import json
import os
import urllib.request as request
import datetime
import re


class MessageBuilder(object):
    def __init__(self, message=""):
        self.__message__ = message
        self.__attachments__ = []
        self.__translate__ = []
    
    def attachments(self, attachments):
        attachments_type = type(attachments)
        if attachments_type is list:
            self.__attachments__ += attachments
        elif attachments_type is str:
            self.__attachments__ += attachments.split(",")
        return self
    
    def attachment(self, attachment):
        self.__attachments__.append(attachment)
        return self
    
    def newline(self, double=False):
        self.__message += "\n\n" if double else "\n"
        return self

    def text(self, text, *args, **kwargs):
        self.__message__ += text.format(*args, **kwargs)
        return self
    
    def translate(self, key, *args, **kwargs):
        self.__translate__.append((key, args, kwargs))
        self.__message__ += "{}"
        return self

    def send(self, bot, peer_id=None, event=None):
        if self.__translate__:
            target = event if event else peer_id
            self.__translate__ = list(map(lambda element: bot.L10N.translate(target, element[0], *element[1], \
                **element[2]), self.__translate__))
            message = self.__message__.format(*self.__translate__)
        else:
            message = self.__message__
        attachment = self.__attachments__[:10]
        peer_id = peer_id if peer_id else event.peer_id
        bot.send(peer_id, message, attachment)

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
    elif default:
        with open(filepath, "w") as file:
            json.dump(default, file, indent=4)
        return default

def save_json(data, filepath):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

def load_token(filepath):
    if os.path.exists(filepath) and os.path.isfile(filepath):
        with open(filepath, "r") as file:
            return file.readline()
    else:
        with open(filepath, "w") as file:
            file.write("Введите токен сюда.")
        print('Пожалуйста, введите токен в файл "' +
              os.path.abspath(filepath) + '" и перезапустите бота.')
        quit()


def find_member(members, user_id):
    for member in members:
        if member['member_id'] == user_id:
            return member

def log_message_event(bot, event):
    user = bot.VK.users.get(user_ids=event.user_id)[0]
    item = event.peer_id, bot.VK.messages.getConversationsById(peer_ids=event.peer_id)['items']
    if item[0] > 2000000000:
        peer = "{} ({}) | ".format(item[0], item[1][0]['chat_settings']['title'])
    else:
        peer = ""
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    print("{}: {}@id{} ({} {}): {}".format(now, peer, user['id'], user['first_name'], user['last_name'], decode_text(event.text)))


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
    prefix = bot.SETTINGS.get_option(peer_id, "chat.prefix", "/")
    if len(mentioned) != len(text):
        domain = mentioned.split()[0].lower()
        if domain == "id{}".format(bot.get_id()) or domain == bot.get_domain():
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
