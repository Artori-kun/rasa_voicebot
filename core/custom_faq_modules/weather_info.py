import requests
import json
import geocoder


class Weather:
    API_KEY = "36e7be63465ea02c9e797f29f19bfd8c"
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"

    def __init__(self):
        self.cur_city = geocoder.ip("me")[0].city

    def get_weather_city(self, city):
        url = self.BASE_URL + "appid=" + self.API_KEY + "&q=" + city

        response = requests.get(url)

        weather_info = response.json()

        if weather_info["cod"] != "404":
            weather = weather_info["weather"][0]["main"]
            visibility = weather_info["visibility"]

            temp = weather_info["main"]["temp"] - 273
            feels_like = weather_info["main"]["feels_like"] - 273
            humidity = weather_info["main"]["humidity"]

            return weather, visibility, temp, feels_like, humidity
        else:
            return None
