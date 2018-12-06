import json
import os
import pickle
import requests
import time

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
        file_stickers = config["database"] + ".pkl"
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
    reply(text="Captcha required!\n" + c.url, attachments=upload_photo("captcha.jpg"))
    global current_captcha
    current_captcha = c


# Init sticker database
try:
    with open(file_stickers, "rb") as f:
        stickers = pickle.load(f)
except (EOFError, FileNotFoundError):
    with open(file_stickers, "wb") as f:
        pickle.dump({}, f)
    with open(file_stickers, "rb") as f:
        stickers = pickle.load(f)


# Required for captcha sender
def upload_photo(path):
    r = uploadSession.photo_messages(path)[0]
    return "photo{}_{}".format(r["owner_id"], r["id"])


def upload_graffiti(path):
    r = uploadSession.graffiti(folder + "/" + path.replace(".", "/") + ".png", peer_id=from_id)["graffiti"]
    return "doc{}_{}".format(r["owner_id"], r["id"])


# Add and write sticker to database file
def add_sticker_to_base(new_sticker):
    stickers.update(new_sticker)
    with open(file_stickers, "wb") as file:
        pickle.dump(stickers, file)


# List if sticker and categories file names
def list_stickers(category_name=""):
    r = ""
    files = []
    dirs = []
    path = "{}/{}/".format(folder, category_name).replace("//", "/")
    if os.path.exists(path):
        for file in os.listdir(path):
            if os.path.isfile(os.path.join(path, file)):
                files.append(os.path.splitext(file)[0])
            else:
                dirs.append(os.path.splitext(file)[0])
        if dirs:
            r = "Categories:\n{}\n".format(", ".join(dirs))
        if files:
            r += "Stickers:\n{}\n".format(", ".join(files))
        if r:
            r = r.replace("\\", ".").replace("/", ".")
        else:
            r += "Category is empty"
    else:
        r = "Category '{}' not found".format(category_name)
    return r


# Send message to last chat
def reply(text=None, attachments=None):
    if text or attachments:
        vk.messages.send(peer_id=from_id, random_id=int(time.time()*1000), message=text, attachment=attachments)


# Get sticker doc id or empty string
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


if token:
    session = VkApi(token=token, captcha_handler=captcha_handler)
    uploadSession = VkUpload(session)
    vk = session.get_api()
    longPoll = VkLongPoll(session)
    for event in longPoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            from_id = event.peer_id
            if event.text.startswith("/captcha "):
                print("Trying to answer captcha with " + event.text[9:])
                try:
                    current_captcha.try_again(event.text[9:])
                except (NameError, Captcha):
                    pass
            elif event.text.startswith("/stickers"):
                try:
                    category = event.text[10:]
                except IndexError:
                    category = ""
                reply(text=list_stickers(category))
            else:
                for word in event.text.split():
                    if word.startswith(":") and word.endswith(":") and len(word) > 2:
                        sticker = get_sticker(word[1:-1])
                        if sticker:
                            reply(attachments=sticker)
                            break
else:
    print("Token not found")
    exit()
