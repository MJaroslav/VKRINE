from .eventlisteners import ChatLogger, CommandHandler
import vkrine.commands as cmds

CHATLOGGER_MODULE_NAME = "chatlogger"
COMMANDHANDLER_MODULE_NAME = "commandhandler"

class BotModule(object):
    def __init__(self, name, bot):
        self.BOT = bot
        self.NAME = name

    def listeners(self):
        return []
    
    def commands(self):
        return []

    def load(self):
        pass

    def unload(self):
        pass

    def reload(self):
        pass


class ChatLoggerModule(BotModule):
    def __init__(self, bot):
        super().__init__(CHATLOGGER_MODULE_NAME, bot)
    
    def listeners(self):
        return [ChatLogger()]

class CommandHandlerModule(BotModule):
    def __init__(self, bot):
        super().__init__(COMMANDHANDLER_MODULE_NAME, bot)
    
    def listeners(self):
        return [CommandHandler(self.BOT)]
    
    def commands(self):
        return [cmds.CommandCaptcha(), cmds.CommandEcho(), cmds.CommandHelp(), cmds.CommandLocale(), cmds.CommandReload(), cmds.CommandStop(), cmds.CommandRoll()]