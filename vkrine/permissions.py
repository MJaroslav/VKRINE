import json
import os


def __get_default__():
    result = {'roles': {}, 'users': {}, 'chats': {}}
    result['roles']['default'] = {'parents': [], 'permissions': ["command.echo", "command.help", "command.info"]}
    result['roles']['admin'] = {'parents': ["default"], 'permissions': ["*"]}
    result['users']['138952604'] = {'roles': ["admin"], 'permissions': ["*"]}
    return result


def __load_or_create__():
    file_path = "runtime/permissions.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="UTF-8") as file:
            return json.load(file)
    else:
        with open(file_path, "w", encoding="UTF-8") as file:
            default = __get_default__()
            json.dump(default, file, ensure_ascii=False, indent=2)
            return default


def split_permission(permission: str):
    result = ["*", permission]
    data = permission.split(".")
    if len(data) > 1:
        i = 1
        j = len(data)
        while i < j:
            result.append("{}.*".format(".".join(data[0:i])))
            i += 1
    return result


class Permissions(object):
    def __init__(self, bot):
        self.__bot__ = bot
        self.__data__ = __load_or_create__()

    def get_from_role(self, name):
        result = []
        if name in self.__data__['roles']:
            result += self.__data__['roles'][name]['permissions']
            for parent in self.__data__['roles'][name]['parents']:
                result += self.get_from_role(parent)
        return result

    def get_roles(self, user_id, peer_id):
        result = []
        user_str = str(user_id)
        peer_str = str(peer_id)
        if user_str in self.__data__['users']:
            result += self.__data__['users'][user_str]['roles']
        if peer_str in self.__data__['chats']:
            result += self.__data__['chats'][peer_str]['roles']
        return result

    def get_from_ids(self, user_id, peer_id):
        result = []
        user_str = str(user_id)
        peer_str = str(peer_id)
        if user_str in self.__data__['users']:
            result += self.__data__['users'][user_str]['permissions']
        if peer_str in self.__data__['chats']:
            result += self.__data__['chats'][peer_str]['permissions']
        return result

    def get_permissions(self, user_id=0, peer_id=0):
        permissions = []
        permissions += self.get_from_ids(user_id, peer_id)
        permissions += self.get_from_role("default")
        for role in self.get_roles(user_id, peer_id):
            permissions += self.get_from_role(role)
        return permissions

    def has_permission(self, permission, user_id, peer_id):
        if user_id == self.__bot__.get_owner_id() + 1:
            return True
        else:
            permissions = self.get_permissions(user_id, peer_id)
            check = split_permission(permission)
            for existed_permission in permissions:
                if existed_permission in check:
                    return True
            return False
