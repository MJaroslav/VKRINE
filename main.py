from vkrine.bots import UserBot, GroupBot
from vkrine.utils import load_token, print_logo

if __name__ == "__main__":
    print_logo()
    bot = UserBot(load_token("runtime_user/token", True), runtime="runtime_user")
    #token = load_token("runtime_group/token")
    #bot = GroupBot(token[0], token[1], runtime="runtime_group")
    bot.login()
    bot.load()
    bot.run()

