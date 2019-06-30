import time

from requests.exceptions import ReadTimeout
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll

from vkrine import utils
from vkrine.permissions import Permissions


class RINEBot:
    def __init__(self, token, prefix="/", owner_id=138952604, log_chat=True):
        self.__stopped__ = False
        self.__running__ = False
        self.__paused__ = False
        self.__timeout_counter__ = 0
        self.__prefix__ = prefix
        self.__owner_id__ = owner_id
        self.__log_chat__ = log_chat
        self.__listeners__ = []
        self.__listeners_ids_ = {}
        self.__command_list__ = {}
        utils.load_listeners(self)
        utils.load_commands(self)
        self.__permissions__ = Permissions(self)
        self.__listeners__.sort(key=lambda x: x.get_priority())
        self.__token__ = token
        self.__session__ = VkApi(token=token)
        self.__api__ = self.__session__.get_api()
        self.__user__ = self.__api__.users.get(fields="domain")[0]
        print("Выполнен вход под аккаунтом @id{} ({} {}).".format(self.__user__['id'], self.__user__['first_name'],
                                                                  self.__user__['last_name']))

    def is_chat_logged(self):
        return self.__log_chat__

    def get_owner_id(self):
        return self.__owner_id__

    def get_permissions(self):
        return self.__permissions__

    def get_domain(self):
        return self.__user__['domain']

    def get_prefix(self):
        return self.__prefix__

    def get_id(self):
        return self.__user__['id']

    def get_token(self):
        return self.__token__

    def get_session(self):
        return self.__session__

    def add_listener(self, listener):
        self.__listeners__.append(listener)
        self.__listeners_ids_[listener.get_listener_name()] = listener

    def get_listener(self, name):
        if name in self.__listeners_ids_:
            return self.__listeners_ids_[name]

    def get_listeners(self):
        return self.__listeners__

    def add_command(self, command):
        self.__command_list__[command.get_command_name()] = command

    def get_commands(self):
        return self.__command_list__

    def get_command(self, text):
        if text.lower() in self.__command_list__:
            return self.__command_list__[text.lower()]

    def get_api(self):
        return self.__api__

    def is_running(self):
        return not self.is_stopped() and not self.is_paused() and self.__running__

    def is_stopped(self):
        return self.__stopped__

    def is_paused(self):
        return self.__paused__

    def pause(self):
        self.__paused__ = True

    def resume(self):
        self.__paused__ = False

    def reply(self, event, text):
        if text:
            self.get_api().messages.send(peer_id=event.peer_id, message=text, random_id=int(time.time() * 1000))

    def run(self):
        self.__running__ = True
        self.run_loop()

    def run_loop(self):
        if self.__timeout_counter__ < 61:
            try:
                for event in VkLongPoll(self.get_session()).listen():
                    if self.is_running():
                        for listener in self.__listeners__:
                            if listener.listen(event, self):
                                break
                        if self.is_stopped():
                            break
                    else:
                        if self.is_stopped():
                            break
            except ReadTimeout:
                while True:
                    if self.__timeout_counter__ < 61:
                        self.__timeout_counter__ += 1
                        print("Потеряно соединение с интернетом, попытка восстановить подключение номер {}...".format(
                            self.__timeout_counter__))
                        if utils.check_connection('https://vk.com'):
                            print("Соединение восстановлено!")
                            self.__timeout_counter__ = 0
                            flag = True
                            break
                        else:
                            time.sleep(30)
                    else:
                        print("Не удалось восстановить подключение к интернету!")
                        flag = False
                        break
                if flag:
                    self.run_loop()

    def stop(self):
        self.__stopped__ = True
