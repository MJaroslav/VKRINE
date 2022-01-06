import datetime
import vkrine

ALL = "ALL"
FINEST = "FINEST"
FINER = "FINER"
FINE = "FINE"
CHAT = "CHAT"
CONFIG = "CONFIG"
INFO = "INFO"
WARNING = "WARNING"
SEVERE = "SEVERE"
OFF = "OFF"

LEVELS = [ALL, FINEST, FINER, FINE, CHAT, CONFIG, INFO, WARNING, SEVERE, OFF]


def log(level, text, *args, **kwargs):
    if __can_log__(level):
        __print__(level, text.format(*args, **kwargs))


def severe(text, *args, **kwargs):
    log(SEVERE, text, *args, **kwargs)


def warning(text, *args, **kwargs):
    log(WARNING, text, *args, **kwargs)


def info(text, *args, **kwargs):
    log(INFO, text, *args, **kwargs)


def config(text, *args, **kwargs):
    log(CONFIG, text, *args, **kwargs)


def chat(text, *args, **kwargs):
    log(CHAT, text, *args, **kwargs)


def fine(text, *args, **kwargs):
    log(FINE, text, *args, **kwargs)


def finer(text, *args, **kwargs):
    log(FINER, text, *args, **kwargs)


def finest(text, *args, **kwargs):
    log(FINEST, text, *args, **kwargs)


def __get_level__():
    return vkrine.args.logger_level


def __timestamp__():
    return datetime.datetime.now().strftime("%d-%m-%Y %H:%M ")


def __make_prefix__(level):
    return __timestamp__() + "[{}] ".format(level)


def __can_log__(level):
    return level not in LEVELS[:LEVELS.index(__get_level__())]


# TODO: Сделать разные виды вывода, как минимум параллельный консоль-файл
def __print__(level, text):
    for line in text.split("\n"):
        print(__make_prefix__(level) + line)


class VkApiLoggedMethod(object):
    __slots__ = ('_vk', '_method')

    def __init__(self, vk, method=None):
        self._vk = vk
        self._method = method

    def __getattr__(self, method):
        if '_' in method:
            m = method.split('_')
            method = m[0] + ''.join(i.title() for i in m[1:])

        return VkApiLoggedMethod(
            self._vk,
            (self._method + '.' if self._method else '') + method
        )

    def __call__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, (list, tuple)):
                kwargs[k] = ','.join(str(x) for x in v)
        params = kwargs if kwargs else "None"
        result = self._vk.method(self._method, kwargs)
        finer("[VK API] Method {}, params: {}, result:\n{}", self._method, params, result)
        return result
