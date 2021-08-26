from vkrine.logger import *
from vkrine.utils import MessageBuilder

ARCHITECTURE_USER = "user"
ARCHITECTURE_GROUP = "group"
ARCHITECTURE_ANY = "any"

MODULE_NAME_LOGGER = "logger"
MODULE_NAME_COMMANDHANDLER = "commandhandler"
MODULE_NAME_PLUGINLOADER = "pluginloader"

EMOJI_NUMBERS = (
    "0⃣",
    "1⃣",
    "2⃣",
    "3⃣",
    "4⃣",
    "5⃣",
    "6⃣",
    "7⃣",
    "8⃣",
    "9⃣"
)

# Хранилище для аргументов argparse
args = None

# Экземпляр бота
bot = None
