import os
import time
from concurrent.futures import ThreadPoolExecutor
from operator import attrgetter

import requests
from requests.exceptions import ReadTimeout
from vk_api import Captcha, VkApi, VkUpload
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

import vkrine.consts as consts
import vkrine.utils as utils

from .localization import Localization
from .modules import ChatLoggerModule, CommandHandlerModule, PluginLoaderModule
from .permissions import Permissions
from .settings import Settings
from .utils import MessageBuilder


class BotBase(object):
    def __init__(self, bot_type, runtime='runtime'):
        self.TYPE = bot_type
        self.RUNTIME = runtime
        utils.init_runtime(self.RUNTIME)
        self.SETTINGS = Settings(self)
        self.L10N = Localization(self)
        self.PERMISSIONS = Permissions(self)
        self.COMMANDHANDLERMODULE = CommandHandlerModule(self)
        self.PLUGINLOADERMODULE = PluginLoaderModule(self)
        self.__commands__ = []
        self.__listeners__ = []
        self.__internal_modules__ = [
            self.SETTINGS,
            self.L10N,
            self.PERMISSIONS,
            self.COMMANDHANDLERMODULE,
            self.PLUGINLOADERMODULE,
            ChatLoggerModule(self)
        ]
        self.EXECUTOR = ThreadPoolExecutor(max_workers=2)

    def __load_commands__(self):
        for module in self.__internal_modules__:
            self.__commands__ += module.commands()

    def __load_listeners__(self):
        for module in self.__internal_modules__:
            self.__listeners__ += module.listeners()
    
    def load(self):
        for module in self.__internal_modules__:
            module.load()
        self.__load_commands__()
        self.__load_listeners__()
    
    def reload(self):
        for module in self.__internal_modules__:
            module.reload()
        self.__commands__.clear()
        self.__load_commands__()
        self.__listeners__.clear()
        self.__load_listeners__()
    
    def unload(self):
        for module in self.__internal_modules__:
            module.unload()

    def commands(self):
        return self.__commands__

    def login(self):
        pass

    def run(self):
        pass

    def stop(self):
        pass

    def send(self, peer_id, message=None, attachment=None):
        if message and not attachment:
            self.VK.messages.send(peer_id=peer_id, message=message, \
                random_id=int(time.time()*1000))
        elif attachment and not message:
            self.VK.messages.send(peer_id=peer_id, attachment=attachment, \
                random_id=int(time.time()*1000))
        elif attachment and message:
            self.VK.messages.send(peer_id=peer_id, message=message, \
                attachment=attachment, random_id=int(time.time()*1000))


class GroupBot(BotBase):
    def __init__(self, token, group_id, runtime='runtime'):
        super().__init__(consts.BOT_TYPE_GROUP, runtime=runtime)
        self.__token__ = token
        self.ID = group_id
        self.__should_stop__ = False
        self.current_captcha = None
    
    def login(self):
        self.SESSION = VkApi(token=self.__token__)
        self.UPLOAD = VkUpload(self.SESSION)
        self.VK = self.SESSION.get_api()
        self.GROUP = self.VK.groups.getById(group_id=self.ID)[0]
        self.ID = self.GROUP["id"]
        self.DOMAIN = self.GROUP["screen_name"]
        print("Выполнен вход под группой @club{} ({})".format(self.GROUP['id'], \
            self.GROUP['name']))

    def run(self):
        while not self.__should_stop__:
            try:
                poll = VkBotLongPoll(self.SESSION, self.ID)
                try:
                    for event in poll.listen():
                        if self.__should_stop__:
                            break
                        print(event)
                        event.object.type = event.type
                        event = event.object
                        if event.type == VkBotEventType.MESSAGE_NEW:
                            
                            event.user_id = event.from_id
                        for listener in self.__listeners__:
                            if self.SETTINGS.get_option("multithreading", False):
                                self.EXECUTOR.submit(listener.on_event, event, self)
                            else:
                                listener.on_event(event, self)
                except Captcha as captcha1:
                    filecaptcha = self.__runtime__ + "/captcha.jpg"
                    with open(filecaptcha, "wb") as handle:
                        response = requests.get(captcha1.url, stream=True)
                        for block in response.iter_content(1024):
                            if not block:
                                break
                        handle.write(block)
                        try:
                            photo = self.UPLOAD.photo_messages(filecaptcha)[0]
                            attachment = "photo{}_{}".format(attachment["owner_id"], attachment["id"])
                            MessageBuilder().translate("text.captcha", captcha1.url).attachment(attachment).send(self, event=event)
                            self.__current_captcha__ = captcha1
                        except Captcha as captcha2:
                            print("Требуется капча, смотрите '{}/captcha.jpg'".format(self.__runtime__))
                            answer = input("Решение: ")
                            captcha2.try_again(answer)
                            print("Решено")
            except ReadTimeout:
                reconnect_count = 0
                while not utils.check_connection(r'https://vk.com') and reconnect_count < 60:
                    reconnect_count += 1
                    print("Потеряно соединение, попытка восстановить номер {}".format(
                        reconnect_count))
                    time.sleep(30)
                if reconnect_count == 60:
                    print("Невозможно восстановить соединение")
                    self.stop()
                else:
                    print("Соединение восстановлено")
        self.EXECUTOR.shutdown(wait=True)
        self.unload()

    def stop(self):
        self.__should_stop__ = True

class UserBot(BotBase):
    def __init__(self, token, runtime='runtime'):
        super().__init__(consts.BOT_TYPE_USER, runtime=runtime)
        self.__token__ = token
        self.__should_stop__ = False
        self.current_captcha = None
    
    def login(self):
        self.SESSION = VkApi(token=self.__token__)
        self.UPLOAD = VkUpload(self.SESSION)
        self.VK = self.SESSION.get_api()
        self.USER = self.VK.users.get(fields="domain")[0]
        self.ID = self.USER["id"]
        self.DOMAIN = self.USER["domain"]
        print("Выполнен вход под пользователем @id{} ({} {})".format(self.USER['id'], \
            self.USER['first_name'], self.USER['last_name']))

    def run(self):
        while not self.__should_stop__:
            try:
                poll = VkLongPoll(self.SESSION)
                try:
                    for event in poll.listen():
                        if self.__should_stop__:
                            break
                        for listener in self.__listeners__:
                            if self.SETTINGS.get_option("multithreading", False):
                                self.EXECUTOR.submit(listener.on_event, event, self)
                            else:
                                listener.on_event(event, self)
                except Captcha as captcha1:
                    filecaptcha = self.__runtime__ + "/captcha.jpg"
                    with open(filecaptcha, "wb") as handle:
                        response = requests.get(captcha1.url, stream=True)
                        for block in response.iter_content(1024):
                            if not block:
                                break
                        handle.write(block)
                        try:
                            photo = self.UPLOAD.photo_messages(filecaptcha)[0]
                            attachment = "photo{}_{}".format(attachment["owner_id"], attachment["id"])
                            MessageBuilder().translate("text.captcha", captcha1.url).attachment(attachment).send(self, event=event)
                            self.__current_captcha__ = captcha1
                        except Captcha as captcha2:
                            print("Требуется капча, смотрите '{}/captcha.jpg'".format(self.__runtime__))
                            answer = input("Решение: ")
                            captcha2.try_again(answer)
                            print("Решено")
            except ReadTimeout:
                reconnect_count = 0
                while not utils.check_connection(r'https://vk.com') and reconnect_count < 60:
                    reconnect_count += 1
                    print("Потеряно соединение, попытка восстановить номер {}".format(
                        reconnect_count))
                    time.sleep(30)
                if reconnect_count == 60:
                    print("Невозможно восстановить соединение")
                    self.stop()
                else:
                    print("Соединение восстановлено")
        self.EXECUTOR.shutdown(wait=True)
        self.unload()

    def stop(self):
        self.__should_stop__ = True

