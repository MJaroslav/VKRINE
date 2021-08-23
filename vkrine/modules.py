import importlib
import inspect
import os
from operator import attrgetter

import vkrine
from .commands import *
from .eventlisteners import ChatLogger, CommandHandler


class BotModule(object):
    def __init__(self, name, bot, priority=0, switchable=True, architecture=vkrine.ARCHITECTURE_ANY, reloadable=True):
        self._BOT_ = bot
        self.NAME = name
        self.PRIORITY = priority
        self.SWITCHABLE = switchable
        self.ARCHITECTURE = architecture
        self.RELOADABLE = reloadable
        self._enable_ = False

    def enable(self):
        if not self.SWITCHABLE or self.is_enabled():
            return
        self._enable_ = True
        self._BOT_.SETTINGS.set_option("modules.{}.enable".format(self.NAME), True)
        self.load()

    def disable(self):
        if not self.SWITCHABLE or not self.is_enabled():
            return
        self._enable_ = False
        self._BOT_.SETTINGS.set_option("modules.{}.enable".format(self.NAME), False)
        self.unload()

    def is_enabled(self):
        return not self.SWITCHABLE or self._BOT_.SETTINGS.get_option("modules.{}.enable".format(self.NAME), True)

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
        super().__init__(vkrine.MODULE_NAME_CHATLOGGER, bot)

    def listeners(self):
        return [ChatLogger(self)]


class PluginLoaderModule(BotModule):
    def __init__(self, bot):
        super().__init__(vkrine.MODULE_NAME_PLUGINLOADER, bot, priority=-1)
        self.__PLUGINS_PATH__ = "plugins"
        self.__plugins__ = []

    def __find_plugins__(self):
        for filename in os.listdir(self.__PLUGINS_PATH__):
            filepath = "{}/{}".format(self.__PLUGINS_PATH__, filename)
            filename_split = os.path.splitext(filename)
            if os.path.isfile(filepath) and filename_split[1] == ".py":
                plugin = importlib.import_module("{}.{}".format(self.__PLUGINS_PATH__, filename_split[0]))
                for name, obj in inspect.getmembers(plugin):
                    if inspect.isclass(obj) and BotModule in obj.__bases__:
                        module = obj(self._BOT_)
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
        super().__init__(vkrine.MODULE_NAME_COMMANDHANDLER, bot, switchable=False)

    def listeners(self):
        return [CommandHandler(self)]

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
