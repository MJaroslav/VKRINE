
import datetime
import vkrine.utils as utils
from vk_api.longpoll import VkEventType
from vk_api.bot_longpoll import VkBotEventType
from .utils import MessageBuilder
import vkrine.exceptions as exceptions
import shlex
import traceback
from .logger import *


class EventListener(object):
    def __init__(self, module, priority=0):
        self._priority_ = priority
        self._module_ = module

    def get_priority(self):
        return self._priority_
    
    def module(self):
        return self._module_

    def on_event(self, event, bot):
        pass

class MessageListener(EventListener):
    def __init__(self, module, priority=0, call_itself=False):
        super().__init__(module, priority)
        self._call_itself_ = call_itself

    def _can_call_(self, event, bot):
        return event.user_id != bot.get_vk_id() or self._call_itself_

    def on_event(self, event, bot):
        if (event.type == VkEventType.MESSAGE_NEW or event.type == VkBotEventType.MESSAGE_NEW) and self._can_call_(event, bot):
            self._on_message_(event, bot)

    def _on_message_(self, event, bot):
        pass


class ChatLogger(MessageListener):
    def _on_message_(self, event, bot):
        chat(utils.parse_message_event_to_string(bot, event))



class CommandHandler(MessageListener):
    def __init__(self, module, priority=0):
        super().__init__(module, priority)
        self._bot_ = self._module_._bot_

    def _on_message_(self, event, bot):
        text = utils.decode_text(event.text)
        command_raw = utils.try_remove_prefix(text, bot, event.peer_id)
        if len(command_raw) != len(text):
            command_raw = command_raw.split()
            try:
                command = self._bot_.get_command(event, command_raw[0])
                if bot.permissions().have_permission(event, command.get_permission()):
                    line = " ".join(command_raw[1:])
                    command.run(event, bot, utils.decode_quot(line), shlex.split(line))
                    return True
                else:
                    MessageBuilder(bot).translate("commands.generic.permission").send(event)
            except exceptions.WrongUsageException as e:
                message = bot.l10n().translate(event, command.get_help())
                MessageBuilder(bot).translate("commands.generic.usage", message).send(event)
            except exceptions.CommandException as e:
                MessageBuilder(bot).translate(e.get_message(), *e.get_args(), **e.get_kwargs()).send(event)
            except Exception as e:
                MessageBuilder(bot).translate("commands.generic.exception", e).send(event)
                traceback.print_exc()


