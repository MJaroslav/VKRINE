import sys
import datetime

__levels__ = ["debug", "chat", "info", "warn", "error"]

def get_log_level():
    level = "info"
    if "--logger-level" in sys.argv:
        i = sys.argv.index("--logger-level")
    elif "-l" in sys.argv:
        i = sys.argv.index("-l")
    else:
        i = -1
    if i > -1:
        i += 1
        raw = sys.argv[i]
        if raw in __levels__:
            level = raw
    return level

def timestamp():
    return datetime.datetime.now().strftime("%d-%m-%Y %H:%M ")

def gen_prefix(level):
    return timestamp() + "[{}] ".format(level)

def check_log_level(level):
    return level not in __levels__[:__levels__.index(get_log_level())]

def debug(text: str, *args, **kwargs):
    if check_log_level("debug"):
        print(gen_prefix("debug") + text.format(*args, **kwargs))

def chat(text: str, *args, **kwargs):
    if check_log_level("chat"):
        print(gen_prefix("chat") + text.format(*args, **kwargs))

def info(text: str, *args, **kwargs):
    if check_log_level("info"):
        print(gen_prefix("info") + text.format(*args, **kwargs))

def warn(text: str, *args, **kwargs):
    if check_log_level("warn"):
        print(gen_prefix("warn") + text.format(*args, **kwargs))

def error(text: str, *args, **kwargs):
    if check_log_level("error"):
        print(gen_prefix("error") + text.format(*args, **kwargs))