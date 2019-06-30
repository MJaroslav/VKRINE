import datetime
import shlex

import vkrine.utils
from vkrine.listeners import MessageListener
from vkrine.exceptions import RineException


class ChatLoggerListener(MessageListener):
    def execute(self, event, bot):
        if bot.is_chat_logged():
            user = bot.get_api().users.get(user_ids=event.user_id)[0]
            peer = ""
            if event.peer_id != event.user_id:
                peer = "{} ({}) | ".format(event.peer_id,
                                           bot.get_api().messages.getConversationsById(peer_ids=event.peer_id)['items'][
                                               0][
                                               'chat_settings']['title'])
            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            print(
                "{}: {}@id{} ({} {}): {}".format(now, peer, user['id'], user['first_name'], user['last_name'],
                                                 vkrine.utils.decode_text(event.text)))


class CommandListener(MessageListener):
    def execute(self, event, bot):
        text = vkrine.utils.decode_text(event.text)
        command_raw = vkrine.utils.try_remove_prefix(text, bot)
        if len(command_raw) != len(text):
            command_raw = command_raw.split()
            command = bot.get_command(command_raw[0])
            if command:
                try:
                    if bot.get_permissions().has_permission(command.get_permission(), event.user_id, event.peer_id):
                        line = " ".join(command_raw[1:])
                        command.execute(event, bot, vkrine.utils.decode_quot(line), shlex.split(line))
                        return True
                except RineException as rine_error:
                    rine_error.reply(event, bot)


def get_listeners():
    return [ChatLoggerListener("rine_chat_logger", priority=-1), CommandListener("rine_commands")]
