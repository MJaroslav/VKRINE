from vkrine.bots import UserBot
from vkrine.utils import load_token, print_logo

if __name__ == "__main__":
    print_logo()
    bot = UserBot(load_token("runtime/token"))
    bot.login()
    bot.load()
    bot.run()

