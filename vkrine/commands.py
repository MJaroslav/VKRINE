from vkrine.eventlisteners import MessageListener
import vkrine.utils as utils
import shlex
import vkrine.exceptions as exceptions
import sys
import re
import traceback
from .utils import MessageBuilder
import random


class Command(object):
    def __init__(self, name):
        self.NAME = name

    def get_aliases_key(self):
        return "commands.{}.aliases".format(self.NAME)

    def run(self, event, bot, line, args):
        pass

    def get_permission(self):
        return "command.{}".format(self.NAME)

    def get_help(self):
        return "help.{}".format(self.NAME)

    def get_help_extended(self):
        return "help.{}.extended".format(self.NAME)

    def get_arg_key(self, arg):
        return "commands.{}.{}".format(self.NAME, arg)

    def get_arg_permission(self, arg):
        return "command.{}.{}".format(self.NAME, arg)
    
    def done(self, bot, event):
        MessageBuilder().translate("commands.done").send(bot, event=event)


def is_arg(bot, event, arg, key, phrase):
    if arg == phrase:
        return True
    if phrase in bot.L10N.translate_list(event, key):
        return True
    if phrase in bot.L10N.translate_list(None, key):
        return True


def have_permission(bot, event, permission):
    if not bot.PERMISSIONS.have_permission(event, permission):
        raise exceptions.CommandException("commands.generic.permission")


def parse_int(arg):
    try:
        return int(arg)
    except ValueError:
        raise exceptions.NumberInvalidException(None, arg)


def parse_int_with_min(arg, min):
    return parse_int_bounded(arg, min, sys.maxint)


def parse_int_bounded(arg, min, max):
    result = parse_int(arg)
    if result > max:
        raise exceptions.NumberInvalidException(
            "commands.generic.num.to_big", arg, max)
    elif result < min:
        raise exceptions.NumberInvalidException(
            "commands.generic.num.to_small", arg, min)
    else:
        return result


def parse_float(arg):
    try:
        f = float(arg)
        f.as_integer_ratio()
        return f
    except ValueError or OverflowError:
        raise exceptions.NumberInvalidException(None, arg)


def parse_float_with_min(arg, min):
    return parse_float_bounded(arg, min, sys.maxint)


def parse_float_bounded(arg, min, max):
    result = parse_float(arg)
    if result > max:
        raise exceptions.NumberInvalidException(
            "commands.generic.float.to_big", arg, max)
    elif result < min:
        raise exceptions.NumberInvalidException(
            "commands.generic.float.to_small", arg, min)
    else:
        return result


def parse_bool(arg):
    if arg != "true" and arg != "1":
        if arg != "false" and arg != "0":
            raise exceptions.CommandException(
                "commands.generic.boolean.invalid", arg)
        else:
            return False
    else:
        return True


def get_user(bot, arg):
    mentioned = re.sub(r'^((\[(\S+?)\|\S+?\])|(@(\S+)( \(\S+?\))?))',
                       r'\3\5', arg, re.IGNORECASE + re.DOTALL)
    if len(mentioned) != len(arg):
        uid = mentioned.split()[0].lower()
    else:
        uid = arg
    users = bot.VK.users.get(user_ids=uid)
    l = len(users)
    if l > 0:
        if l > 1:
            return users
        else:
            return users[0]
    else:
        raise exceptions.UserNotFoundException(None, arg)


class CommandEcho(Command):
    def __init__(self):
        super().__init__("echo")

    def run(self, event, bot, line, args):
        MessageBuilder(line).send(bot, event=event)


class CommandReload(Command):
    def __init__(self):
        super().__init__("reload")

    def run(self, event, bot, line, args):
        bot.reload()
        self.done(bot, event)


class CommandStop(Command):
    def __init__(self):
        super().__init__("stop")

    def run(self, event, bot, line, args):
        bot.stop()
        self.done(bot, event)


class CommandLocale(Command):
    def __init__(self):
        super().__init__("locale")

    def run(self, event, bot, line, args):
        l = len(args)
        if l == 0:
            raise exceptions.WrongUsageException(None)
        if is_arg(bot, event, "global", self.get_arg_key("global"), args[0]):
            have_permission(bot, event, self.get_arg_permission("global"))
            if l == 2:
                locale = args[1]
                if locale == "default":
                    bot.L10N.set_locale("@main", "en_US")
                    self.done(bot, event)
                elif bot.L10N.has_locale(locale):
                    bot.l10n().set_locale("@main", locale)
                    self.done(bot, event)
                else:
                    MessageBuilder().translate("commands.text.locale.not_found", locale).send(bot, event=event)
            elif l == 1:
                locale = bot.L10N.get_locale_key("@main")
                MessageBuilder().translate("commands.text.locale.current", locale).send(bot, event=event)
            else:
                raise exceptions.WrongUsageException(None)
        elif is_arg(bot, event, "chat", self.get_arg_key("chat"), args[0]):
            have_permission(bot, event, self.get_arg_permission("chat"))
            if l == 2:
                locale = args[1]
                if locale == "default":
                    bot.L10N.reset_locale(str(event.peer_id))
                    self.done(bot, event)
                elif bot.l10n().has_locale(locale):
                    bot.L10N.set_locale(str(event.peer_id), locale)
                    self.done(bot, event)
                else:
                    MessageBuilder().translate("commands.text.locale.not_found", locale).send(bot, event=event)
            elif l == 1:
                locale = bot.L10N.get_locale_key(event.peer_id)
                MessageBuilder().translate("commands.text.locale.current", locale).send(bot, event=event)
            else:
                raise exceptions.WrongUsageException(None)
        elif is_arg(bot, event, "personal", self.get_arg_key("personal"), args[0]):
            have_permission(bot, event, self.get_arg_permission("personal"))
            if l == 2:
                locale = args[1]
                if locale == "default":
                    bot.L10N.reset_locale(str(event.user_id))
                    self.done(bot, event)
                elif bot.L10N.has_locale(locale):
                    bot.L10N.set_locale(str(event.user_id), locale)
                    self.done(bot, event)
                else:
                    MessageBuilder().translate("commands.text.locale.not_found", locale).send(bot, event=event)
            elif l == 1:
                locale = bot.L10N.get_locale_key(event.user_id)
                MessageBuilder().translate("commands.text.locale.current", locale).send(bot, event=event)
            else:
                raise exceptions.WrongUsageException(None)
        elif is_arg(bot, event, "list", self.get_arg_key("list"), args[0]):
            if l == 1:
                MessageBuilder().translate("commands.text.locale.list", ", ".join(bot.L10N.locales())).send(bot, event=event)
            else:
                raise exceptions.WrongUsageException(None)
        else:
            raise exceptions.WrongUsageException(None)


class CommandHelp(Command):
    def __init__(self):
        super().__init__("help")
        self.__pages__ = None

    def __init_pages_lazy__(self, bot):
        if not self.__pages__:
            commands = bot.commands()
            self.__pages__ = [commands[i:i+8]
                              for i in range(0, len(commands), 8)]

    def run(self, event, bot, line, args):
        self.__init_pages_lazy__(bot)
        page = 0
        command_name = None
        if len(args) > 0:
            try:
                page = parse_int_bounded(
                    bot, args[0], 0, len(self.__pages__) - 1)
            except exceptions.NumberInvalidException:
                command_name = args[0]
        if command_name:
            command = bot.COMMANDHANDLER.get_command(event, command_name)
            aliases = bot.L10N.translate_list(event, command.get_aliases_key())
            aliases += bot.L10N.translate_list(None, command.get_aliases_key())
            aliases = "', '".join(aliases)
            if not aliases:
                aliases = bot.L10N.translate(event, "commands.none")
            else:
                aliases = "'{}'".format(aliases)
            MessageBuilder().translate(command.get_help_extended()).newline(True).translate("help.aliases", aliases).send(bot, event=event)
        else:
            page_data = []
            for command in self.__pages__[page]:
                text = "{} - {}".format(command.NAME, bot.L10N.translate(event, command.get_help()))
                page_data.append(text)
            MessageBuilder().translate("help.page", page, "\n".join(page_data)).send(bot, event=event)

class CommandCaptcha(Command):
    def __init__(self):
        super().__init__("captcha")
    
    def run(self, event, bot, line, args):
        if len(args) == 1:
            answer = args[0]
            if bot.__current_captcha__:
                bot.__current_captcha__.try_again(answer)
                self.done(bot, event)
                bot.__current_captcha__ = None
            else:
                MessageBuilder().translate("text.captcha.none").send(bot, event=event)
        else:
            raise exceptions.WrongUsageException(None)

class CommandRoll(Command):
    def __init__(self):
        super().__init__("roll")
    
    def run(self, event, bot, line, args):
        if args:
            l = len(args)
            min_roll = 0
            if l == 1:
                max_roll = parse_int(args[0])
            elif l == 2:
                mix_roll = parse_int(args[0])
                max_roll = parse_int(args[1])
            else:
                raise exceptions.WrongUsageException(None)
            roll = random.randint(min_roll, max_roll)
            MessageBuilder().translate("commands.text.roll", roll).send(bot, event=event)
        else:
            roll = random.randint(0, 100)
            MessageBuilder().translate("commands.text.roll", roll).send(bot, event=event)
