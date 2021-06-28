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
        self._filepath_ = self._bot_.get_runtime() + "/settings.json"
    
    def load(self):
        self._data_ = utils.load_json(self._filepath_, DEFAULT)

    def reload(self):
        self.load()

    def save(self):
        utils.save_json(self._data_, self._filepath_)
    
    def _get_data_(self, chat_id, create_entry=False):
        chat_id = str(chat_id)
        if chat_id in self._data_:
            return self._data_[chat_id]
        elif create_entry and chat_id != "0":
            self._data_[chat_id] = {}
            return self._data_[chat_id]
        else:
            return self._data_["@main"]

    def get_option(self, key, default=None, chat_id=0):
        main_value = default
        if chat_id != 0:
            main_value = self.get_option(key, default=default)
        keys = key.split(".")
        data = self._get_data_(chat_id)
        while len(keys) > 1:
            if keys[0] in data:
                data = data[keys[0]]
                del keys[0]
            else:
                return main_value
        return data[keys[0]] if keys[0] in data else default

    def set_option(self, key, value, chat_id=0):
        keys = key.split(".")
        data = self._get_data_(chat_id, True)
        while len(keys) > 1:
            if keys[0] not in data:
                data[keys[0]] = {}
            data = data[keys[0]]    
            del keys[0]
        data[keys[0]] = value
        self.save()