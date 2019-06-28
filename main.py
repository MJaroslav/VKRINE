import vkrine.utils
import sys
from vkrine.rinebot import RINEBot
import os


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def writelines(self, data):
        self.stream.writelines(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


if __name__ == "__main__":
    sys.stdout = Unbuffered(sys.stdout)
    vkrine.utils.print_logo()
    if not os.path.isdir("runtime"):
        os.mkdir("runtime")
    token = vkrine.utils.load_token()
    if token:
        RINEBot(token).run()
else:
    print("Главный модуль VKRINE можно только исполнять!")
