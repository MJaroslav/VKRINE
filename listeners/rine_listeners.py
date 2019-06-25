import shlex

import vkrine.utils
from vkrine.listeners import MessageListener


class ChatLoggerListener(MessageListener):
    def execute(self, event, bot):
        user = bot.get_api().users.get(user_ids=event.user_id)[0]
        peer = ""
        if event.peer_id != event.user_id:
            peer = "{} ({}) | ".format(event.peer_id,
                                       bot.get_api().messages.getConversationsById(peer_ids=event.peer_id)['items'][0][
                                           'chat_settings']['title'])
        print("{}@id{} ({} {}): {}".format(peer, user['id'], user['first_name'], user['last_name'], event.text))


class CommandListener(MessageListener):
    def execute(self, event, bot):
        command_raw = vkrine.utils.try_remove_prefix(event.text, bot)
        if len(command_raw) != len(event.text):
            command_raw = command_raw.split()
            command = bot.get_command(command_raw[0])
            if command:
                line = " ".join(command_raw[1:])
                return command.execute(event, bot, line, shlex.split(line))


def get_listeners():
    return [ChatLoggerListener(), CommandListener()]
