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

from .logger import *
from vkrine import exceptions

class BotBase(object):
    def __init__(self, architecture, runtime='runtime'):
        self._architecture_ = architecture
        self._runtime_ = runtime
        utils.init_runtime(self._runtime_)
        self._settings_ = Settings(self)
        self._l10n_ = Localization(self)
        self._permissions_ = Permissions(self)
        self._command_module_ = CommandHandlerModule(self)
        self._plugin_module_ = PluginLoaderModule(self)
        self._commands_ = []
        self._listeners_ = []
        self._modules_ = [
            self._settings_,
            self._l10n_,
            self._permissions_,
            self._command_module_,
            self._plugin_module_,
            ChatLoggerModule(self)
        ]
        self._executor_ = ThreadPoolExecutor(max_workers=2)

    def settings(self):
        return self._settings_
    
    def l10n(self):
        return self._l10n_
    
    def permissions(self):
        return self._permissions_

    def _load_commands_(self):
        for module in self._modules_:
            self._commands_ += module.commands()

    def _load_listeners_(self):
        for module in self._modules_:
            self._listeners_ += module.listeners()
    
    def get_runtime(self):
        return self._runtime_

    def load(self):
        for module in self._modules_:
            module.load()
        self._load_commands_()
        self._load_listeners_()
    
    def reload(self):
        for module in self._modules_:
            module.reload()
        self._commands_.clear()
        self._load_commands_()
        self._listeners_.clear()
        self._load_listeners_()
    
    def unload(self):
        for module in self._modules_:
            module.unload()

    def get_architecture(self):
        return self._architecture_

    def commands(self):
        return self._commands_

    def login(self):
        pass

    def run(self):
        pass

    def stop(self):
        pass

    def vk(self):
        return self._vk_
    
    def upload(self):
        return self._upload_session_

    def get_vk_id(self):
        return self._id_

    def get_vk_name(self):
        return self._name_

    def get_vk_domain(self):
        return self._domain_

    def get_command(self, event, phrase):
        for command in self.commands():
            if command.NAME == phrase:
                return command
            if command.get_aliases_key():
                if phrase in self.l10n().translate_list(event, command.get_aliases_key()):
                    return command
                if phrase in self.l10n().translate_list(None, command.get_aliases_key()):
                    return command
        raise exceptions.CommandNotFoundException(None)

class GroupBot(BotBase):
    def __init__(self, token, group_id, runtime='runtime'):
        super().__init__(consts.ARCHITECTURE_GROUP, runtime=runtime)
        self.__token__ = token
        self._id_ = group_id
        self._should_stop_ = False

    def login(self):
        self._session_ = VkApi(token=self.__token__)
        self._upload_session_ = VkUpload(self._session_)
        self._vk_ = self._session_.get_api()
        login_info = self.vk().groups.getById(group_id=self._id_)[0]
        self._domain_ = login_info["screen_name"]
        self._name_ = login_info["name"]
        info("Logged as @club{} ({})", self.get_vk_id(), self.get_vk_name())

    def run(self):
        while not self._should_stop_:
            try:
                poll = VkBotLongPoll(self._session_, self.get_vk_id())
                for event in poll.listen():
                    if self._should_stop_:
                        break
                    event.object.type = event.type
                    event = event.object
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        event.user_id = event.from_id
                    for listener in self._listeners_:
                        if self.settings().get_option("multithreading", False):
                            self._executor_.submit(listener.on_event, event, self)
                        else:
                            listener.on_event(event, self)
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
        self._executor_.shutdown(wait=True)
        self.unload()

    def stop(self):
        self._should_stop_ = True

class UserBot(BotBase):
    def __init__(self, token, runtime='runtime'):
        super().__init__(consts.ARCHITECTURE_USER, runtime=runtime)
        self._token_ = token
        self._should_stop_ = False
        self.current_captcha = None
    
    def login(self):
        self._session_ = VkApi(token=self._token_)
        self._upload_ = VkUpload(self._session_)
        self._vk_ = self._session_.get_api()
        login_info = self.vk().users.get(fields="domain")[0]
        self._id_ = login_info["id"]
        self._domain_ = login_info["domain"]
        self._name_ = login_info["first_name"] + " " + login_info["last_name"]
        info("Logged as @id{} ({})", self.get_vk_id(), self.get_vk_name())

    def run(self):
        while not self._should_stop_:
            try:
                poll = VkLongPoll(self._session_)
                try:
                    for event in poll.listen():
                        if self._should_stop_:
                            break
                        for listener in self._listeners_:
                            if self.settings().get_option("multithreading", False):
                                self._executor_.submit(listener.on_event, event, self)
                            else:
                                listener.on_event(event, self)
                except Captcha as captcha1:
                    filecaptcha = self._runtime_ + "/captcha.jpg"
                    with open(filecaptcha, "wb") as handle:
                        response = requests.get(captcha1.url, stream=True)
                        for block in response.iter_content(1024):
                            if not block:
                                break
                        handle.write(block)
                        try:
                            photo = self._upload_.photo_messages(filecaptcha)[0]
                            attachment = "photo{}_{}".format(attachment["owner_id"], attachment["id"])
                            MessageBuilder(self).translate("text.captcha", captcha1.url).attachment(attachment).send(event)
                            self._current_captcha_ = captcha1
                        except Captcha as captcha2:
                            print("Требуется капча, смотрите '{}/captcha.jpg'".format(self._runtime_))
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
        self._executor_.shutdown(wait=True)
        self.unload()

    def stop(self):
        self._should_stop_ = True

