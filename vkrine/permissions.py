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
        self.__FILEPATH__ = self._BOT_.RUNTIME + "/permissions.json"
        self.__permissions__ = {}

    def reload(self):
        self.load()

    def load(self):
        self.__permissions__ = utils.load_json_from_file(self.__FILEPATH__, DEFAULT)

    def save(self):
        utils.dump_json_to_file(self.__permissions__, self.__FILEPATH__)

    def have_permission(self, event, permission):
        members = self._BOT_.get_vk().messages.getConversationMembers(peer_id=event.peer_id)["items"]
        member = utils.find_chat_member(members, event.user_id)
        chat_id = str(event.peer_id)
        user_id = str(event.user_id)
        if user_id in self.__permissions__:
            if utils.element_in_dot_star_list(self.__permissions__[user_id], permission):
                return True
        if event.peer_id < 2000000000:
            if utils.element_in_dot_star_list(self.__permissions__[PRIVATE_PERMISSION_KEY], permission):
                return True
        else:
            if utils.chat_member_is_admin(member, must_be_owner=True):
                if utils.element_in_dot_star_list(self.__permissions__[OWNER_PERMISSION_KEY], permission):
                    return True
            if utils.chat_member_is_admin(member):
                if utils.element_in_dot_star_list(self.__permissions__[ADMIN_PERMISSION_KEY], permission):
                    return True
            if utils.element_in_dot_star_list(self.__permissions__[MEMBER_PERMISSION_KEY], permission):
                return True
            if chat_id in self.__permissions__:
                if utils.element_in_dot_star_list(self.__permissions__[chat_id], permission):
                    return True
