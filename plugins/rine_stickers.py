from vkrine.eventlisteners import MessageListener
import vkrine.utils as utils
from vkrine.utils import MessageBuilder
import os
import json
import re
from vkrine.modules import BotModule
from vkrine.logger import *

class StickersListener(MessageListener):
    def __init__(self, module):
        super().__init__(module, priority=100)
        
    def _on_message_(self, event, bot):
        marker = bot.settings().get_option("modules.stickers.marker", default=":", chat_id=event.peer_id)
        temp = utils.try_remove_prefix(event.text, bot, event.peer_id)
        if temp == event.text:
            for word in re.findall(marker + r'([а-яёa-z0-9._();]+)' + marker, utils.decode_text(event.text), re.IGNORECASE):
                sticker = self._module_.get_sticker(event, word)
                if sticker:
                    if bot.permissions().have_permission(event, "stickers.{}".format(word)):
                        MessageBuilder(bot).attachment(sticker).send(event)
                        break

class StickersModule(BotModule):
    def __init__(self, bot):
        super().__init__("stickers", bot)
        self._stickers_ = {}
        if bot.get_architecture() == "user":
            self._upload_function_ = self._upload_graffiti_
        else:
            self._upload_function_ = self._upload_photo_
        self._datafile_ = self._bot_.get_runtime() + "/stickers.json"
        self._location_ = self._bot_.settings().get_option("modules.stickers.location", self._bot_.get_runtime() + "/stickers")
    
    def listeners(self):
        return [StickersListener(self)]
    
    def load(self):
        self._stickers_ = utils.load_json(self._datafile_, {})

    def reload(self):
        self.load()

    def unload(self):
        self._save_stickers_()

    def _save_stickers_(self):
        utils.save_json(self._stickers_, self._datafile_)

    def _upload_graffiti_(self, event, name):
        r = self._bot_.upload().document(self._location_ + "/" + name.replace(".", "/") + ".png", message_peer_id=event.peer_id, title="graffiti.png")['doc']
        result = "doc{}_{}".format(r["owner_id"], r["id"])
        self._stickers_[name] = result
        self._save_stickers_()
        return result

    def _upload_photo_(self, event, name):
        r = self._bot_.upload().photo_messages(self._location_ + "/" + name.replace(".", "/") + ".png", peer_id=event.peer_id)[0]
        result = "photo{}_{}".format(r["owner_id"], r["id"])
        self._stickers_[name] = result
        self._save_stickers_()
        return result

    def get_sticker(self, event, name):
        try:
            sticker = self._stickers_[name]
            info("Found sticker '" + sticker + "' for name '" + name + "'")
            return sticker
        except KeyError:
            try:
                sticker = self._upload_function_(event, name)
                info("Created sticker '" + sticker + "' for name '" + name + "'")
                return sticker
            except (FileNotFoundError, KeyError):
                pass

    
