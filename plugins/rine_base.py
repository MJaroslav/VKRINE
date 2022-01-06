import random

import vkrine
import vkrine.commands as cmds
import vkrine.exceptions as exceptions
from vkrine.modules import BotModule


class CommandEcho(cmds.Command):
    def __init__(self, module):
        super().__init__(module, "echo")

    def run(self, event, bot, line, args):
        vkrine.MessageBuilder(line).send(event)


class CommandRoll(cmds.Command):
    def __init__(self, module):
        super().__init__(module, "roll")

    def run(self, event, bot, line, args):
        if args:
            s = len(args)
            min_roll = 0
            if s == 1:
                max_roll = cmds.parse_int(args[0])
            elif s == 2:
                min_roll = cmds.parse_int(args[0])
                max_roll = cmds.parse_int(args[1])
                if min_roll >= max_roll:
                    raise exceptions.CommandSyntaxError("commands.text.roll.bad_range")
            else:
                raise exceptions.CommandWrongUsageException(None)
            roll = random.randint(min_roll, max_roll)
            vkrine.MessageBuilder().translated_text("commands.text.roll", roll).send(event)
        else:
            roll = random.randint(0, 100)
            vkrine.MessageBuilder().translated_text("commands.text.roll", roll).send(event)


class BaseModule(BotModule):
    def __init__(self, bot):
        super().__init__("base", bot)

    def commands(self):
        return [CommandEcho(self),
                CommandRoll(self)]
