import argparse
import sys

import vkrine

from vkrine.bots import UserBot, GroupBot
from vkrine.utils import load_token, print_logo, create_dirs_if_not_exists


def init():
    parser = argparse.ArgumentParser(description="VKRINE Bot default runner")
    parser.add_argument("-a", "--architecture", default="group", choices=["group", "user"], metavar='type',
                        help="Select bot realization")
    parser.add_argument("-l", "--logger-level", default=vkrine.INFO, choices=vkrine.LEVELS,
                        metavar='type', help="Select logger log level")
    parser.add_argument("-r", "--runtime", metavar='rundir',
                        help="Select runtime directory, default 'runtime_<architecture>'")
    return parser.parse_args(sys.argv[1:])


if __name__ == "__main__":

    print_logo()

    args = init()
    vkrine.args = args
    architecture = args.architecture
    if args.runtime:
        runtime = args.runtime
    else:
        runtime = "runtime_" + architecture
    create_dirs_if_not_exists(runtime)
    if architecture == "user":
        bot = UserBot(load_token("%s/token" % runtime, True), runtime=runtime)
    else:
        token = load_token("%s/token" % runtime)
        bot = GroupBot(token[0], token[1], runtime=runtime)
    vkrine.bot = bot

    bot.login()
    bot.load_modules()
    bot.run()
