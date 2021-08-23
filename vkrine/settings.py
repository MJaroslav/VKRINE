import vkrine.utils as utils
from .modules import BotModule

MODULE_NAME = "settings"

DEFAULT = {
    "@main": {
        "chat": {
            "prefix": "/",
            "logging": [
                "commands"
            ]
        }
    }
}

class Settings(BotModule):
    def __init__(self, bot):
        super().__init__(MODULE_NAME, bot)
        self.FILEPATH = bot.RUNTIME + "/settings.json"
    
    def load(self):
        self.__data__ = utils.load_json(self.FILEPATH, DEFAULT)

    def reload(self):
        self.load()

    def save(self):
        utils.save_json(self.__data__, self.FILEPATH)
    
    def __get_data__(self, chat_id, create_entry=False):
        chat_id = str(chat_id)
        if chat_id in self.__data__:
            return self.__data__[chat_id]
        elif create_entry and chat_id != "0":
            self.__data__[chat_id] = {}
            return self.__data__[chat_id]
        else:
            return self.__data__["@main"]

    def get_option(self, key, default=None, chat_id=0):
        main_value = default
        if chat_id != 0:
            main_value = self.get_option(key, default=default)
        keys = key.split(".")
        data = self.__get_data__(chat_id)
        while len(keys) > 1:
            if keys[0] in data:
                data = data[keys[0]]
                del keys[0]
            else:
                return main_value
        return data[keys[0]] if keys[0] in data else default

    def set_option(self, key, value, chat_id=0):
        keys = key.split(".")
        data = self.__get_data__(chat_id, True)
        while len(keys) > 1:
            if keys[0] not in data:
                data[keys[0]] = {}
            data = data[keys[0]]    
            del keys[0]
        data[keys[0]] = value
        self.save()