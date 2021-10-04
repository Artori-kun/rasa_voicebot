from typing import List, Dict, Text, Any

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

import datetime
from datetime import time


class ActionFaqCurrentTime(Action):
    def name(self) -> Text:
        return 'action_faq_current_time'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_time = datetime.datetime.now().time()

        dispatcher.utter_message(f"Bây giờ là {current_time.hour} giờ {current_time.minute} phút")

        return []


class ActionFaqCurrentDate(Action):
    def name(self) -> Text:
        return 'action_faq_current_date'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_date = datetime.datetime.now()

        dispatcher.utter_message(
            f"Hôm nay là ngày {current_date.day} tháng {current_date.month} năm {current_date.year}")

        return []


class ActionFaqCurrentWeekday(Action):
    def name(self) -> Text:
        return 'action_faq_current_weekday'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        weekdays = {0: "thứ hai",
                    1: "thứ ba",
                    2: "thứ tư",
                    3: "thứ năm",
                    4: "thứ sáu",
                    5: "thứ bảy",
                    6: "chủ nhật"}

        current_date = weekdays[datetime.datetime.today().weekday()]

        dispatcher.utter_message(f"Hôm nay là {current_date}")

        return []
