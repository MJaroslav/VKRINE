
import datetime
import vkrine.utils as utils
from vk_api.longpoll import VkEventType
from vk_api.bot_longpoll import VkBotEventType
from .utils import MessageBuilder
import vkrine.exceptions as exceptions
import shlex
import traceback


class EventListener(object):
    def __init__(self, module, priority=0):
        self.PRIORITY = priority
        self.MODULE = module

    def on_event(self, event, bot):
        pass

class MessageListener(EventListener):
    def __init__(self, module, priority=0, call_itself=False):
        super().__init__(module, priority)
        self.__call_itself__ = call_itself

    def __can_call__(self, event, bot):
        return not event.from_me or self.__call_itself__

    def on_event(self, event, bot):
        if (event.type == VkEventType.MESSAGE_NEW or event.type == VkBotEventType.MESSAGE_NEW) and self.__can_call__(event, bot):
            self._on_message_(event, bot)

    def _on_message_(self, event, bot):
        pass


class ChatLogger(MessageListener):
    def _on_message_(self, event, bot):
        if "messages" in bot.SETTINGS.get_option("chat.logging", chat_id=event.peer_id):
            utils.log_message_event(bot, event)



class CommandHandler(MessageListener):
    def __init__(self, module, priority=0):
        super().__init__(module, priority)
        self.BOT = self.MODULE.BOT

    def _on_message_(self, event, bot):
        text = utils.decode_text(event.text)
        command_raw = utils.try_remove_prefix(text, bot, event.peer_id)
        if len(command_raw) != len(text):
            command_raw = command_raw.split()
            try:
                command = self.get_command(event, command_raw[0])
                if bot.PERMISSIONS.have_permission(event, command.get_permission()):
                    line = " ".join(command_raw[1:])
                    if "commands" in bot.SETTINGS.get_option("chat.logging", event.peer_id):
                        utils.log_message_event(bot, event)
                    command.run(event, bot, utils.decode_quot(
                        line), shlex.split(line))
                    return True
                else:
                    MessageBuilder().translate("commands.generic.permission").send(bot, event=event)
            except exceptions.WrongUsageException as e:
                message = bot.L10N.translate(event, command.get_help())
                MessageBuilder().translate("commands.generic.usage", message).send(bot, event=event)
            except exceptions.CommandException as e:
                MessageBuilder().translate(e.get_message(), *e.get_args(), **e.get_kwargs()).send(bot, event=event)
            except Exception as e:
                MessageBuilder().translate("commands.generic.exception", e).send(bot, event=event)
                traceback.print_exc()

    def get_command(self, event, phrase):
        for command in self.BOT.commands():
            if command.NAME == phrase:
                return command
            if command.get_aliases_key():
                if phrase in self.BOT.L10N.translate_list(event, command.get_aliases_key()):
                    return command
                if phrase in self.BOT.L10N.translate_list(None, command.get_aliases_key()):
                    return command
        raise exceptions.CommandNotFoundException(None)
