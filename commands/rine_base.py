from vkrine.commands import Command
import vkrine.utils


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
        bot.reply(event, line)
        return True


class CommandInfo(Command):
    def execute(self, event, bot, line, args):
        return True


def get_commands():
    return [CommandExit("exit"), CommandEcho("echo")]
