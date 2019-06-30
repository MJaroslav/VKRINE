import vkrine.utils
from vkrine.rinebot import RINEBot
import os


if __name__ == "__main__":
    vkrine.utils.set_unbuffered_logger()
    vkrine.utils.print_logo()
    if not os.path.isdir("runtime"):
        os.mkdir("runtime")
    token = vkrine.utils.load_token()
    if token:
        RINEBot(token).run()
else:
    print("Главный модуль VKRINE можно только исполнять!")
