import json
import os
import pickle
import re
import requests
import time
from re import RegexFlag

from vk_api import VkApi, Captcha
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload

# Sticker cache database file
file_stickers = "stickers.pkl"
# Stickers folder
folder = "stickers"
# VK token
token = ""

# Load configuration
if os.path.exists("config.json"):
    with open("config.json", "r") as f:
        config = json.load(f)
    try:
        file_stickers = config["database"]
    except KeyError:
        pass
    try:
        folder = config["path"]
    except KeyError:
        pass
    try:
        token = config["token"]
    except KeyError:
        print("Token not found")
        quit()
else:
    with open("config.json", "w") as f:
        f.write('{"token": "enter token"}')
    print("Enter token to config.json")
    quit()


# Sends captcha to current chat and wait /captcha command
def captcha_handler(c: Captcha):
    with open("captcha.jpg", "wb") as handle:
        response = requests.get(c.url, stream=True)
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
    print("Captcha required, see captcha.jpg")
    vk.messages.send(peer_id=event.peer_id, message="Captcha required!\n{}".format(str(c.url)),
                     random_id=int(time.time()), attachment=upload_photo("captcha.jpg"))
    global current_captcha
    current_captcha = c


# Init sticker database
try:
    with open(file_stickers, "rb") as f:
        stickers = pickle.load(f)
except EOFError:
    with open(file_stickers, "wb") as f:
        pickle.dump({}, f)
    with open(file_stickers, "rb") as f:
        stickers = pickle.load(f)


# Required for captcha sender
def upload_photo(path):
    r = uploadSession.photo_messages(path)[0]
    return "photo{}_{}".format(r["owner_id"], r["id"])


def upload_graffiti(path):
    r = uploadSession.graffiti(folder + "/" + path.replace(".", "/") + ".png", peer_id=event.peer_id)["graffiti"]
    return "doc{}_{}".format(r["owner_id"], r["id"])


# Add and write sticker to database file
def add_sticker_to_base(new_sticker):
    stickers.update(new_sticker)
    with open(file_stickers, "wb") as file:
        pickle.dump(stickers, file)


# List if sticker file names
def list_stickers(cat):
    r, c, s, p = "", "", "", folder + "/"
    if cat:
        p = p + cat + "/"
    if os.path.exists(p):
        for file in os.listdir(p):
            if file.endswith(".png"):
                if s:
                    s = "{}, {}".format(s, os.path.join(p, file)[len(p):-4])
                else:
                    s = os.path.join(p, file)[len(p):-4]
            elif os.path.isdir(os.path.join(p, file)):
                if c:
                    c = "{}, {}".format(c, os.path.join(p, file)[len(p):])
                else:
                    c = os.path.join(p, file)[len(p):]
        if c:
            r = "Categories:\n{}\n".format(c)
        if s:
            r = r + "Stickers:\n" + s
        if r:
            r = r.replace("\\", ".").replace("/", ".")
        else:
            r = "Category is empty"
    else:
        r = "Category '{}' not found".format(cat)
    return r


if token:
    session = VkApi(token=token, captcha_handler=captcha_handler)
    uploadSession = VkUpload(session)
    vk = session.get_api()
    longPoll = VkLongPoll(session)
    for event in longPoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

                if re.match("^/captcha \w+$", event.text, RegexFlag.I):
                    print("Trying to answer captcha with " + event.text[9:])
                    current_captcha.try_again(event.text[9:])
                elif re.match("^/stickers( \w+)?$", event.text, RegexFlag.I):
                    category = event.text[9:]
                    if category.startswith(" "):
                        category = category[1:]
                    vk.messages.send(peer_id=event.peer_id, message=list_stickers(category), random_id=int(time.time()))
                elif "../" not in event.text:
                    for el in event.text.split():
                        if re.match("^:(\w|\.)+:$", el):
                            try:
                                sticker = stickers[el[1:-1]]
                            except KeyError:
                                sticker = upload_graffiti(el[1:-1])
                                add_sticker_to_base({el[1:-1]: sticker})
                            vk.messages.send(peer_id=event.peer_id, attachment=sticker, random_id=int(time.time()))
                            break

else:
    print("Token not found")
    quit()
