from vk_api.longpoll import VkEventType


class Listener(object):
    def __init__(self, name, priority=0):
        self.__priority__ = priority
        self.__listener_name__ = name

    def get_listener_name(self):
        return self.__listener_name__

    def listen(self, event, bot):
        pass

    def get_priority(self):
        return self.__priority__


class MessageListener(Listener):
    def __init__(self, name, can_execute_by_self=False, priority=0):
        super().__init__(name, priority)
        self.__can_execute_by_self__ = can_execute_by_self

    def __can_execute__(self, event, bot):
        return event.user_id != bot.get_id() or self.__can_execute_by_self__

    def execute(self, event, bot):
        pass

    def listen(self, event, bot):
        if event.type == VkEventType.MESSAGE_NEW:
            if self.__can_execute__(event, bot):
                return self.execute(event, bot)
