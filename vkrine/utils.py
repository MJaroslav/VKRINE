import importlib
import os
import re
import time
from urllib.request import urlopen


def print_logo():
    print(r"===================================================")
    print(r"=            _____  _____ _   _ ______            =")
    print(r"=           |  __ \|_   _| \ | |  ____|           =")
    print(r"=           | |__) | | | |  \| | |__              =")
    print(r"=           |  _  /  | | | . ` |  __|             =")
    print(r"=           | | \ \ _| |_| |\  | |____            =")
    print(r"=           |_|  \_\_____|_| \_|______|           =")
    print(r"=                   By MJaroslav                  =")
    print(r"=                                                 =")
    print(r"===================================================")


def load_token():
    print("Загрузка ключа доступа", end="")
    sleep_log(2)
    try:
        with open("runtime/token", "r") as file:
            token = file.readline()
        if token:
            print("Ключ доступа получен!")
            return token
        else:
            print('Впишите ключ доступа страницы ПОЛЬЗОВАТЕЛЯ в "./runtime/token" файл!')
    except FileNotFoundError:
        print('Создайте файл "./runtime/token" и впишите в него ключ доступа страницы ПОЛЬЗОВАТЕЛЯ!')


def load_listeners(bot):
    print("Подготовка внешних слушателей:")
    directory = "listeners"
    if os.path.isdir(directory):
        flag = True
        for file in filter(lambda obj: os.path.isfile("{}/{}".format(directory, obj)) and obj.endswith(".py"),
                           os.listdir(directory)):
            module_name = file[:-3]
            print(module_name, end="")
            sleep_log(1.5, end="")
            for listener in importlib.import_module("{}.{}".format(directory, module_name)).get_listeners():
                bot.add_listener(listener)
            print(" готов!")
            flag = False
        if flag:
            print("Слушателей не обнаружено!")
        else:
            print("Все слушатели готовы!")
    else:
        print("Директории слушателей не обнаружено, она будет создана!")
        os.mkdir(directory)


def load_commands(bot):
    print("Подготовка внешних команд:")
    directory = "commands"
    if os.path.isdir(directory):
        flag = True
        for file in filter(lambda obj: os.path.isfile("{}/{}".format(directory, obj)) and obj.endswith(".py"),
                           os.listdir(directory)):
            module_name = file[:-3]
            print(module_name, end="")
            sleep_log(1.5, end="")
            for command in importlib.import_module("{}.{}".format(directory, module_name)).get_commands():
                bot.add_command(command)
            print(" готов!")
            flag = False
        if flag:
            print("Команд не обнаружено!")
        else:
            print("Все команды готовы!")
    else:
        print("Директории команд не обнаружены, она будет создана!")
        os.mkdir(directory)


def try_remove_prefix(text, bot):
    mentioned = re.sub(r'^((\[(\S+?)\|\S+?\])|(@(\S+)( \(\S+?\))?))', r'\3\5', text, re.IGNORECASE + re.DOTALL)
    if len(mentioned) != len(text):
        domain = mentioned.split()[0].lower()
        if domain == "id{}".format(bot.get_id()) or domain == bot.get_domain():
            return " ".join(mentioned.split()[1:])
        else:
            return text
    elif text.lower().startswith(bot.get_prefix()):
        return text[len(bot.get_prefix()):].strip()
    else:
        return text


def check_connection(url):
    # noinspection PyBroadException
    try:
        urlopen(url, timeout=5)
        return True
    except Exception:
        return False


def sleep_log(sleep_time, step_time=0.5, sleep_char=".", end="\n"):
    for i in range(int(sleep_time / step_time)):
        print(sleep_char, end="")
        time.sleep(step_time)
    print("", end=end)
