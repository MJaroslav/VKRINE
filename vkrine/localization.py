import os
import json
import vkrine.utils as utils
from vk_api.longpoll import Event as UserEvent
from vk_api.bot_longpoll import DotDict as GroupEvent
import random
from .modules import BotModule

MODULE_NAME = "localization"

MAIN_LOCALE_KEY = "@main"

DEFAULT = {
    MAIN_LOCALE_KEY: "en_US"
}

class Localization(BotModule):
    def __init__(self, bot):
        super().__init__(MODULE_NAME, bot)
        self._filepath_ = self._bot_.get_runtime() + "/localization.json"
        self._locales_ = {}
        self._settings_ = {}

    def reload(self):
        self.load()

    def load(self):
        self._settings_ = utils.load_json(self._filepath_, DEFAULT)
        dirpath = "locales"
        for filename in os.listdir(dirpath):
            filepath = "{}/{}".format(dirpath, filename)
            filenamesplit = os.path.splitext(filename)
            if os.path.isfile(filepath) and filenamesplit[1] == ".json":
                data = utils.load_json(filepath)
                if data: self._locales_[filenamesplit[0]] = data

    def save(self):
        utils.save_json(self._settings_, self._filepath_)

    def main_locale(self):
        return self._locales_[self._settings_[MAIN_LOCALE_KEY]]

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
            if user_id in self._settings_:
                return self._settings_[user_id]
            if peer_id in self._settings_:
                return self._settings_[peer_id]
        elif target_type is str:
            if target in self._settings_:
                return self._settings_[target]
        return self._settings_[MAIN_LOCALE_KEY]

    def translate(self, target, key, *args, **kwargs):
        locale_key = self.get_locale_key(target)
        locale = self._locales_[locale_key]
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
        locale = self._locales_[locale_key]
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
            del self._settings_[target]
        self.save()

    def set_locale(self, target, locale):
        if locale in self._settings_:
            self._settings_[target][0] = locale
        else:
            self._settings_[target] = locale
        self.save()

    def has_locale(self, locale):
        return locale in self._locales_

    def locales(self):
        return self._locales_.keys()
