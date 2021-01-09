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
        self.FILEPATH = self.BOT.RUNTIME + "/permissions.json"
        self.__permissions__ = {}

    def reload(self):
        self.load()

    def load(self):
        self.__permissions__ = utils.load_json(self.FILEPATH, DEFAULT)

    def save(self):
        utils.save_json(self.__permissions__, self.FILEPATH)

    def have_permission(self, event, permission):
        members = self.BOT.VK.messages.getConversationMembers(
            peer_id=event.peer_id)["items"]
        member = utils.find_member(members, event.user_id)
        if event.peer_id < 2000000000:
            if utils.in_level_list(self.__permissions__[PRIVATE_PERMISSION_KEY], permission):
                return True
        else:
            if utils.member_is_admin(member, is_owner=True):
                if utils.in_level_list(self.__permissions__[OWNER_PERMISSION_KEY], permission):
                    return True
            if utils.member_is_admin(member):
                if utils.in_level_list(self.__permissions__[ADMIN_PERMISSION_KEY], permission):
                    return True
            if utils.in_level_list(self.__permissions__[MEMBER_PERMISSION_KEY], permission):
                return True
        chat_id = str(event.peer_id)
        user_id = str(event.user_id)
        if chat_id in self.__permissions__:
            if user_id in self.__permissions__:
                if utils.in_level_list(self.__permissions__[chat_id][user_id], permission):
                    return True
        if user_id in self.__permissions__:
            if utils.in_level_list(self.__permissions__[user_id], permission):
                return True
