from vkrine.commands import Command


class CommandExit(Command):
    def execute(self, event, bot, line, args):
        bot.reply(event, "Бот остановлен!")
        print("Бот остановлен командой!")
        bot.stop()
        return True


class CommandEcho(Command):
    def execute(self, event, bot, line, args):
        bot.reply(event, line)
        return True


def get_commands():
    return [CommandExit("exit"), CommandEcho("echo")]
