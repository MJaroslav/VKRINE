print("===================================================")
print("=            _____  _____ _   _ ______            =")
print("=           |  __ \|_   _| \ | |  ____|           =")
print("=           | |__) | | | |  \| | |__              =")
print("=           |  _  /  | | | . ` |  __|             =")
print("=           | | \ \ _| |_| |\  | |____            =")
print("=           |_|  \_\_____|_| \_|______|           =")
print("=                   By MJaroslav                  =")
print("=                                                 =")
print("===================================================")

import json
import os
import pickle
import requests
import time

from vk_api import VkApi, Captcha
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload

# Файл данных авторизации: ключ доступа VK.
file_auth = "auth.json"
# Файл настроек бота.
file_config = "config.json"
# Файл для последней капчи.
file_captcha = "captcha.jpg"

# Ключ доступа VK.
token = ""

# Файл датабазы стикеров.
file_stickers = "stickers.pkl"
# Папка стикеров.
folder = "stickers"
# Маркер ключа стикера. Формат: '%MARKER%%KEY%%MARKER%'.
marker_sticker = ":"
# Маркер команды бота. Формат: '%MARKER%%COMMAND%'.
marker_command = "/"
# Список администраторов.
admins = []
# Список модераторов. Не могут назначать администраторов.
moders = []
# Чёрный список. Работают только команды администрации.
blacklist = []
# Символы, которые будут заменены в ключе стикера.
rep_chars = {"ё": "е"}

# Комманда помощи бота.
command_help = "help"
# Комманда вывода списка стикеров и категорий.
command_stickers = "stickers"
text_command_stickers = "вывести список стикеров и категорий (КАТЕГОРИЯ либо основная)"
# Комманда сброса датабазы стикеров.
command_reset = "reset"
text_command_reset = "сбросить датабазу стикеров"
# Команда обновления стикера в датабазе.
command_update = "update"
text_command_update = "обновить стикер в датабазе (STICKER)"
# Команда чисти датабазы от несуществующих стикеров.
command_clean = "clean"
text_command_clean = "очистить удалённые стикеры из датабазы"
# Команда добавления нового модератора.
command_moder_add = "moderadd"
text_command_moder_add = "добавить модератора (ID)"
# Команда удаления модератора.
command_moder_remove = "moderremove"
text_command_moder_remove = "удалить модератора (ID)"
# Команда добавления в чёрный список.
command_blacklist_add = "bladd"
text_command_blacklist_add = "добавить в чёрный список (ID либо текущий)"
# Команда удаления из чёрного списка.
command_blacklist_remove = "blremove"
text_command_blacklist_remove = "удалить из чёрного списка (ID либо текущий)"
# Команда ответа на капчу.
command_captcha = "captcha"
text_command_captcha = "ввести капчу (КОД)"
# Команда добавления стикера
command_add_sticker = "addsticker"
text_command_add_sticker = "добавить стикер (ИМЯ КАТЕГОРИЯ либо основная)(приложить png документ)"
# Команда удаления стикера
command_remove_sticker = "removesticker" 
text_command_remove_sticker = "удалить стикер (ИМЯ КАТЕГОРИЯ либо основная)"

# Выводится, если команда command_stickers <category> не нашла категорию
text_none = "Категория '$name$' не найдена"
# Список категорий: $categories$ - перечисление категорий через запятую.
text_categories = "Категории:\n$categories$\n\n"
# Выводится, если список категорий пуст
text_zero_categories = "Категории не найдены"
# Список стикеров: $stickers$ - перечисление стикеров через запятую.
text_stickers = "Стикеры:\n$stickers$"
# Placeholder for text_stickers
text_zero_stickers = "Стикеры не найдены"
# Текст команды stickers: $categories$ = text_categories, $stickers$ = text_stickers
text_stickers_command = "$categories$$stickers$"
# Текст капчи: $url$ - ссылка на картинку капчи, $command$ - комманда-пример
text_captcha = "Введите код с картинки:\n$url$\n\nКомманда: $command$"
# Текст комманды command_help: $example$ - пример, $commands$ - список команд
text_help = "Использование стикеров:\n$example$\n\nСписок команд:\n\n$commands$"


def get_or_default(key, default, get_from):
    try:
        return get_from[key]
    except KeyError:
        return default


def save_config():
    with open(file_config, "w", encoding='utf-8') as f:
        f.write(json.dumps({"database": file_stickers, "sticker_path": folder, "marker_sticker": marker_sticker,
                            "text_none": text_none, "text_stickers": text_stickers, "text_categories": text_categories,
                            "text_zero_categories": text_zero_categories, "text_zero_stickers": text_zero_stickers,
                            "text_stickers_command": text_stickers_command, "text_captcha": text_captcha,
                            "command_blacklist_add": command_blacklist_add, "command_captcha": command_captcha,
                            "command_blacklist_remove": command_blacklist_remove,
                            "command_clean": command_clean, "command_help": command_help, "command_reset": command_reset,
                            "command_moder_add": command_moder_add, "command_moder_remove": command_moder_remove,
                            "command_stickers": command_stickers, "command_update": command_update, "admins": admins,
                            "moders": moders, "rep_chars": rep_chars, "marker_command": marker_command,
                            "text_command_blacklist_add": text_command_blacklist_add,
                            "text_command_captcha": text_command_captcha,
                            "text_command_blacklist_remove": text_command_blacklist_remove,
                            "text_command_clean": text_command_clean, "text_command_reset": text_command_reset,
                            "text_command_moder_add": text_command_moder_add,
                            "text_command_moder_remove": text_command_moder_remove,
                            "text_command_stickers": text_command_stickers, "text_command_update": text_command_update},
                           sort_keys=True, indent=4))
    print("Конфигурация сохранена")
                           
                           
# Загрузка данных авторизации
print("Загрузка авторизации...")
try:
    with open(file_auth, "r") as f:
        auth = json.load(f)
    token = get_or_default("token", "", auth)
    if not token:
        print("Ключ доступа не найден!")
        quit()
except FileNotFoundError:
    with open(file_auth, "w") as f:
        f.write('{\n  "token": "ВВЕДИТЕ КЛЮЧ ДОСТУПА (НЕ ГРУППЫ) СЮДА (ТРЕБУЕТСЯ messages ПРАВО)"\n}')
    print("Введите ключ доступа в {}".format(file_auth))
    quit()


# Загрузка конфигурации
print("Загрузка конфигурации...")
if os.path.exists(file_config):
    with open(file_config, "r", encoding='utf-8') as f:
        config = json.load(f)
    file_stickers = get_or_default("database", file_stickers, config)
    folder = get_or_default("sticker_path", folder, config)
    marker_sticker = get_or_default("marker_sticker", marker_sticker, config)
    marker_command = get_or_default("marker_command", marker_command, config)
    admins = get_or_default("admins", admins, config)
    moders = get_or_default("moders", moders, config)
    blacklist = get_or_default("blacklist", blacklist, config)
    rep_chars = get_or_default("rep_chars", rep_chars, config)
    command_blacklist_add = get_or_default("command_blacklist_add", command_blacklist_add, config)
    command_blacklist_remove = get_or_default("command_blacklist_remove", command_blacklist_remove, config)
    command_moder_add = get_or_default("command_moder_add", command_moder_add, config)
    command_moder_remove = get_or_default("command_moder_remove", command_moder_remove, config)
    command_clean = get_or_default("command_clean", command_clean, config)
    command_help = get_or_default("command_help", command_help, config)
    command_stickers = get_or_default("command_stickers", command_stickers, config)
    command_update = get_or_default("command_update", command_update, config)
    command_reset = get_or_default("command_reset", command_reset, config)
    command_captcha = get_or_default("command_captcha", command_captcha, config)
    text_command_blacklist_add = get_or_default("text_command_blacklist_add", text_command_blacklist_add, config)
    text_command_blacklist_remove = get_or_default("text_command_blacklist_remove", text_command_blacklist_remove, config)
    text_command_moder_add = get_or_default("text_command_moder_add", text_command_moder_add, config)
    text_command_moder_remove = get_or_default("text_command_moder_remove", text_command_moder_remove, config)
    text_command_clean = get_or_default("text_command_clean", text_command_clean, config)
    text_command_stickers = get_or_default("text_command_stickers", text_command_stickers, config)
    text_command_update = get_or_default("text_command_update", text_command_update, config)
    text_command_reset = get_or_default("text_command_reset", text_command_reset, config)
    text_command_captcha = get_or_default("text_command_captcha", text_command_captcha, config)
    text_none = get_or_default("text_none", text_none, config)
    text_captcha = get_or_default("text_captcha", text_captcha, config)
    text_stickers = get_or_default("text_stickers", text_stickers, config)
    text_categories = get_or_default("text_categories", text_categories, config)
    text_zero_stickers = get_or_default("text_zero_stickers", text_zero_stickers, config)
    text_zero_categories = get_or_default("text_zero_categories", text_zero_categories, config)
    text_stickers_command = get_or_default("text_stickers_command", text_stickers_command, config)
save_config()
marker_sticker_len = len(marker_sticker)
marker_command_len = len(marker_command)


# Отправляет капчу в последний чат
def captcha_handler(c: Captcha):
    with open(file_captcha, "wb") as handle:
        response = requests.get(c.url, stream=True)
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
    print("Требуется капча, смотрите captcha.jpg")
    reply(text=text_captcha.replace("$url$", c.url).replace("$command$", marker_command + command_captcha + " КЛЮЧ"),
          attachments=upload_photo(file_captcha))
    global current_captcha
    current_captcha = c


# Загрузка датабазы стикеров
try:
    with open(file_stickers, "rb") as f:
        stickers = pickle.load(f)
except (EOFError, FileNotFoundError, PermissionError):
    with open(file_stickers, "wb") as f:
        pickle.dump({}, f)
    with open(file_stickers, "rb") as f:
        stickers = pickle.load(f)


# Требуется для капчи
def upload_photo(path):
    r = uploadSession.photo_messages(path)[0]
    return "photo{}_{}".format(r["owner_id"], r["id"])


def upload_graffiti(path):
    print("Загрузка стикера {}".format(path))
    r = uploadSession.graffiti(folder + "/" + path.replace(".", "/") + ".png", peer_id=from_id)["graffiti"]
    return "doc{}_{}".format(r["owner_id"], r["id"])


# Добавить и записать стикер в датабазу
def add_sticker_to_base(new_sticker):
    stickers.update(new_sticker)
    with open(file_stickers, "wb") as file:
        pickle.dump(stickers, file)


# Вывод команды command_stickers
def list_stickers(category_name=""):
    path = "{}/{}/".format(folder, category_name).replace("//", "/")
    if os.path.exists(path):
        files, dirs = [], []
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                files.append(os.path.splitext(file)[0])
            else:
                dirs.append(os.path.splitext(file)[0])
        r = text_stickers_command
        if dirs:
            r = r.replace("$categories$", text_categories.replace("$categories$", ", ".join(dirs)))
        else:
            r = r.replace("$categories$", text_zero_categories)
        if files:
            r = r.replace("$stickers$", text_stickers.replace("$stickers$", ", ".join(files)))
        else:
            r = r.replace("$stickers$", text_zero_stickers)
    else:
        r = text_none.replace("$name$", category_name)
    return r


# Отправить сообщение в последний чат
def reply(text=None, attachments=None):
    if text or attachments:
        vk.messages.send(peer_id=from_id, random_id=int(time.time() * 1000), message=text, attachment=attachments)


# Получить ID стикера или пустую строку
def get_sticker(key):
    try:
        return stickers[key]
    except KeyError:
        try:
            r = upload_graffiti(key)
            add_sticker_to_base({key: r})
            return r
        except (FileNotFoundError, KeyError):
            return ""


print("Авторизация...")
session = VkApi(token=token, captcha_handler=captcha_handler)
uploadSession = VkUpload(session)
vk = session.get_api()
longPoll = VkLongPoll(session)
print("Авторизирован!")
for event in longPoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        from_id = event.peer_id
        if event.text.startswith(marker_command):
            command = event.text[marker_command_len:].split()
            if command[0] == command_captcha:
                if len(command) > 1:
                    print("Попытка ответить на капчу с ответом " + command[1])
                    try:
                        current_captcha.try_again(command[1])
                    except (NameError, Captcha):
                        pass
            elif command[0] == command_stickers:
                try:
                    category = command[1]
                except IndexError:
                    category = ""
                reply(text=list_stickers(category))
            elif command[0] == command_help:
                commands = marker_command + " - префикс команд" + "\n"\
                            + command_stickers + " - " + text_command_stickers + "\n"\
                            + command_reset + " - " + text_command_reset + "\n"\
                            + command_update + " - " + text_command_update + "\n"\
                            + command_clean + " - " + text_command_clean + "\n"\
                            + command_moder_add + " - " + text_command_moder_add + "\n"\
                            + command_moder_remove + " - " + text_command_moder_remove + "\n"\
                            + command_blacklist_add + " - " + text_command_blacklist_add + "\n"\
                            + command_blacklist_remove + " - " + text_command_blacklist_remove + "\n"\
                            + command_captcha + " - " + text_command_captcha + "\n"\
                            + command_add_sticker + " - " + text_command_add_sticker + "\n"\
                            + command_remove_sticker + " - " + text_command_remove_sticker\
                            + "\n\nWIP, работают только команды help и stickers"
                example = marker_sticker + "category_name.sticker_name" + marker_sticker + " " + marker_sticker\
                           + "sticker_name" + marker_sticker
                reply(text=text_help.replace("$commands$", commands).replace("$example$", example))
        else:
            words = event.text.lower();
            for key, value in rep_chars.items():
                words = words.replace(key, value)
            for word in words.split():
                if word.startswith(marker_sticker) and word.endswith(marker_sticker) and len(word) > (marker_sticker_len * 2):
                    try:
                        sticker = get_sticker(word[marker_sticker_len:-marker_sticker_len])
                        if sticker:
                            reply(attachments=sticker)
                            break
                    except Captcha as cp:
                        captcha_handler(cp)
