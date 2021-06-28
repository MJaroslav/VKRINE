from .eventlisteners import ChatLogger, CommandHandler
from .commands import *
import vkrine.consts as consts
import importlib
import os
import inspect
from operator import attrgetter

class BotModule(object):
    def __init__(self, name, bot, priority=0, switchable=True, architecture=consts.ARCHITECTURE_ANY, reloadable=True):
        self._bot_ = bot
        self._module_name_ = name
        self._priority_ = priority
        self._enable_ = False
        self._switchable_ = switchable
        self._architecture_ = architecture
        self._reloadable_ = reloadable

    def is_switchable(self):
        return self._switchable_

    def is_reloadable(self):
        return self._reloadable_

    def enable(self):
        if not self.is_switchable() or self.is_enabled():
            return
        self._enable_ = True
        self._bot_.settings().set_option("modules.{}.enable".format(self._module_name_), True)
        self.load()
    
    def disable(self):
        if not self.is_switchable() or not self.is_enabled():
            return
        self._enable_ = False
        self._bot_.settings().set_option("modules.{}.enable".format(self._module_name_), False)
        self.unload()

    def is_enabled(self):
        return not self._switchable_ or self._bot_.settings().get_option("modules.{}.enable".format(self._module_name_), True)

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
        self._pluginspath_ = "plugins"
        self._plugins_ = []

    def _find_plugins_(self):
        for filename in os.listdir(self._pluginspath_):
            filepath = "{}/{}".format(self._pluginspath_, filename)
            filenamesplit = os.path.splitext(filename)
            if os.path.isfile(filepath) and filenamesplit[1] == ".py":
                plugin = importlib.import_module("{}.{}".format(self._pluginspath_, filenamesplit[0]))
                for name, obj in inspect.getmembers(plugin):
                    if inspect.isclass(obj) and BotModule in obj.__bases__:
                        module = obj(self._bot_)
                        if module.is_enabled():
                            self._plugins_.append(module)
        self._plugins_.sort(key=attrgetter("_priority_", "_module_name_"))

    def load(self):
        self._find_plugins_()
        for plugin in self._plugins_:
            if plugin.is_enabled():
                plugin.load()

    def listeners(self):
        result = []
        for plugin in self._plugins_:
            if plugin.is_enabled():
                listeners = plugin.listeners()
                listeners.sort(key=attrgetter("_priority_"))
                result += listeners
        return result
        
    def commands(self):
        result = []
        for plugin in self._plugins_:
            if plugin.is_enabled():
                result += plugin.commands()
        return result

    def unload(self):
        for plugin in self._plugins_:
            if plugin.is_enabled():
                plugin.unload()

    def reload(self):
        self._plugins_.clear()
        self._find_plugins_()
        for plugin in self._plugins_:
            if plugin.is_enabled():
                plugin.reload()

class CommandHandlerModule(BotModule):
    def __init__(self, bot):
        super().__init__(consts.MODULE_NAME_COMMANDHANDLER, bot, switchable=False)
    
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
