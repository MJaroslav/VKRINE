from .eventlisteners import ChatLogger, CommandHandler
from .commands import *
import vkrine.consts as consts
import importlib
import os
import inspect
from operator import attrgetter

class BotModule(object):
    def __init__(self, name, bot, priority=0, switchable=True):
        self.BOT = bot
        self.NAME = name
        self.PRIORITY = priority
        self.enabled = False
        self.SWITCHABLE = switchable

    def enable(self):
        if not self.SWITCHABLE or self.is_enabled():
            return
        self.enabled = True
        self.BOT.SETTINGS.set_option("modules.{}.enable".format(self.NAME), True)
        self.load()
    
    def disable(self):
        if not self.SWITCHABLE or not self.is_enabled():
            return
        self.enabled = False
        self.BOT.SETTINGS.set_option("modules.{}.enable".format(self.NAME), False)
        self.unload()

    def is_enabled(self):
        return not self.SWITCHABLE or self.BOT.SETTINGS.get_option("modules.{}.enable".format(self.NAME), True)

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
        super().__init__(consts.MODULE_NAME_CHATLOGGER, bot)
    
    def listeners(self):
        return [ChatLogger(self)]

class PluginLoaderModule(BotModule):
    def __init__(self, bot):
        super().__init__(consts.MODULE_NAME_PLUGINLOADER, bot, priority=-1)
        self.PLUGINDIRPATH = "plugins"
        self.__plugins__ = []

    def __find_plugins__(self):
        for filename in os.listdir(self.PLUGINDIRPATH):
            filepath = "{}/{}".format(self.PLUGINDIRPATH, filename)
            filenamesplit = os.path.splitext(filename)
            if os.path.isfile(filepath) and filenamesplit[1] == ".py":
                plugin = importlib.import_module("{}.{}".format(self.PLUGINDIRPATH, filenamesplit[0]))
                for name, obj in inspect.getmembers(plugin):
                    if inspect.isclass(obj) and BotModule in obj.__bases__:
                        module = obj(self.BOT)
                        if module.is_enabled():
                            self.__plugins__.append(module)
        self.__plugins__.sort(key=attrgetter("PRIORITY", "NAME"))

    def load(self):
        self.__find_plugins__()
        for plugin in self.__plugins__:
            if plugin.is_enabled():
                plugin.load()

    def listeners(self):
        result = []
        for plugin in self.__plugins__:
            if plugin.is_enabled():
                listeners = plugin.listeners()
                listeners.sort(key=attrgetter("PRIORITY"))
                result += listeners
        return result
        
    def commands(self):
        result = []
        for plugin in self.__plugins__:
            if plugin.is_enabled():
                result += plugin.commands()
        return result

    def unload(self):
        for plugin in self.__plugins__:
            if plugin.is_enabled():
                plugin.unload()

    def reload(self):
        self.__plugins__.clear()
        self.__find_plugins__()
        for plugin in self.__plugins__:
            if plugin.is_enabled():
                plugin.reload()

class CommandHandlerModule(BotModule):
    def __init__(self, bot):
        super().__init__(consts.MODULE_NAME_COMMANDHANDLER, bot, switchable=False)
        self.COMMANDHANDLER = CommandHandler(self)
    
    def listeners(self):
        return [self.COMMANDHANDLER]
    
    def commands(self):
        return [
            CommandCaptcha(self), 
            CommandEcho(self), 
            CommandHelp(self), 
            CommandLocale(self), 
            CommandReload(self), 
            CommandStop(self), 
            CommandRoll(self), 
            ]
