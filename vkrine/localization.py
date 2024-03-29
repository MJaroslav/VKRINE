import os
import random

from vk_api.bot_longpoll import DotDict as GroupEvent
from vk_api.longpoll import Event as UserEvent

import vkrine.utils as utils
from .modules import BotModule

MODULE_NAME = "localization"

MAIN_LOCALE_KEY = "@main"

DEFAULT = {
    MAIN_LOCALE_KEY: "en_US"
}


class Localization(BotModule):
    def __init__(self, bot):
        super().__init__(MODULE_NAME, bot)
        self.__FILEPATH__ = self._BOT_.RUNTIME + "/localization.json"
        self.__locales__ = {}
        self.__settings__ = {}

    def reload(self):
        self.load()

    def load(self):
        self.__settings__ = utils.load_json_from_file(self.__FILEPATH__, DEFAULT)
        dir_path = "locales"
        for filename in os.listdir(dir_path):
            filepath = "{}/{}".format(dir_path, filename)
            filename_split = os.path.splitext(filename)
            if os.path.isfile(filepath) and filename_split[1] == ".json":
                data = utils.load_json_from_file(filepath)
                if data:
                    self.__locales__[filename_split[0]] = data

    def save(self):
        utils.dump_json_to_file(self.__settings__, self.__FILEPATH__)

    def main_locale(self):
        return self.__locales__[self.__settings__[MAIN_LOCALE_KEY]]

    def get_locale_key(self, target):
        target_type = type(target)
        if target_type is UserEvent:
            user_id = str(target.user_id)
            peer_id = str(target.peer_id)
        elif target_type is GroupEvent:
            user_id = str(target.user_id)
            peer_id = str(target.peer_id)
        elif target_type is tuple or target_type is list:
            user_id = target[0]
            peer_id = target[1]
        elif target_type is int:
            if target > 2000000000:
                peer_id = target
                user_id = 0
            else:
                peer_id = 0
                user_id = target
        else:
            user_id = None
            peer_id = None
        if user_id or peer_id:
            user_id = str(user_id)
            peer_id = str(peer_id)
            if user_id in self.__settings__:
                return self.__settings__[user_id]
            if peer_id in self.__settings__:
                return self.__settings__[peer_id]
        elif target_type is str:
            if target in self.__settings__:
                return self.__settings__[target]
        return self.__settings__[MAIN_LOCALE_KEY]

    def translate(self, target, key, *args, **kwargs):
        locale_key = self.get_locale_key(target)
        locale = self.__locales__[locale_key]
        main_locale = self.main_locale()
        if key in locale["keys"]:
            return locale["keys"][key].format(*args, **kwargs)
        elif key in main_locale["keys"]:
            return main_locale["keys"][key].format(*args, **kwargs)
        else:
            return key

    def translate_random(self, target, key, *args, **kwargs):
        return random.choice(self.translate_list(target, key, *args, **kwargs))

    def translate_list(self, target, key, *args, **kwargs):
        result = [key]
        locale_key = self.get_locale_key(target)
        locale = self.__locales__[locale_key]
        main_locale = self.main_locale()
        if key in locale["keys"]:
            result += locale["keys"][key]
        elif key in main_locale["keys"]:
            result += main_locale["keys"][key]
        del result[0]
        result = list(map(lambda element: element.format(*args, **kwargs), result))
        return result if result else [key]

    def reset_locale(self, target):
        if target != "@main":
            del self.__settings__[target]
        self.save()

    def set_locale(self, target, locale):
        if locale in self.__settings__:
            self.__settings__[target][0] = locale
        else:
            self.__settings__[target] = locale
        self.save()

    def has_locale(self, locale):
        return locale in self.__locales__

    def locales(self):
        return self.__locales__.keys()
