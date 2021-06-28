import os
import json
import vkrine.utils as utils
from .modules import BotModule

MODULE_NAME = "permissions"

OWNER_PERMISSION_KEY = "@owner"
ADMIN_PERMISSION_KEY = "@admin"
MEMBER_PERMISSION_KEY = "@member"
PRIVATE_PERMISSION_KEY = "@private"

DEFAULT = {
    OWNER_PERMISSION_KEY: [
        "command.locale.chat"
    ],
    ADMIN_PERMISSION_KEY: [],
    MEMBER_PERMISSION_KEY: [
        "command.locale",
        "command.locale.personal",
        "command.echo",
        "command.help"
    ],
    PRIVATE_PERMISSION_KEY: [
        "command.locale",
        "command.locale.personal",
        "command.echo",
        "command.help"
    ]
}

class Permissions(BotModule):
    def __init__(self, bot):
        super().__init__(MODULE_NAME, bot)
        self._filepath_ = self._bot_.get_runtime() + "/permissions.json"
        self._permissions_ = {}

    def reload(self):
        self.load()

    def load(self):
        self._permissions_ = utils.load_json(self._filepath_, DEFAULT)

    def save(self):
        utils.save_json(self._permissions_, self._filepath_)

    def have_permission(self, event, permission):
        members = self._bot_.vk().messages.getConversationMembers(
            peer_id=event.peer_id)["items"]
        member = utils.find_member(members, event.user_id)
        chat_id = str(event.peer_id)
        user_id = str(event.user_id)
        if user_id in self._permissions_:
            if utils.in_level_list(self._permissions_[user_id], permission):
                return True
        if event.peer_id < 2000000000:
            if utils.in_level_list(self._permissions_[PRIVATE_PERMISSION_KEY], permission):
                return True
        else:
            if utils.member_is_admin(member, is_owner=True):
                if utils.in_level_list(self._permissions_[OWNER_PERMISSION_KEY], permission):
                    return True
            if utils.member_is_admin(member):
                if utils.in_level_list(self._permissions_[ADMIN_PERMISSION_KEY], permission):
                    return True
            if utils.in_level_list(self._permissions_[MEMBER_PERMISSION_KEY], permission):
                return True
            if chat_id in self._permissions_:
                if utils.in_level_list(self._permissions_[chat_id], permission):
                    return True
