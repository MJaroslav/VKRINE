class RineException(Exception):
    def get_text(self):
        pass

    def reply(self, event, bot):
        bot.reply(event, self.get_text())


class NotEnoughArgumentsError(RineException):
    def __init__(self, count, required_count, minimum=False):
        self.__count__ = count
        self.__required_count__ = required_count
        self.__minimum__ = minimum

    def get_text(self):
        plus = ""
        if self.__minimum__:
            plus = " или больше"
        return "Недостаточно аргуметов: {}! Требуется {}{}!".format(self.__count__, self.__required_count__, plus)


class TooManyArgumentsError(RineException):
    def __init__(self, count, required_count, maximum=False):
        self.__count__ = count
        self.__required_count__ = required_count
        self.__maximum__ = maximum

    def get_text(self):
        minus = ""
        if self.__maximum__:
            minus = " или меньше"
        return "Слишком много аргументов: {}! Требуется {}!".format(self.__count__, self.__required_count__, minus)


class NotEnoughPermissions(RineException):
    def __init__(self, permission):
        self.__permission__ = permission

    def get_text(self):
        return "Недостаточно прав!\n- {}".format(self.__permission__)
