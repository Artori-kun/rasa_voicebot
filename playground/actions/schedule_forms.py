import json
from datetime import datetime, date
import difflib
from typing import List, Text, Dict, Any, Optional

import requests
from custom_date_extractor import date_extractor
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

BASE_SCHEDULES_URL = "http://127.0.0.1:7000/schedules/"


# Show schedules
class ActionShowSchedule(Action):
    def name(self) -> Text:
        return "action_show_schedule"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        response = None
        schedules = []

        if len(times) == 0:
            if len(dates) == 0:
                dispatcher.utter_message("Xin lỗi, tôi không biết bạn cần thông tin của thời điểm nào")
                return []
            else:
                response = requests.get(BASE_SCHEDULES_URL + f"?date={dates[0]}")
        elif len(dates) == 0:
            today = date.today()
            today = today.strftime("%d-%m-%Y")
            response = requests.get(BASE_SCHEDULES_URL + f"?date={today}&time={times[0]}")
        else:
            response = requests.get(BASE_SCHEDULES_URL + f"?date={dates[0]}&time={times[0]}")

        status = response.status_code
        if status == 400:
            dispatcher.utter_message("Ối, yêu cầu của bạn không hợp lệ")
        elif status == 404:
            dispatcher.utter_message("Tôi không tìm thấy thông tin bạn yêu cầu")
        elif status == 503:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
        elif status == 200:
            schedules = response.json()

        if len(schedules) == 0:
            dispatcher.utter_message("Bạn không có lịch gì")
            return []
        else:
            for schedule in schedules:
                date_field = schedule['date_field']
                start_time = schedule['start_time']
                end_time = schedule['end_time']
                content = schedule['content']

                text = f"Ngày {date_field}\n" \
                       f"Từ {start_time} đến {end_time}\n" \
                       f"Nội dung: {content}\n"
                dispatcher.utter_message(text)

        return [SlotSet("current_schedule_list", schedules)]


# Validation for create schedule form
class ValidateScheduleCreateForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_create_schedule_form"

    def validate_date_field(self,
                            slot_value: Any,
                            dispatcher: CollectingDispatcher,
                            tracker: Tracker,
                            domain: DomainDict,
                            ) -> Dict[Text, Any]:
        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"date_field": None}
        else:
            return {"date_field": dates[0]}

    def validate_start_time(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"start_time": None}
        else:
            return {"start_time": times[0]}

    def validate_end_time(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"end_time": None}
        else:
            return {"end_time": times[0]}


# Create schedule
class ActionCreateScheduleSubmit(Action):
    def name(self) -> Text:
        return "action_create_schedule_submit"

    async def run(self,
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: DomainDict) -> List[SlotSet]:
        date_field = tracker.get_slot('date_field')

        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")

        start_time = tracker.get_slot('start_time')
        end_time = tracker.get_slot('end_time')
        content = tracker.get_slot('content')

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "start_time": start_time,
            "end_time": end_time,
            "content": content
        }

        payload = json.dumps(payload)

        # print(payload)

        response = requests.post("http://127.0.0.1:7000/schedules/", data=payload, headers=headers)

        status = response.status_code

        if status == 400:
            err = response.json()
            for e in err.keys():
                dispatcher.utter_message(err[e][0])

        elif status == 500:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
        elif status == 201:
            dispatcher.utter_message("Tạo lịch mới thành công")

        return [SlotSet('date_field', None),
                SlotSet('start_time', None),
                SlotSet('end_time', None),
                SlotSet('content', None)]


# Confirm info before submit create
class ActionConfirmCreateScheduleInfo(Action):

    def name(self) -> Text:
        return "action_confirm_create_schedule_info"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        date_field = tracker.get_slot('date_field')
        start_time = tracker.get_slot('start_time')
        end_time = tracker.get_slot('end_time')
        content = tracker.get_slot('content')

        dispatcher.utter_message("Đây là lịch bạn vửa lập:")
        dispatcher.utter_message(f"Ngày: {date_field}\n"
                                 f"Thời gian bắt đầu: {start_time}\n"
                                 f"Thời gian kết thúc: {end_time}\n"
                                 f"Nội dung: {content}")
        dispatcher.utter_message("Bạn có chắc muốn thêm lịch này chứ?")
        return []


# Confirm info before delete
class ActionConfirmDeleteScheduleInfo(Action):
    def name(self) -> Text:
        return "action_confirm_delete_schedule_info"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        response = None
        schedules = []
        # print(dates)
        # print(times)

        if len(times) == 0:
            if len(dates) == 0:
                dispatcher.utter_message("Xin lỗi, tôi không biết bạn cần thông tin lịch vào thời điểm nào")
                return []
            else:
                response = requests.get(BASE_SCHEDULES_URL + f"?date={dates[0]}")
        elif len(dates) == 0:
            today = date.today()
            today = today.strftime("%d-%m-%Y")
            response = requests.get(BASE_SCHEDULES_URL + f"?date={today}&time={times[0]}")
        else:
            response = requests.get(BASE_SCHEDULES_URL + f"?date={dates[0]}&time={times[0]}")

        status = response.status_code
        if status == 400:
            dispatcher.utter_message("Ối, yêu cầu của bạn không hợp lệ")
        elif status == 404:
            dispatcher.utter_message("Tôi không tìm thấy lịch bạn yêu cầu")
        elif status == 503:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
        elif status == 200:
            schedules = response.json()

        if len(schedules) == 0:
            dispatcher.utter_message("Có vẻ như bạn không có kế hoạch gì để hủy")
            return []
        else:
            dispatcher.utter_message("Đây là các kế hoạch bạn muốn xóa:\n")
            for schedule in schedules:
                date_field = schedule['date_field']
                start_time = schedule['start_time']
                end_time = schedule['end_time']
                content = schedule['content']

                text = f"Ngày {date_field}\n" \
                       f"Từ {start_time} đến {end_time}\n" \
                       f"Nội dung: {content}\n"
                dispatcher.utter_message(text)

            if len(dates) != 0:
                if datetime.strptime(dates[0], "%d-%m-%Y") < datetime.today():
                    dispatcher.utter_message("Đây có vẻ như là lịch từ những ngày trước. Việc xóa chúng có thể làm mất "
                                             "một số thông tin bạn cần sau này")
            if len(times) != 0:
                if datetime.strptime(times[0], "%H:%M").time() < datetime.now().time():
                    dispatcher.utter_message("Kế hoạch mà bạn muốn xóa có vẻ đã hoặc đang diễn ra")

            dispatcher.utter_message("Bạn có thực sự muốn xóa lịch không?")

        return [SlotSet('delete_schedule_list', schedules)]


# Delete schedule
class ActionDeleteSchedule(Action):
    def name(self) -> Text:
        return "action_delete_schedule"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        schedules = tracker.get_slot('delete_schedule_list')
        fail_schedules = []

        if len(schedules) == 0 or schedules is None:
            return []

        for schedule in schedules:
            response = requests.delete(BASE_SCHEDULES_URL + str(schedule['id']))

            status = response.status_code

            if status in [400, 404, 503]:
                fail_schedules.append(schedule)

        if len(fail_schedules) != 0:
            dispatcher.utter_message("Ối, có vẻ đã xảy ra lỗi. Một hoặc một vài kế hoạch mà bạn muốn xóa hiện chưa "
                                     "thể xóa được. Hãy thử lại sau nhé")
        else:
            dispatcher.utter_message("Đã xóa thành công")
        return [SlotSet('delete_schedule_list', None)]


# Check edit info
class ActionCheckEditScheduleInfo(Action):
    def name(self) -> Text:
        return 'action_check_edit_schedule_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        SlotSet('edit_schedule', None)
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        response = None
        schedules = []

        if len(times) == 0:
            dispatcher.utter_message("Xin lỗi, bạn cần phải cung cấp đủ thông tin về thời gian và ngày tháng của lịch "
                                     "bạn muốn sửa")
            return [SlotSet("info_provided", False)]
        elif len(dates) == 0:
            today = date.today()
            today = today.strftime("%d-%m-%Y")
            response = requests.get(BASE_SCHEDULES_URL + f"?date={today}&time={times[0]}")
        else:
            response = requests.get(BASE_SCHEDULES_URL + f"?date={dates[0]}&time={times[0]}")

        status = response.status_code
        if status == 400:
            dispatcher.utter_message("Ối, yêu cầu của bạn không hợp lệ")
        elif status == 404:
            dispatcher.utter_message("Tôi không tìm thấy thông tin bạn yêu cầu")
        elif status == 503:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
        elif status == 200:
            schedules = response.json()

        if len(schedules) == 0:
            dispatcher.utter_message("Bạn không có lịch gì")
            return [SlotSet("info_provided", False)]
        else:
            dispatcher.utter_message("Đây có phải lịch bạn muốn sửa không?")

            schedule = schedules[0]

            date_field = schedule['date_field']
            start_time = schedule['start_time']
            end_time = schedule['end_time']
            content = schedule['content']

            text = f"Ngày {date_field}\n" \
                   f"Từ {start_time} đến {end_time}\n" \
                   f"Nội dung: {content}\n"
            dispatcher.utter_message(text)

        return [SlotSet("edit_schedule", schedule),
                SlotSet("info_provided", True)]


# Validation for edit schedule form
class ValidateEditScheduleForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_edit_schedule_form"

    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Optional[List[Text]]:
        if tracker.get_slot('selected_field_schedule') == 'date_field':
            return ['selected_field_schedule', 'date_field_edit']
        elif tracker.get_slot('selected_field_schedule') == 'start_time':
            return ['selected_field_schedule', 'start_time_edit']
        elif tracker.get_slot('selected_field_schedule') == 'end_time':
            return ['selected_field_schedule', 'end_time_edit']
        elif tracker.get_slot('selected_field_schedule') == 'content':
            return ['selected_field_schedule', 'content_edit']
        elif tracker.get_slot('selected_field_schedule') == 'all':
            return ['selected_field_schedule', 'date_field_edit', 'start_time_edit', 'end_time_edit', 'content_edit']
        else:
            return ['selected_field_schedule']

    def validate_selected_field_schedule(self,
                                         slot_value: Any,
                                         dispatcher: CollectingDispatcher,
                                         tracker: Tracker,
                                         domain: DomainDict) -> Dict[Text, Any]:
        selected_field_schedule = tracker.latest_message.get('text').lower()

        synonyms_all = ["tất cả"]
        synonyms_date_field = ["ngày", "ngày tháng"]
        synonyms_start_time = ["thời gian bắt đầu"]
        synonyms_end_time = ["thời gian kết thúc"]
        synonyms_content = ["nội dung"]

        synonyms = synonyms_all + synonyms_date_field + synonyms_start_time + synonyms_end_time + synonyms_content

        selected_field_schedule = difflib.get_close_matches(selected_field_schedule,
                                                            synonyms,
                                                            n=1)
        # print(selected_field_schedule)

        if len(selected_field_schedule) == 0:
            return {'selected_field_schedule': None}
        else:
            selected_field_schedule = selected_field_schedule[0]

        if selected_field_schedule in synonyms_all:
            return {'selected_field_schedule': 'all'}
        elif selected_field_schedule in synonyms_start_time:
            return {'selected_field_schedule': 'start_time'}
        elif selected_field_schedule in synonyms_end_time:
            return {'selected_field_schedule': 'end_time'}
        elif selected_field_schedule in synonyms_date_field:
            return {'selected_field_schedule': 'date_field'}
        elif selected_field_schedule in synonyms_content:
            return {'selected_field_schedule': 'content'}

    def validate_date_field_edit(self,
                                 slot_value: Any,
                                 dispatcher: CollectingDispatcher,
                                 tracker: Tracker,
                                 domain: DomainDict,
                                 ) -> Dict[Text, Any]:
        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"date_field_edit": None}
        else:
            return {"date_field_edit": dates[0]}

    def validate_start_time_edit(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"start_time_edit": None}
        else:
            return {"start_time_edit": times[0]}

    def validate_end_time_edit(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"end_time_edit": None}
        else:
            return {"end_time_edit": times[0]}


# Reset slots after schedule edit form
class ActionResetEditSlots(Action):

    def name(self) -> Text:
        return 'action_reset_edit_schedule_slots'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_schedule = tracker.slots.get('edit_schedule')

        if tracker.get_slot('date_field_edit') is not None:
            current_schedule['date_field'] = tracker.get_slot('date_field_edit')
        if tracker.get_slot('start_time_edit') is not None:
            current_schedule['start_time'] = tracker.get_slot('start_time_edit')
        if tracker.get_slot('end_time_edit') is not None:
            current_schedule['end_time'] = tracker.get_slot('end_time_edit')
        if tracker.get_slot('content_edit') is not None:
            current_schedule['content'] = tracker.get_slot('content_edit')

        if tracker.get_slot('change_made') is False:
            SlotSet('change_made', True)

        return [SlotSet("edit_schedule", current_schedule),
                SlotSet("selected_field_schedule", None),
                SlotSet("date_field_edit", None),
                SlotSet("start_time_edit", None),
                SlotSet("end_time_edit", None),
                SlotSet("content_edit", None)]


# Confirm edit info
class ActionConfirmEditInfo(Action):
    def name(self) -> Text:
        return 'action_confirm_edit_schedule_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edit_schedule = tracker.get_slot('edit_schedule')

        date_field = edit_schedule['date_field']
        start_time = edit_schedule['start_time']
        end_time = edit_schedule['end_time']
        content = edit_schedule['content']

        dispatcher.utter_message("Đây là các thông tin bạn vừa thay đổi:\n")
        dispatcher.utter_message(f"Ngày: {date_field}\n"
                                 f"Thời gian bắt đầu: {start_time}\n"
                                 f"Thời gian kết thúc: {end_time}\n"
                                 f"Nội dung: {content}")

        dispatcher.utter_message("Bạn có chắc muốn thay đổi không?")

        return [SlotSet('change_made', False)]


# Edit schedule
class ActionEditSchedule(Action):
    def name(self) -> Text:
        return 'action_edit_schedule'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edit_schedule = tracker.get_slot('edit_schedule')

        date_field = edit_schedule['date_field']
        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")
        
        start_time = edit_schedule['start_time']
        end_time = edit_schedule['end_time']
        content = edit_schedule['content']

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "start_time": start_time,
            "end_time": end_time,
            "content": content
        }

        payload = json.dumps(payload)

        response = requests.put(BASE_SCHEDULES_URL + f"{edit_schedule['id']}/", data=payload, headers=headers)

        status = response.status_code

        if status == 400:
            err = response.json()
            for e in err.keys():
                dispatcher.utter_message(err[e][0])

        elif status == 500:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
        elif status == 200 or status == 204:
            dispatcher.utter_message("Thay đổi lịch thành công")

        return []
