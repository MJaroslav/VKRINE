from vkrine import utils, rinebot


if __name__ == "__main__":
    utils.print_logo()
    token = utils.load_token()
    if token:
        rinebot.RINEBot(token).run()
else:
    print("Это главный модуль VKRINE, он может быть только запущен.")
