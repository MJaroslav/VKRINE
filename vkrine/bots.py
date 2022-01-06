from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import ReadTimeout

import requests
import datetime
from vk_api import Captcha, VkApi, VkUpload
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.longpoll import VkLongPoll

import time
import vkrine
import vkrine.utils as utils
from vkrine import exceptions
from .localization import Localization
from .modules import LoggerModule, CommandHandlerModule, PluginLoaderModule
from .permissions import Permissions
from .settings import Settings


class BotBase(object):
    def __init__(self, architecture, runtime='runtime'):
        self.ARCHITECTURE = architecture
        self.RUNTIME = runtime
        self.SETTINGS = Settings(self)
        self.L10N = Localization(self)
        self.PERMISSIONS = Permissions(self)
        self._COMMAND_MODULE_ = CommandHandlerModule(self)
        self._PLUGIN_MODULE_ = PluginLoaderModule(self)
        self._commands_ = []
        self._listeners_ = []
        self._modules_ = [
            self.SETTINGS,
            self.L10N,
            self.PERMISSIONS,
            self._COMMAND_MODULE_,
            self._PLUGIN_MODULE_,
            LoggerModule(self)
        ]
        self._register_additional_modules_()
        self._EXECUTOR_ = ThreadPoolExecutor(max_workers=2)
        self._event_thread_ = None
        self._is_alive_ = False
        self._status_thread_ = None

        # Должны быть инициализированы в реализации login метода:
        self._vk_ = None
        self._id_ = None
        self._name_ = None
        self._domain_ = None
        self._upload_session_ = None

    def _status_update_task_(self):
        raise NotImplementedError()

    def _register_additional_modules_(self):
        pass

    def __load_commands__(self):
        for module in self._modules_:
            self._commands_ += module.commands()

    def __load_listeners__(self):
        for module in self._modules_:
            self._listeners_ += module.listeners()

    def load_modules(self):
        for module in self._modules_:
            module.load()
        self.__load_commands__()
        self.__load_listeners__()

    def reload_modules(self):
        for module in self._modules_:
            module.reload()
        self._commands_.clear()
        self.__load_commands__()
        self._listeners_.clear()
        self.__load_listeners__()

    def unload_modules(self):
        for module in self._modules_:
            module.unload()

    def get_commands(self):
        return self._commands_

    def login(self):
        raise NotImplementedError()

    def run(self):
        raise NotImplementedError()

    def _run_(self):
        try:
            self.run()
        except ReadTimeout:
            tries_count = 0
            vkrine.warning("Net", "Connection lost.")
            while not utils.check_connection(r'https://vk.com') and tries_count < 60:
                tries_count += 1
                vkrine.warning("Net", "Try to reconnect number {}", tries_count)
                time.sleep(30)
            if tries_count == 60:
                vkrine.severe("Net", "Can't reconnect. Shutting down...")
                self.stop()
            else:
                vkrine.info("Net", "Connection restored")

    def start(self):
        self._event_thread_ = utils.LoopThread(target=self._run_, name="EventThread", daemon=True)
        self._event_thread_.start()
        self._status_thread_ = utils.LoopThread(interval=60,
                                                target=self._status_update_task_, name="StatusThread", daemon=True)
        self._status_thread_.start()
        self._is_alive_ = True

    def stop(self):
        self._EXECUTOR_.shutdown(wait=True)
        self.unload_modules()
        self._is_alive_ = False

    def join(self):
        while self.is_alive():
            pass

    def is_alive(self):
        return self._is_alive_ and self._event_thread_.is_alive() and self._status_thread_.is_alive()

    def get_vk(self):
        return self._vk_

    def get_upload(self):
        return self._upload_session_

    def get_vk_id(self):
        return self._id_

    def get_vk_id_with_type(self):
        return int(self.get_vk_id())

    def get_vk_name(self):
        return self._name_

    def get_vk_domain(self):
        return self._domain_

    def get_command(self, event, phrase):
        for command in self.get_commands():
            if command.NAME == phrase:
                return command
            if command.get_aliases_key():
                if phrase in self.L10N.translate_list(event, command.get_aliases_key()):
                    return command
                if phrase in self.L10N.translate_list(None, command.get_aliases_key()):
                    return command
        raise exceptions.CommandNotFoundException(None)


class GroupBot(BotBase):
    def __init__(self, token, group_id, runtime='runtime'):
        super().__init__(vkrine.ARCHITECTURE_GROUP, runtime=runtime)
        self.__TOKEN__ = token
        self._id_ = group_id

        self.__should_stop__ = False
        self.__session__ = None

    def login(self):
        self.__session__ = VkApi(token=self.__TOKEN__)
        self._upload_session_ = VkUpload(self.__session__)
        self._vk_ = vkrine.VkApiLoggedMethod(self.__session__)
        login_info = self.get_vk().groups.getById(group_id=self._id_)[0]
        self._domain_ = login_info["screen_name"]
        self._name_ = login_info["name"]
        vkrine.info("Net", "Logged as @club{} ({})", self.get_vk_id(), self.get_vk_name())

    def run(self):
        poll = VkBotLongPoll(self.__session__, self.get_vk_id())
        for event in poll.listen():
            if not event:
                continue
            if self.__should_stop__:
                break
            event.object.type = event.type
            event = event.object
            if event.type == VkBotEventType.MESSAGE_NEW:
                event.user_id = event.from_id
            for listener in self._listeners_:
                if self.SETTINGS.get_option("multithreading", False):
                    self._EXECUTOR_.submit(listener.on_event, event, self)
                else:
                    listener.on_event(event, self)

    def _status_update_task_(self):
        pass

    def get_vk_id_with_type(self):
        return -super().get_vk_id_with_type()


class UserBot(BotBase):
    def __init__(self, token, runtime='runtime'):
        super().__init__(vkrine.ARCHITECTURE_USER, runtime=runtime)
        self.__TOKEN__ = token

        self.current_captcha = None
        self.__session__ = None

    def login(self):
        self.__session__ = VkApi(token=self.__TOKEN__)
        self._upload_session_ = VkUpload(self.__session__)
        self._vk_ = vkrine.VkApiLoggedMethod(self.__session__)
        login_info = self.get_vk().users.get(fields="domain")[0]
        self._id_ = login_info["id"]
        self._domain_ = login_info["domain"]
        self._name_ = login_info["first_name"] + " " + login_info["last_name"]
        vkrine.info("Net", "Logged as @id{} ({})", self.get_vk_id(), self.get_vk_name())

    def _status_update_task_(self):
        self._vk_.status.set(text="VKRINE " + utils.get_version() + " last online: " + utils.emoji_numbers_replace(
            datetime.datetime.now().strftime("%d-%m-%Y %H:%M")))

    def run(self):
        for event in VkLongPoll(self.__session__).check():
            if not event:
                continue
            try:
                for listener in self._listeners_:
                    if self.SETTINGS.get_option("multithreading", False):
                        self._EXECUTOR_.submit(listener.on_event, event, self)
                    else:
                        listener.on_event(event, self)
            except Captcha as captcha1:
                file_captcha = self.RUNTIME + "/captcha.jpg"
                with open(file_captcha, "wb") as handle:
                    response = requests.get(captcha1.url, stream=True)
                    for block in response.iter_content(1024):
                        if not block:
                            break
                    handle.write(block)
                    try:
                        photo = self.get_upload().photo_messages(file_captcha)[0]
                        attachment = "photo{}_{}".format(photo["owner_id"], photo["id"])
                        vkrine.MessageBuilder().translated_text("text.captcha", captcha1.url).attachment(
                            attachment).send(event)
                        self.current_captcha = captcha1
                    except Captcha as captcha2:
                        vkrine.severe("Captcha", "Required captcha, see {}/captcha.jpg", self.RUNTIME)
                        answer = input("Answer: ")
                        captcha2.try_again(answer)
                        vkrine.info("Captcha", "Captcha solved")
