import urllib.request

# noinspection PyProtectedMember
from bs4 import BeautifulSoup, NavigableString

import vkrine
from vkrine.commands import Command
from vkrine.modules import BotModule


def bash_im_random_quote():
    agent = vkrine.bot.SETTINGS.get_option("user-agent")
    req = urllib.request.Request(url="http://bashorg.org/casual", headers={"User-Agent": agent})
    with urllib.request.urlopen(req) as f:
        response = f.read()
    soup = BeautifulSoup(response, "html.parser")
    text_div = soup.find_all('div', class_='q')[0].find_all('div')[1]
    quote = '\n\n'.join(
        i.strip() for i in text_div.contents
        if isinstance(i, NavigableString) and i != '\n'
    )
    return quote


class CommandBash(Command):
    def __init__(self, module):
        super().__init__(module, "bash")

    def run(self, event, bot, line, args):
        vkrine.MessageBuilder(bash_im_random_quote()).send(event)


class BashModule(BotModule):
    def __init__(self, bot):
        super().__init__("bash", bot)

    def commands(self):
        return [CommandBash(self)]
