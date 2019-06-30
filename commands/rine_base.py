from vkrine.commands import Command
import vkrine.utils
from vkrine.exceptions import NotEnoughArgumentsError


class CommandExit(Command):
    def execute(self, event, bot, line, args):
        print("Бот остановлен командой!")
        print("Остановка", end="")
        vkrine.utils.sleep_log(3)
        bot.reply(event, "Бот остановлен!")
        bot.stop()
        print("Бот остановлен!")
        return True


class CommandEcho(Command):
    def execute(self, event, bot, line, args):
        if len(args) == 0:
            raise NotEnoughArgumentsError(0, 1, True)
        if args[0] == "-detail" or args[0] == "-d":
            bot.reply(event, "Линия:\n{}\nАргументы:\n{}".format(line, "\n".join(args)))
        else:
            bot.reply(event, line)
        return True


class CommandInfo(Command):
    def execute(self, event, bot, line, args):
        return True


def get_commands():
    return [CommandExit("exit"), CommandEcho("echo")]
