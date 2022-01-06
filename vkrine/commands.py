import random
import re
import sys

import vkrine
import vkrine.exceptions as exceptions
import vkrine.utils as utils


class Command(object):
    def __init__(self, module, name, bot_type=vkrine.ARCHITECTURE_ANY):
        self.MODULE = module
        self.NAME = name
        self.TYPE = bot_type

    def get_aliases_key(self):
        return "commands.{}.aliases".format(self.NAME)

    def run(self, event, bot, line, args):
        raise NotImplementedError()

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


def done(event):
    vkrine.MessageBuilder().translated_text("commands.done").send(event)


def is_arg(event, arg, key, phrase):
    if arg == phrase:
        return True
    if phrase in vkrine.bot.L10N.translate_list(event, key):
        return True
    if phrase in vkrine.bot.L10N.translate_list(None, key):
        return True


def have_permission(event, permission):
    if not vkrine.bot.PERMISSIONS.have_permission(event, permission):
        raise exceptions.CommandException("commands.generic.permission")


def parse_int(arg):
    try:
        return int(arg)
    except ValueError:
        raise exceptions.NumberInvalidException(None, arg)


def parse_int_with_min(arg, i_min):
    return parse_int_bounded(arg, i_min, sys.maxsize)


def parse_int_bounded(arg, i_min, i_max):
    result = parse_int(arg)
    if result > i_max:
        raise exceptions.NumberInvalidException(
            "commands.generic.num.to_big", arg, i_max)
    elif result < i_min:
        raise exceptions.NumberInvalidException(
            "commands.generic.num.to_small", arg, i_min)
    else:
        return result


def parse_float(arg):
    try:
        f = float(arg)
        f.as_integer_ratio()
        return f
    except ValueError or OverflowError:
        raise exceptions.NumberInvalidException(None, arg)


def parse_float_with_min(arg, i_min):
    return parse_float_bounded(arg, i_min, sys.maxsize)


def parse_float_bounded(arg, i_min, i_max):
    result = parse_float(arg)
    if result > i_max:
        raise exceptions.NumberInvalidException(
            "commands.generic.float.to_big", arg, i_max)
    elif result < i_min:
        raise exceptions.NumberInvalidException(
            "commands.generic.float.to_small", arg, i_min)
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


def parse_mention(arg):
    mentioned = re.sub(r'^((\[(\S+)\|\S+])|(@(\S+)( \(\S+?\))?))',
                       r'\3\5', arg, re.IGNORECASE + re.DOTALL)
    if len(mentioned) != len(arg):
        uid = mentioned.split()[0].lower()
    else:
        uid = arg
    users = vkrine.bot.get_vk().users.get(user_ids=uid)
    l = len(users)
    if l > 0:
        if l > 1:
            return users
        else:
            return users[0]
    else:
        raise exceptions.UserNotFoundException(None, arg)


class CommandEcho(Command):
    def __init__(self, module):
        super().__init__(module, "echo")

    def run(self, event, bot, line, args):
        vkrine.MessageBuilder(line).send(event)


class CommandReload(Command):
    def __init__(self, module):
        super().__init__(module, "reload")

    def run(self, event, bot, line, args):
        bot.reload_modules()
        done(event)


class CommandStop(Command):
    def __init__(self, module):
        super().__init__(module, "stop")

    def run(self, event, bot, line, args):
        done(event)
        bot.stop()


class CommandLocale(Command):
    def __init__(self, module):
        super().__init__(module, "locale")

    def run(self, event, bot, line, args):
        l = len(args)
        if l == 0:
            raise exceptions.CommandWrongUsageException(None)
        if is_arg(event, "global", self.get_arg_key("global"), args[0]):
            have_permission(event, self.get_arg_permission("global"))
            if l == 2:
                locale = args[1]
                if locale == "default":
                    bot.L10N.set_locale("@main", "en_US")
                    done(event)
                elif bot.L10N.has_locale(locale):
                    bot.L10N.set_locale("@main", locale)
                    done(event)
                else:
                    vkrine.MessageBuilder().translated_text("commands.text.locale.not_found", locale).send(event)
            elif l == 1:
                locale = bot.L10N.get_locale_key("@main")
                vkrine.MessageBuilder().translated_text("commands.text.locale.current", locale).send(event)
            else:
                raise exceptions.CommandWrongUsageException(None)
        elif is_arg(event, "chat", self.get_arg_key("chat"), args[0]):
            have_permission(event, self.get_arg_permission("chat"))
            if l == 2:
                locale = args[1]
                if locale == "default":
                    bot.L10N.reset_locale(str(event.peer_id))
                    done(event)
                elif bot.L10N.has_locale(locale):
                    bot.L10N.set_locale(str(event.peer_id), locale)
                    done(event)
                else:
                    vkrine.MessageBuilder().translated_text("commands.text.locale.not_found", locale).send(event)
            elif l == 1:
                locale = bot.L10N.get_locale_key(event.peer_id)
                vkrine.MessageBuilder().translated_text("commands.text.locale.current", locale).send(event)
            else:
                raise exceptions.CommandWrongUsageException(None)
        elif is_arg(event, "personal", self.get_arg_key("personal"), args[0]):
            have_permission(event, self.get_arg_permission("personal"))
            if l == 2:
                locale = args[1]
                if locale == "default":
                    bot.L10N.reset_locale(str(event.user_id))
                    done(event)
                elif bot.L10N.has_locale(locale):
                    bot.L10N.set_locale(str(event.user_id), locale)
                    done(event)
                else:
                    vkrine.MessageBuilder().translated_text("commands.text.locale.not_found", locale).send(event)
            elif l == 1:
                locale = bot.L10N.get_locale_key(event.user_id)
                vkrine.MessageBuilder().translated_text("commands.text.locale.current", locale).send(event)
            else:
                raise exceptions.CommandWrongUsageException(None)
        elif is_arg(event, "list", self.get_arg_key("list"), args[0]):
            if l == 1:
                vkrine.MessageBuilder().translated_text("commands.text.locale.list",
                                                        ", ".join(bot.L10N.locales())).send(event)
            else:
                raise exceptions.CommandWrongUsageException(None)
        else:
            raise exceptions.CommandWrongUsageException(None)


class CommandHelp(Command):
    def __init__(self, module):
        super().__init__(module, "help")
        self.__pages__ = None

    def __init_pages_lazy__(self, bot):
        if not self.__pages__:
            commands = bot.get_commands()
            self.__pages__ = [commands[i:i + 8]
                              for i in range(0, len(commands), 8)]

    def run(self, event, bot, line, args):
        self.__init_pages_lazy__(bot)
        page = 0
        command_name = None
        if len(args) > 0:
            try:
                page = parse_int_bounded(args[0], 0, len(self.__pages__) - 1)
            except exceptions.NumberInvalidException:
                command_name = args[0]
        if command_name:
            command = bot.get_command(event, command_name)
            aliases = bot.L10N.translate_list(event, command.get_aliases_key())
            aliases = "', '".join(aliases)
            if not aliases:
                aliases = bot.L10N.translate(event, "commands.none")
            else:
                aliases = "'{}'".format(aliases)
            vkrine.MessageBuilder().translated_text(command.get_help_extended()).newline(2).translated_text(
                "help.aliases", aliases).send(event)
        else:
            page_data = []
            for command in self.__pages__[page]:
                text = "{} - {}".format(command.NAME, bot.L10N.translate(event, command.get_help()))
                page_data.append(text)
            page = utils.emoji_numbers(page)
            vkrine.MessageBuilder().translated_text("help.page", page, "\n".join(page_data)).send(event)


class CommandCaptcha(Command):
    def __init__(self, module):
        super().__init__(module, "captcha", vkrine.ARCHITECTURE_USER)

    def run(self, event, bot, line, args):
        if len(args) == 1:
            answer = args[0]
            if bot.current_captcha:
                bot.current_captcha.try_again(answer)
                done(event)
                bot.current_captcha = None
            else:
                vkrine.MessageBuilder().translated_text("text.captcha.none").send(event)
        else:
            raise exceptions.CommandWrongUsageException(None)


class CommandRoll(Command):
    def __init__(self, module):
        super().__init__(module, "roll")

    def run(self, event, bot, line, args):
        if args:
            l = len(args)
            min_roll = 0
            if l == 1:
                max_roll = parse_int(args[0])
            elif l == 2:
                min_roll = parse_int(args[0])
                max_roll = parse_int(args[1])
            else:
                raise exceptions.CommandWrongUsageException(None)
            roll = random.randint(min_roll, max_roll)
            vkrine.MessageBuilder().translated_text("commands.text.roll", roll).send(event)
        else:
            roll = random.randint(0, 100)
            vkrine.MessageBuilder().translated_text("commands.text.roll", roll).send(event)
