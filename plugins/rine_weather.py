import requests

import vkrine
import vkrine.exceptions
from vkrine.commands import Command
from vkrine.modules import BotModule

API_URL = 'https://api.openweathermap.org/data/2.5/'
METHOD_WEATHER = "weather"

WEATHER_UNICODE = {
    "Thunderstorm": "&#127785;",
    "Drizzle": "&#127783;",
    "Rain": "&#127782;",
    511: "&#10052;",  # freezing rain
    520: "&#127783;",  # light intensity shower rain
    521: "&#127783;",  # shower rain
    522: "&#127783;",  # heavy intensity shower rain
    531: "&#127783;",  # ragged shower rain
    "Snow": "&#10052;",
    701: "&#127787;",  # mist
    711: "&#127787;",  # smoke
    721: "&#127787;",  # haze
    731: "&#127787;",  # sand/ dust whirls
    741: "&#127787;",  # fog
    751: "&#127787;",  # sand
    761: "&#127787;",  # dust
    762: "&#127787;",  # volcanic ash
    771: "&#127787;",  # squalls
    "Tornado": "&#127786;",
    "Clear": "&#9728;",
    801: "&#127780;",  # few clouds: 11-25%
    802: "&#9925;",  # scattered clouds: 25-50%
    803: "&#127781;",  # broken clouds: 51-84%
    804: "&#9729;"  # overcast clouds: 85-100%
}


def __parse_icon__(weather):
    w_id = weather["weather"][0]["id"]
    w_main = weather["weather"][0]["main"]
    if w_id in WEATHER_UNICODE:
        return WEATHER_UNICODE[w_id]
    if w_main in WEATHER_UNICODE:
        return WEATHER_UNICODE[w_main]
    return "&#10067;"


class WeatherCommand(Command):
    def __init__(self, module):
        super().__init__(module, "weather")
        self.__token__ = vkrine.bot.SETTINGS.get_option("modules.weather.api_token")

    def run(self, event, bot, line, args):
        if self.__token__:
            if line:
                lang_state = bot.L10N.get_locale_key(event).split("_")[0]
                data = {
                    "q": line,
                    "appid": self.__token__,
                    "units": "metric",
                    "lang": lang_state
                }
                response = requests.get(API_URL + METHOD_WEATHER, params=data)
                if response.status_code == 200:
                    weather = response.json()
                    header = {
                        "icon": __parse_icon__(weather),
                        "desc": weather["weather"][0]["description"],
                        "city": weather["name"]
                    }
                    body = {
                        "temp": weather["main"]["temp"],
                        "min": weather["main"]["temp_min"],
                        "max": weather["main"]["temp_max"],
                        "feels": weather["main"]["feels_like"],
                        "humidity": weather["main"]["humidity"],
                        "clouds": weather["clouds"]["all"],
                        "speed": weather["wind"]["speed"]
                    }
                    vkrine.MessageBuilder().translated_text("commands.text.weather.header", **header).newline(2) \
                        .translated_text("commands.text.weather.body", **body).newline(2) \
                        .translated_text("commands.text.weather.footer", "OpenWeather").send(event)
                else:
                    vkrine.MessageBuilder().translated_text("commands.text.weather.response.bad",
                                                            response.status_code).send(event)
            else:
                raise vkrine.exceptions.CommandWrongUsageException(None)
        else:
            vkrine.MessageBuilder().translated_text("commands.text.weather.bad_token").send(event)


class WeatherModule(BotModule):
    def __init__(self, bot):
        super().__init__("weather", bot)

    def commands(self):
        return [WeatherCommand(self)]
