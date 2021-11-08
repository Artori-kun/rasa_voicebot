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


class ActionFaqIntroduce(Action):
    def name(self) -> Text:
        return 'action_faq_introduce'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        dispatcher.utter_message("Xin chào. Tên tôi là Bạc Xỉu. Hãy cứ gọi tôi là Xỉu cho gọn. Nếu bạn thắc mắc thì "
                                 "tên tôi được đặt theo tên con mèo của người tạo ra tôi.")
        dispatcher.utter_message("Tôi là một trợ lý ảo được "
                                 "xây dựng trên nền tảng Rasa. Tôi có nhiệm vụ hỗ trợ bạn trong việc quản lý lịch cá "
                                 "nhân của mình và cung cấp cho bạn những tin tức nóng hổi và mới nhất để bạn không "
                                 "trở thành người tối cổ. Yêu cầu của bạn là mệnh lệnh của tôi, trừ khi tôi không "
                                 "hiểu bạn đang muốn cái gì.")
        dispatcher.utter_message("Hôm nay tôi tới đây với một sứ mệnh cao cả. Đó là giúp Hiếu và Hà bảo vệ thành công "
                                 "đồ án tốt nghiệp và đạt điểm cao. "
                                 "Hiếu thức trắng mấy đêm rồi nên các thầy đừng ngần ngại cho 9 điểm nhé. Xin cảm "
                                 "ơn!!")
        return []
