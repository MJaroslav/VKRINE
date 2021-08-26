import shlex
import traceback

from vk_api.bot_longpoll import VkBotEventType
from vk_api.longpoll import VkEventType

import vkrine
import vkrine.exceptions as exceptions
import vkrine.utils as utils


class EventListener(object):
    def __init__(self, module, priority=0):
        self.PRIORITY = priority
        self._MODULE_ = module

    def on_event(self, event, bot):
        raise NotImplementedError()


class MessageListener(EventListener):
    def __init__(self, module, priority=0, call_itself=False):
        super().__init__(module, priority)
        self._CALL_ITSELF_ = call_itself

    def _can_call_(self, event, bot):
        return (event.user_id != bot.get_vk_id() or self._CALL_ITSELF_) \
               and (not bot.ARCHITECTURE == vkrine.ARCHITECTURE_GROUP or event.peer_id > 2000000000
                    and utils.bot_is_admin_in_chat(event.peer_id))

    def on_event(self, event, bot):
        if (event.type == VkEventType.MESSAGE_NEW or event.type == VkBotEventType.MESSAGE_NEW) and self._can_call_(
                event, bot):
            self._on_message_(event, bot)

    def _on_message_(self, event, bot):
        raise NotImplementedError()


class EventLogger(EventListener):
    def on_event(self, event, bot):
        vkrine.finer("[VK API] Long poll event: {}", event.__dict__)


class ChatLogger(MessageListener):
    def _on_message_(self, event, bot):
        vkrine.chat(utils.parse_message_event_to_string(event))


class CommandHandler(MessageListener):
    def _on_message_(self, event, bot):
        text = utils.decode_text(event.text)
        command_raw = utils.try_remove_prefix(text, event.peer_id)
        if len(command_raw) != len(text):
            command_raw = command_raw.split()
            command = None
            try:
                command = bot.get_command(event, command_raw[0])
                if bot.PERMISSIONS.have_permission(event, command.get_permission()):
                    line = " ".join(command_raw[1:])
                    command.run(event, bot, utils.decode_quot(line), shlex.split(line))
                    return True
                else:
                    vkrine.MessageBuilder().translated_text("commands.generic.permission").send(event)
            except exceptions.CommandWrongUsageException:
                message = bot.L10N.translate(event, command.get_help())
                vkrine.MessageBuilder().translated_text("commands.generic.usage", message).send(event)
            except exceptions.CommandException as e:
                vkrine.MessageBuilder().translated_text(e.get_message(), *e.get_args(), **e.get_kwargs()).send(event)
            except Exception as e:
                vkrine.MessageBuilder().translated_text("commands.generic.exception", e).send(event)
                traceback.print_exc()
