class Command(object):
    def __init__(self, command_name):
        self.__command_name__ = command_name

    def get_command_name(self):
        return self.__command_name__

    def execute(self, event, bot, line, args):
        pass
