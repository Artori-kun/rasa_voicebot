from typing import List, Dict, Text, Any

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from custom_news_modules.news_extractor import NewsExtractor


class ActionRetrieveNewsHeadlines(Action):
    def name(self) -> Text:
        return "action_retrieve_news_headlines"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        intent = tracker.latest_message['intent'].get('name')
        e = NewsExtractor()
        category = ''

        if intent == "request_covid_news":
            headlines = e.get_covid_headline()
        else:
            entities = tracker.latest_message['entities']
            category_provided = False
            for entity in entities:
                if entity['entity'] == 'category':
                    category_provided = True
                    category = entity['value']
                    break
            if category_provided:
                headlines = e.get_headline(category)
            else:
                headlines = e.get_latest_headline()

        return [SlotSet("news_headlines", headlines)]


class ActionReadNewsHeadlines(Action):
    def name(self) -> Text:
        return 'action_read_news_headlines'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        headlines_slot = tracker.get_slot('news_headlines')
        current_headlines = tracker.get_slot('news_headlines_current')
        # print(headlines_slot.keys())

        if headlines_slot is None:
            dispatcher.utter_message("không tìm thấy tin tức liên quan đến chủ đề bạn cần")
        else:
            try:
                if current_headlines is not None:
                    for h in current_headlines:
                        headlines_slot.pop(h)

                current_headlines = list(headlines_slot.keys())[:3]

                news_order = ["tin thứ nhất: ",
                              "tin thứ hai: ",
                              "tin thứ ba: "]

                dispatcher.utter_message("đây là những tin bạn yêu cầu")

                for i in range(3):
                    dispatcher.utter_message(news_order[i] + current_headlines[i])

                dispatcher.utter_message("bạn muốn nghe tin nào")

            except IndexError or KeyError:
                dispatcher.utter_message(f"Đã hết tin")

        return [SlotSet("news_headlines", headlines_slot),
                SlotSet("news_headlines_current", current_headlines)]


class ActionNewsResetSlots(Action):

    def name(self) -> Text:
        return 'action_news_reset_slots'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        return [SlotSet("news_headlines", None),
                SlotSet("news_headlines_current", None)]


class ActionRetrieveNewsContent(Action):

    def name(self) -> Text:
        return 'action_retrieve_news_content'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> None:
        entities = tracker.latest_message['entities']
        headlines_slot = tracker.get_slot('news_headlines')
        current_headlines = tracker.get_slot('news_headlines_current')
        entity_provided = False

        e = NewsExtractor()

        for entity in entities:
            if entity['entity'] == "news_order_st":
                entity_provided = True
                content = e.get_article(headlines_slot[current_headlines[0]])
                dispatcher.utter_message(content)
            elif entity['entity'] == "news_order_nd":
                entity_provided = True
                content = e.get_article(headlines_slot[current_headlines[1]])
                dispatcher.utter_message(content)
            elif entity['entity'] == "news_order_rd":
                entity_provided = True
                content = e.get_article(headlines_slot[current_headlines[2]])
                dispatcher.utter_message(content)

        if entity_provided is False:
            dispatcher.utter_message("bạn chưa chọn tin nào")

        return None


class ActionRetrieveCovidNumber(Action):
    def name(self) -> Text:
        return 'action_retrieve_covid_numbers'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> None:
        entities = tracker.latest_message['entities']
        entity_provided = False

        e = NewsExtractor()

        for entity in entities:
            print(entity)
            if entity['entity'] == 'domestic':
                entity_provided = True
                data = e.get_general_covid_info_vn()

                dispatcher.utter_message(f"Tình hình dịch bệnh trong nước:\n"
                                         f"Số ca nhiễm: {data['cases']}\n"
                                         f"Số ca mới: {data['new-cases']}\n"
                                         f"Đã khỏi: {data['cured']}\n"
                                         f"Tử vong: {data['death']}")
            elif entity['entity'] == 'foreign':
                entity_provided = True
                data = e.get_general_covid_info_world()

                dispatcher.utter_message(f"Tình hình dịch bệnh thế giới:\n"
                                         f"Số ca nhiễm: {data['cases']}\n"
                                         f"Đã khỏi: {data['cured']}\n"
                                         f"Tử vong: {data['death']}")
            elif entity['entity'] == 'province':
                entity_provided = True
                province = entity['value']
                data = e.get_province_covid_info(province)

                print(province)
                print(data)
                dispatcher.utter_message(f"Tình hình dịch bệnh tại {province}:\n"
                                         f"Số ca nhiễm: {data['cases']}\n"
                                         f"Số ca mới: {data['new-cases']}\n")

        if not entity_provided:
            data_vn = e.get_general_covid_info_vn()
            data_world = e.get_general_covid_info_world()

            dispatcher.utter_message(f"Tình hình dịch bệnh trong nước:\n"
                                     f"Số ca nhiễm: {data_vn['cases']}\n"
                                     f"Số ca mới: {data_vn['new-cases']}\n"
                                     f"Đã khỏi: {data_vn['cured']}\n"
                                     f"Tử vong: {data_vn['death']}")

            dispatcher.utter_message(f"Tình hình dịch bệnh thế giới:\n"
                                     f"Số ca nhiễm: {data_world['cases']}\n"
                                     f"Đã khỏi: {data_world['cured']}\n"
                                     f"Tử vong: {data_world['death']}")

        return None


class ActionRetrieveCovidTimeline(Action):

    def name(self) -> Text:
        return 'action_retrieve_covid_timeline'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> None:
        e = NewsExtractor()

        data = e.get_covid_timeline()

        dispatcher.utter_message(f"Diễn biến dịch bệnh {data['timestamp']}:\n"
                                 f"{data['timeline']}")

        return None
