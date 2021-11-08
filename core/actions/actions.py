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
import requests
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet

from scipy.io import wavfile

SPEAKER_VERIFICATION_URL = 'http://192.168.14.22:7000/api/tutorials/login2'


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

class ActionVerifySpeaker(Action):

    def name(self) -> Text:
        return 'action_verify_speaker'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: DomainDict) -> List[Dict[Text, Any]]:
        latest_intent = tracker.get_intent_of_latest_message()
        print(latest_intent)
        sender_id = tracker.sender_id

        wav = open(f"custom_components/wavs/input_{sender_id}.wav", "rb")

        files = {"wav": wav}

        response = requests.post(SPEAKER_VERIFICATION_URL, files=files)

        # response = response.json()

        if response.status_code >= 300 or response.status_code <= 100:
            dispatcher.utter_message(f"Đã có lỗi xảy ra. Mã lỗi: sv_{response.status_code}")
            return [SlotSet('user_id', None),
                    SlotSet('user_firstname', None),
                    SlotSet('user_lastname', None),
                    SlotSet('is_verified', False)]

        if response.status_code == 204:
            return [SlotSet('user_id', None),
                    SlotSet('user_firstname', None),
                    SlotSet('user_lastname', None),
                    SlotSet('is_verified', False)]

        response = response.json()

        return [SlotSet('user_id', response['id']),
                SlotSet('user_firstname', response['firstname']),
                SlotSet('user_lastname', response['lastname']),
                SlotSet('is_verified', True)]


class ActionUnverifySpeaker(Action):

    def name(self) -> Text:
        return 'action_unverify_speaker'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        return [SlotSet('user_id', None),
                SlotSet('user_firstname', None),
                SlotSet('user_lastname', None),
                SlotSet('is_verified', False)]


class ActionGreetUser(Action):

    def name(self) -> Text:
        return 'action_greet_user'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        user_name = tracker.get_slot('user_firstname').split()[-1]

        dispatcher.utter_message(f"Xin chào {user_name}")

        return []


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
