from vkrine.bots import UserBot, GroupBot
from vkrine.utils import load_token, print_logo
import sys
import argparse


def init():
    parser = argparse.ArgumentParser(description="VKRINE Bot default runner")
    parser.add_argument("-a", "--architecture", default="group", choices=["group", "user"], metavar='type', help="Select bot realization")
    parser.add_argument("-l", "--logger-level", default="info", choices=["debug", "chat", "info", "warn", "error"], metavar='type', help="Select logger log level")
    parser.add_argument("-r", "--runtime", metavar='rundir', help="Select runtime directory, default 'runtime_<architecture>'")
    return parser.parse_args(sys.argv[1:])

if __name__ == "__main__":
    print_logo()

    args = init()
    architecture = args.architecture
    if args.runtime:
        runtime = args.runtime
    else:
        runtime = "runtime_" + architecture
    if architecture == "user":
        bot = UserBot(load_token("runtime_user/token", True), runtime="runtime_user")
    else:
        token = load_token("runtime_group/token")
        bot = GroupBot(token[0], token[1], runtime="runtime_group")

    bot.login()
    bot.load()
    bot.run()

