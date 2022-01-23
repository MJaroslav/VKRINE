import json
import os
import re
import subprocess
import time
import urllib.request as request
import vk_api
from threading import Thread

import requests
from requests.exceptions import ReadTimeout
from vk_api.bot_longpoll import DotDict as GroupEvent
from vk_api.longpoll import Event as UserEvent

import vkrine

__cached_version__ = None


class LoopThread(Thread):
    def __init__(self, continue_condition=None, interval=None, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self._interval_ = interval
        self._continue_condition_ = continue_condition if continue_condition else True

    def run(self):
        try:
            while self._continue_condition_ is True or self._continue_condition_():
                if self._target:
                    self._target(*self._args, **self._kwargs)
                    if self._interval_:
                        time.sleep(self._interval_)
                else:
                    break
        finally:
            del self._target, self._args, self._kwargs


class NetworkLoopThread(LoopThread):
    def __init__(self, timeout_target=None, reconnect_success_target=None, reconnect_error_target=None, reconnect_timeout=30,
                 reconnect_attempts=60,
                 continue_condition=None, interval=None, group=None, target=None, name=None, args=(), kwargs=None,
                 *, daemon=None):
        super().__init__(continue_condition, interval, group, target, name, args, kwargs, daemon=daemon)
        self._reconnect_error_target_ = reconnect_error_target
        self._reconnect_success_target_ = reconnect_success_target
        self._reconnect_timeout_ = reconnect_timeout
        self._reconnect_attempts_ = reconnect_attempts
        self._timeout_target_ = timeout_target

    def run(self):
        try:
            while self._continue_condition_ is True or self._continue_condition_():
                try:
                    if self._target:
                        self._target(*self._args, **self._kwargs)
                        if self._interval_:
                            time.sleep(self._interval_)
                    else:
                        break
                except ReadTimeout:
                    if self._timeout_target_:
                        self._timeout_target_()
                    attempts = 0
                    vkrine.warning("Net", "Connection lost.")
                    while not check_connection(r'https://vk.com') and attempts < self._reconnect_attempts_:
                        attempts += 1
                        vkrine.warning("Net", "Try to reconnect number {}", attempts)
                        time.sleep(self._reconnect_timeout_)
                    if attempts == self._reconnect_attempts_:
                        vkrine.severe("Net", "Can't reconnect. Shutting down...")
                        if self._reconnect_error_target_:
                            self._reconnect_error_target_()
                        break
                    else:
                        vkrine.info("Net", "Connection restored")
                        if self._reconnect_success_target_:
                            self._reconnect_success_target_()
        finally:
            del self._target, self._args, self._kwargs, self._reconnect_error_target_


class SessionTimeoutWrapper(requests.Session):
    def __init__(self, timeout=None):
        super().__init__()
        self.timeout = timeout
        self.headers['User-agent'] = vk_api.vk_api.DEFAULT_USERAGENT

    @property
    def timeout(self):
        return self.__timeout__

    @timeout.setter
    def timeout(self, value):
        self.__timeout__ = value

    def request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None,
                json=None):
        return super().request(method, url, params, data, headers, cookies, files, auth,
                               self.timeout if self.timeout else timeout, allow_redirects,
                               proxies, hooks, stream, verify, cert, json)


class MessageBuilder(object):
    def __init__(self, message=""):
        vkrine.finest('MessageBuilder', 'Created instance with base message "{}"', message)
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
            vkrine.warning('MessageBuilder', 'Trying use not allowed type of attachments: {}', attachments)
            return self
        vkrine.finest('MessageBuilder', 'Appended attachment list: "{}"', attachments)
        return self

    def append_attachment(self, attachment):
        self.__attachments__.append(attachment)
        vkrine.finest('MessageBuilder', 'Appended attachment: "{}"', attachment)
        return self

    def newline(self, count=1):
        self.__message__ += "\n" * count
        vkrine.finest('MessageBuilder', "Added {} empty lines", count)
        return self

    def text(self, text, *args, **kwargs):
        self.__message__ += text.format(*args, **kwargs)
        vkrine.finest('MessageBuilder', 'Added simple formatted text: text "{}", args "{}", kwarg "{}"', text, args,
                      kwargs)
        return self

    def translated_text(self, key, *args, **kwargs):
        self.__translate__.append((key, args, kwargs))
        self.__message__ += "{}"
        vkrine.finest('MessageBuilder', 'Added translated formatted text: key "{}", args "{}", kwargs "{}"', key, args,
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
        vkrine.finest('MessageBuilder', 'Message send: peer_id "{}", message "{}", attachment "{}"', peer_id, message,
                      attachment)


def emoji_numbers(number):
    result = ""
    for char in str(number):
        result += vkrine.EMOJI_NUMBERS[int(char)]
    return result


def emoji_numbers_replace(string):
    for i in range(10):
        string = string.replace(str(i), vkrine.EMOJI_NUMBERS[i])
    return string


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
        vkrine.severe(None, "Please, enter bot token to %s file and restart the bot" % os.path.abspath(filepath))
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
    return 'is_admin' in member and (
            must_be_owner and 'is_owner' in member and member['is_owner'] or member['is_admin'])


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


def get_version():
    global __cached_version__
    if __cached_version__:
        return __cached_version__
    try:
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).decode().strip()
    except subprocess.CalledProcessError:
        tag = "UNKNOWN"
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
    except subprocess.CalledProcessError:
        commit = "CUSTOM"
    __cached_version__ = tag + "-" + commit
    return __cached_version__


def print_version():
    version = get_version()
    print("VKRINE Bot version " + version)
    if "CUSTOM" in version or "UNKNOWN" in version:
        print("\nFor knowing correct version required \"git\" command in PATH and bot should be located in its "
              "cloned repo")
