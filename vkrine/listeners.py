from vk_api.longpoll import VkEventType


class Listener(object):
    def __init__(self, priority=0):
        self.__priority__ = priority

    def listen(self, event, bot):
        pass

    def get_priority(self):
        return self.__priority__


class MessageListener(Listener):
    def __init__(self, can_execute_by_self=False, priority=0):
        super().__init__(priority)
        self.__can_execute_by_self__ = can_execute_by_self

    def __can_execute__(self, event, bot):
        return event.user_id != bot.get_id() or self.__can_execute_by_self__

    def execute(self, event, bot):
        pass

    def listen(self, event, bot):
        if event.type == VkEventType.MESSAGE_NEW:
            if self.__can_execute__(event, bot):
                return self.execute(event, bot)
