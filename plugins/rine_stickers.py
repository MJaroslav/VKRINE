import re
import traceback

import vkrine
import vkrine.utils as utils
from vkrine.eventlisteners import MessageListener
from vkrine.modules import BotModule


class StickersListener(MessageListener):
    def __init__(self, module):
        super().__init__(module, priority=100)

    def _on_message_(self, event, bot):
        marker = bot.SETTINGS.get_option("modules.stickers.marker", default=":", chat_id=event.peer_id)
        temp = utils.try_remove_prefix(event.text, event.peer_id)
        if temp == event.text:
            for word in re.findall(marker + r'([а-яёa-z0-9._();]+)' + marker, utils.decode_text(event.text),
                                   re.IGNORECASE):
                sticker = self._MODULE_.get_sticker(event, word)
                if sticker:
                    if bot.PERMISSIONS.have_permission(event, "stickers.{}".format(word)):
                        vkrine.MessageBuilder().append_attachment(sticker).send(event)
                        break


class StickersModule(BotModule):
    def __init__(self, bot):
        super().__init__("stickers", bot)
        self.__stickers__ = {}
        if bot.ARCHITECTURE == "user":
            self.__upload_function__ = self.__upload_graffiti__
        else:
            self.__upload_function__ = self.__upload_photo__
        self.__DATAFILE__ = self._BOT_.RUNTIME + "/stickers.json"
        self.__location__ = None

    def listeners(self):
        return [StickersListener(self)]

    def load(self):
        self.__location__ = self._BOT_.SETTINGS.get_option("modules.stickers.location",
                                                           self._BOT_.RUNTIME + "/stickers")
        self.__stickers__ = utils.load_json_from_file(self.__DATAFILE__, {})

    def reload(self):
        self.load()

    def unload(self):
        self.__save_stickers__()

    def __save_stickers__(self):
        utils.dump_json_to_file(self.__stickers__, self.__DATAFILE__)

    def __upload_graffiti__(self, event, name):
        r = \
        self._BOT_.get_upload().document(self.__location__ + "/" + name.replace(".", "/") + ".png", doc_type='graffiti',
                                         message_peer_id=event.peer_id, title="graffiti.png")['graffiti']
        result = "doc{}_{}".format(r["owner_id"], r["id"])
        self.__stickers__[name] = result
        self.__save_stickers__()
        return result

    def __upload_photo__(self, event, name):
        r = self._BOT_.get_upload().photo_messages(self.__location__ + "/" + name.replace(".", "/") + ".png",
                                                   peer_id=event.peer_id)[0]
        result = "photo{}_{}".format(r["owner_id"], r["id"])
        self.__stickers__[name] = result
        self.__save_stickers__()
        return result

    def get_sticker(self, event, name):
        try:
            sticker = self.__stickers__[name]
            vkrine.fine("Found sticker '" + sticker + "' for name '" + name + "'")
            return sticker
        except KeyError:
            try:
                sticker = self.__upload_function__(event, name)
                vkrine.fine("Created sticker '" + sticker + "' for name '" + name + "'")
                return sticker
            except (FileNotFoundError, KeyError):
                traceback.print_exc()
