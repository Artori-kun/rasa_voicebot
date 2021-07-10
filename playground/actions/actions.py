# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


import json
# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List

from custom_faq_modules.weather_info import Weather
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []


class ActionWeatherHere(Action):

    def name(self) -> Text:
        return "action_weather_here"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # city = tracker.get_latest_entity_values("city")
        weather_info = Weather()
        weather, visibility, temp, feels_like, humidity = weather_info.get_weather_city(weather_info.cur_city)

        if weather_info is not None:
            response = f"Tình Hình thời tiết tại {weather_info.cur_city}:\n" \
                       + f"Thời tiết: {weather}\n" \
                       + f"Nhiệt độ: {temp}\n" \
                       + f"Cảm giác như: {feels_like}\n" \
                       + f"Độ ẩm: {humidity}\n" \
                       + f"Tầm nhìn xa: {visibility}"
            dispatcher.utter_message(response)
        else:
            dispatcher.utter_message("Không tìm thấy thành phố yêu cầu")
        return []


class ActionWeatherCity(Action):

    def name(self) -> Text:
        return "action_weather_city"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # print(tracker.latest_message['entities'])
        city_entities = []
        entities = tracker.latest_message['entities']
        for e in entities:
            if e['entity'] == "city":
                city_entities.append(e['value'])

        with open("custom_faq_modules/city_name.json", "r", encoding="utf8") as fr:
            city_name = json.load(fr)

        weather_info = Weather()

        # print(city_entities)

        response = ''

        for city in city_entities:
            if city in city_name.keys():
                _city = city_name[city]

                weather, visibility, temp, feels_like, humidity = weather_info.get_weather_city(_city)

                if weather_info is not None:
                    response += f"Tình Hình thời tiết tại {city}:\n" \
                                + f"Thời tiết: {weather}\n" \
                                + f"Nhiệt độ: {temp}\n" \
                                + f"Cảm giác như: {feels_like}\n" \
                                + f"Độ ẩm: {humidity}\n" \
                                + f"Tầm nhìn xa: {visibility}\n"

                else:
                    response += f"Không tìm thấy {city}\n"

        dispatcher.utter_message(response)
        return []
