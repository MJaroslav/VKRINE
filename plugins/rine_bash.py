from bs4 import BeautifulSoup, Tag, NavigableString
import urllib.request
from vkrine.modules import BotModule
from vkrine.commands import Command
from vkrine.utils import MessageBuilder

def bash_im_random_quote(bot):
    agent = bot.settings().get_option("user-agent")
    req = urllib.request.Request(url="https://bash.im/random", headers={"User-Agent": agent})
    with urllib.request.urlopen(req) as f:
        response = f.read()
    soup = BeautifulSoup(response, "html.parser")
    text_div = soup.find_all('article', class_='quote')[0].find('div', class_='quote__body')
    quote = '\n\n'.join(
        i.strip() for i in text_div.contents
        if isinstance(i, NavigableString) and i != '\n'
    )
    return quote

class CommandBash(Command):
    def __init__(self, module):
        super().__init__(module, "bash")
    
    def run(self, event, bot, line, args):
        MessageBuilder(bot, bash_im_random_quote(bot)).send(event)

class BashModule(BotModule):
    def __init__(self, bot):
        super().__init__("bash", bot)
    
    def commands(self):
        return [CommandBash(self)]