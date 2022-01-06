import datetime
import vkrine
import threading

ALL = "ALL"
FINEST = "FINEST"
FINER = "FINER"
FINE = "FINE"
INFO = "INFO"
WARNING = "WARNING"
SEVERE = "SEVERE"
OFF = "OFF"

LEVELS = [ALL, FINEST, FINER, FINE, INFO, WARNING, SEVERE, OFF]


def log(level, tag, text, *args, **kwargs):
    if __can_log__(level):
        __print__(level, tag, text.format(*args, **kwargs))


def severe(tag, text, *args, **kwargs):
    log(SEVERE, tag, text, *args, **kwargs)


def warning(tag, text, *args, **kwargs):
    log(WARNING, tag, text, *args, **kwargs)


def info(tag, text, *args, **kwargs):
    log(INFO, tag, text, *args, **kwargs)


def fine(tag, text, *args, **kwargs):
    log(FINE, tag, text, *args, **kwargs)


def finer(tag, text, *args, **kwargs):
    log(FINER, tag, text, *args, **kwargs)


def finest(tag, text, *args, **kwargs):
    log(FINEST, tag, text, *args, **kwargs)


def __get_level__():
    return vkrine.args.logger_level


def __get_thread_name__():
    return threading.currentThread().name


def __timestamp__():
    return datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def __can_log__(level):
    return level not in LEVELS[:LEVELS.index(__get_level__())]


# TODO: Сделать разные виды вывода, как минимум параллельный консоль-файл
def __print__(level, tag, text):
    for line in text.split("\n"):
        print("{} [{}|{}|{}]: {}"
              .format(__timestamp__(), __get_thread_name__(), tag, level, line))


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
        finer("VK API", "Method {}, params: {}, result:\n{}", self._method, params, result)
        return result
