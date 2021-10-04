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
BASE_SCHEDULE_EXCEPTION_URL = "http://127.0.0.1:7000/schedule-exceptions/"


# GET SCHEDULES
# Show schedules
class ActionRetrieveSchedule(Action):
    def name(self) -> Text:
        return "action_retrieve_schedule"

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
                return [SlotSet('schedule_current'), None]
            else:
                date_param = dates[0]
                response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}")
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}&time={times[0]}")

        status = response.status_code
        if status == 400:
            dispatcher.utter_message("Ối, yêu cầu của bạn không hợp lệ. Vui lòng thử lại")
            return []
        elif status == 404:
            dispatcher.utter_message("Tôi không tìm thấy thông tin bạn yêu cầu")
            return []
        elif status == 503:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
            return []
        elif status < 200 or status >= 300:
            dispatcher.utter_message(f"Ối, đã xảy ra lỗi, bạn hãy thử lại sau nhé. Mã lỗi:{status}")
            return []
        elif status == 200:
            schedules = response.json()

        # date_param = datetime.strptime(date_param, "%d-%m-%Y")
        # date_param = date_param.strftime("%Y-%m-%d")

        if len(schedules) == 0:
            dispatcher.utter_message("Bạn không có lịch gì")
            return [SlotSet('schedule_current', None)]
        else:
            for schedule in schedules:
                schedule['date_field'] = date_param
                # date_field = schedule['date_field']
                start_time = schedule['start_time']
                end_time = schedule['end_time']
                content = schedule['content']
                location = schedule['location']

                text = f"Ngày {date_param}\n" \
                       f"Từ {start_time} đến {end_time}\n" \
                       f"Nội dung: {content}\n" \
                       f"Địa điểm: {location}"
                dispatcher.utter_message(text)

        return [SlotSet("schedule_current", schedules)]


class ActionCheckCurrentSchedule(Action):

    def name(self) -> Text:
        return 'action_check_current_schedule'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_schedule = tracker.get_slot('schedule_current')

        if len(current_schedule) == 1:
            return [SlotSet('schedule_current_num', 'one'),
                    SlotSet('schedule_edited_record', current_schedule[0]),
                    SlotSet('schedule_current', current_schedule[0])]
        elif len(current_schedule) > 1:
            return [SlotSet('schedule_current_num', 'many')]
        elif current_schedule is None:
            return [SlotSet('schedule_current_num', 'none')]


# CREATE SCHEDULE ACTIONS
# submit
class ActionCreateScheduleSubmit(Action):
    def name(self) -> Text:
        return "action_create_schedule_submit"

    async def run(self,
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: DomainDict) -> List[SlotSet]:
        date_field = tracker.get_slot('schedule_date_field')

        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")

        start_time = tracker.get_slot('schedule_start_time')
        end_time = tracker.get_slot('schedule_end_time')
        content = tracker.get_slot('schedule_content')
        location = tracker.get_slot('schedule_location')
        is_recurring = tracker.get_slot('schedule_is_recurring')
        recurrence_type = tracker.get_slot('schedule_recurrence_type')
        separation_count = tracker.get_slot('schedule_separation_count')

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "start_time": start_time,
            "end_time": end_time,
            "content": content,
            "location": location,
            "is_recurring": is_recurring,
            "recurring_type": recurrence_type,
            "separation_count": separation_count
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
        elif status < 200 or status >= 300:
            dispatcher.utter_message(f"Ối, đã xảy ra lỗi, bạn hãy thử lại sau nhé. Mã lỗi:{status}")
        elif status == 201:
            dispatcher.utter_message("Tạo lịch mới thành công")

        return []


# Confirm info before submit create
class ActionCreateScheduleConfirmInfo(Action):

    def name(self) -> Text:
        return "action_create_schedule_confirm_info"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        date_field = tracker.get_slot('schedule_date_field')
        start_time = tracker.get_slot('schedule_start_time')
        end_time = tracker.get_slot('schedule_end_time')
        content = tracker.get_slot('schedule_content')
        location = tracker.get_slot('schedule_location')
        is_recurring = tracker.get_slot('schedule_is_recurring')
        recurrence_type = tracker.get_slot('schedule_recurrence_type')
        separation_count = tracker.get_slot('schedule_separation_count')

        # print(recurrence_type)
        # print(separation_count)

        dispatcher.utter_message("Đây là lịch bạn vửa lập:")
        dispatcher.utter_message(f"Ngày: {date_field}\n"
                                 f"Thời gian bắt đầu: {start_time}\n"
                                 f"Thời gian kết thúc: {end_time}\n"
                                 f"Nội dung: {content}\n"
                                 f"Địa điểm: {location}\n")
        if is_recurring is True:
            if recurrence_type == 'daily':
                recurrence_type = 'ngày'
            elif recurrence_type == 'weekly':
                recurrence_type = 'tuần'
            elif recurrence_type == 'monthly':
                recurrence_type = 'tháng'
            elif recurrence_type == 'yearly':
                recurrence_type = 'năm'
            dispatcher.utter_message(f"Lặp lại: {separation_count} {recurrence_type} 1 lần\n")
        dispatcher.utter_message("Bạn có chắc muốn thêm lịch này chứ?")
        return []


class ActionCreateScheduleResetForm(Action):

    def name(self) -> Text:
        return 'action_create_schedule_reset_form'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        return [SlotSet('schedule_date_field', None),
                SlotSet('schedule_start_time', None),
                SlotSet('schedule_end_time', None),
                SlotSet('schedule_content', None),
                SlotSet('schedule_location', None),
                SlotSet('schedule_is_recurring', None),
                SlotSet('schedule_recurrence', None),
                SlotSet('schedule_recurrence_type', None),
                SlotSet('schedule_separation_count', None)]


# DELETE SCHEDULE ACTIONS
# Confirm info before delete
class ActionDeleteScheduleConfirmInfo(Action):
    def name(self) -> Text:
        return "action_delete_schedule_confirm_info"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        # date_param = None
        # time_param = None
        response = None
        schedules = []
        # print(dates)
        # print(times)

        if len(times) == 0:
            if len(dates) == 0:
                dispatcher.utter_message("Xin lỗi, tôi không biết bạn cần thông tin lịch vào thời điểm nào.")
                return [SlotSet("schedule_info_provided", False)]
            else:
                date_param = dates[0]
                response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}")
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}&time={times[0]}")

        status = response.status_code
        if status == 400:
            dispatcher.utter_message("Ối, yêu cầu của bạn không hợp lệ. Vui lòng thử lại")
            return []
        elif status == 404:
            dispatcher.utter_message("Tôi không tìm thấy thông tin bạn yêu cầu")
            return []
        elif status == 503:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
            return []
        elif status < 200 or status >= 300:
            dispatcher.utter_message(f"Ối, đã xảy ra lỗi, bạn hãy thử lại sau nhé. Mã lỗi:{status}")
            return []
        elif status == 200:
            schedules = response.json()

        if len(schedules) == 0:
            dispatcher.utter_message("Có vẻ như bạn không có kế hoạch gì để hủy")
            return [SlotSet("schedule_info_provided", False)]
        else:
            dispatcher.utter_message("Đây là các kế hoạch bạn muốn xóa:\n")
            for schedule in schedules:
                schedule['date_field'] = date_param
                date_field = schedule['date_field']
                start_time = schedule['start_time']
                end_time = schedule['end_time']
                content = schedule['content']
                location = schedule['location']

                text = f"Ngày {date_field}\n" \
                       f"Từ {start_time} đến {end_time}\n" \
                       f"Nội dung: {content}\n" \
                       f"Địa điểm: {location}\n"
                dispatcher.utter_message(text)

            if len(dates) != 0:
                if datetime.strptime(dates[0], "%d-%m-%Y") <= datetime.today():
                    dispatcher.utter_message("Đây có vẻ như là lịch từ những ngày trước hoặc đang diễn ra. Việc xóa "
                                             "chúng có thể làm mất "
                                             "một số thông tin bạn cần sau này")
            else:
                if len(times) != 0:
                    if datetime.strptime(times[0], "%H:%M").time() < datetime.now().time():
                        dispatcher.utter_message("Kế hoạch mà bạn muốn xóa có vẻ đã hoặc đang diễn ra")

            # dispatcher.utter_message("Bạn có thực sự muốn xóa lịch không?")

        return [SlotSet('schedule_current', schedules),
                SlotSet('schedule_info_provided', True)]


# Delete schedule
class ActionDeleteSchedule(Action):
    def name(self) -> Text:
        return "action_delete_schedule"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        schedules = tracker.get_slot('schedule_current')
        fail_schedules = []
        # recurrent_schedule = []

        if len(schedules) == 0 or schedules is None:
            dispatcher.utter_message("Không có gì để xóa")
            return []

        for schedule in schedules:
            if schedule['is_recurring'] is False:
                response = requests.delete(BASE_SCHEDULES_URL + str(schedule['id']) + "/")

                # status = response.status_code
                #
                # if status in [400, 404, 503]:
                #     fail_schedules.append(schedule)
            else:
                # SlotSet("schedule_has_recurrence", True)
                # recurrent_schedule.append(schedule)

                schedule['date_field'] = datetime.strptime(schedule['date_field'], "%d-%m-%Y")
                schedule['date_field'] = schedule['date_field'].strftime("%Y-%m-%d")

                headers = {
                    'Content-Type': 'application/json; charset=utf-8'
                }

                payload = {
                    "schedule_id": schedule["id"],
                    "date_field": schedule["date_field"]
                }

                payload = json.dumps(payload)

                response = requests.post(BASE_SCHEDULE_EXCEPTION_URL, data=payload, headers=headers)

            status = response.status_code

            if status < 200 or status >= 300:
                fail_schedules.append(schedule)

        # if len(recurrent_schedule) != 0:
        #     SlotSet("schedule_current_recurrence", recurrent_schedule)

        if len(fail_schedules) != 0:
            dispatcher.utter_message("Ối, có vẻ đã xảy ra lỗi. Một hoặc một vài kế hoạch mà bạn muốn xóa hiện chưa "
                                     "thể xóa được. Hãy thử lại sau nhé")
        else:
            dispatcher.utter_message("Đã xóa thành công")
        return [SlotSet('schedule_current', None)]


# EDIT SCHEDULE ACTIONS
# Reset form
class ActionEditScheduleResetForm(Action):
    def name(self) -> Text:
        return 'action_edit_schedule_reset_form'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        return [SlotSet("schedule_selected_field", None),
                SlotSet("schedule_date_field_edit", None),
                SlotSet("schedule_start_time_edit", None),
                SlotSet("schedule_end_time_edit", None),
                SlotSet("schedule_content_edit", None),
                SlotSet("schedule_location_edit", None),
                SlotSet("schedule_change_made", False)]


# Check edit info
class ActionEditScheduleConfirmInfo(Action):
    def name(self) -> Text:
        return 'action_edit_schedule_confirm_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        # SlotSet('schedule_edited_record', None)
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        response = None
        schedules = []

        if len(times) == 0:
            dispatcher.utter_message("Xin lỗi, bạn cần phải cung cấp đủ thông tin về thời gian và ngày tháng của lịch "
                                     "bạn muốn sửa.")
            return [SlotSet("schedule_info_provided", False)]
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_SCHEDULES_URL + f"?date={date_param}&time={times[0]}")

        status = response.status_code
        if status == 400:
            dispatcher.utter_message("Ối, yêu cầu của bạn không hợp lệ. Vui lòng thử lại")
            return []
        elif status == 404:
            dispatcher.utter_message("Tôi không tìm thấy thông tin bạn yêu cầu")
            return []
        elif status == 503:
            dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
            return []
        elif status < 200 or status >= 300:
            dispatcher.utter_message(f"Ối, đã xảy ra lỗi, bạn hãy thử lại sau nhé. Mã lỗi:{status}")
            return []
        elif status == 200:
            schedules = response.json()

        if len(schedules) == 0:
            dispatcher.utter_message("Bạn không có lịch gì")
            return [SlotSet("schedule_info_provided", False)]
        else:
            dispatcher.utter_message("Đây là lịch bạn yêu cầu:")

            schedule = schedules[0]
            schedule['date_field'] = date_param

            start_time = schedule['start_time']
            end_time = schedule['end_time']
            content = schedule['content']
            location = schedule['location']

            text = f"Ngày {date_param}\n" \
                   f"Từ {start_time} đến {end_time}\n" \
                   f"Nội dung: {content}\n" \
                   f"Địa điểm: {location}\n"
            dispatcher.utter_message(text)

        return [SlotSet("schedule_edited_record", schedule),
                SlotSet("schedule_current", schedule),
                SlotSet("schedule_info_provided", True)]


# Reset slots after schedule edit form
class ActionEditScheduleResetSlots(Action):

    def name(self) -> Text:
        return 'action_edit_schedule_reset_slots'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_schedule = tracker.get_slot('schedule_edited_record')
        change_made = tracker.get_slot('schedule_change_made')

        if tracker.get_slot('schedule_date_field_edit') is not None:
            current_schedule['date_field'] = tracker.get_slot('schedule_date_field_edit')
        if tracker.get_slot('schedule_start_time_edit') is not None:
            current_schedule['start_time'] = tracker.get_slot('schedule_start_time_edit')
        if tracker.get_slot('schedule_end_time_edit') is not None:
            current_schedule['end_time'] = tracker.get_slot('schedule_end_time_edit')
        if tracker.get_slot('schedule_content_edit') is not None:
            current_schedule['content'] = tracker.get_slot('schedule_content_edit')
        if tracker.get_slot('schedule_location_edit') is not None:
            current_schedule['location'] = tracker.get_slot('schedule_location_edit')

        if change_made is False or None:
            change_made = True

        # print(tracker.get_slot('schedule_change_made'))

        return [SlotSet("schedule_edited_record", current_schedule),
                SlotSet("schedule_selected_field", None),
                SlotSet("schedule_date_field_edit", None),
                SlotSet("schedule_start_time_edit", None),
                SlotSet("schedule_end_time_edit", None),
                SlotSet("schedule_content_edit", None),
                SlotSet("schedule_location_edit", None),
                SlotSet("schedule_change_made", change_made)]


# Confirm edit info
class ActionEditScheduleConfirmEditInfo(Action):
    def name(self) -> Text:
        return 'action_edit_schedule_confirm_edit_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edit_schedule = tracker.get_slot('schedule_edited_record')

        date_field = edit_schedule['date_field']
        start_time = edit_schedule['start_time']
        end_time = edit_schedule['end_time']
        content = edit_schedule['content']
        location = edit_schedule['location']

        dispatcher.utter_message("Đây là các thông tin bạn vừa thay đổi:\n")
        dispatcher.utter_message(f"Ngày: {date_field}\n"
                                 f"Thời gian bắt đầu: {start_time}\n"
                                 f"Thời gian kết thúc: {end_time}\n"
                                 f"Nội dung: {content}\n"
                                 f"Địa điểm: {location}")

        dispatcher.utter_message("Bạn có chắc muốn lưu các thay đổi này không?")

        return [SlotSet('schedule_change_made', False)]


# Edit schedule
class ActionEditSchedule(Action):
    def name(self) -> Text:
        return 'action_edit_schedule'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edited_schedule = tracker.get_slot('schedule_edited_record')
        current_schedule = tracker.get_slot('schedule_current')

        date_field = edited_schedule['date_field']
        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")

        start_time = edited_schedule['start_time']
        end_time = edited_schedule['end_time']
        content = edited_schedule['content']
        location = edited_schedule['location']

        # if the schedule is recurring
        # first add an exception record
        # then create a new schedule with edited info

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "start_time": start_time,
            "end_time": end_time,
            "content": content,
            "location": location
        }

        if current_schedule['is_recurring'] is True:
            payload = json.dumps(payload)

            response = requests.post(BASE_SCHEDULES_URL, data=payload, headers=headers)

            status = response.status_code
            if status == 400:
                err = response.json()
                for e in err.keys():
                    dispatcher.utter_message(err[e][0])
                return []

            elif status == 500:
                dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
                return []

            if status < 200 or status >= 300:
                dispatcher.utter_message(f"Ối, đã xảy ra lỗi, bạn hãy thử lại sau nhé. Mã lỗi:{status}")
                return []

            current_schedule['date_field'] = datetime.strptime(current_schedule['date_field'], "%d-%m-%Y")
            current_schedule['date_field'] = current_schedule['date_field'].strftime("%Y-%m-%d")

            exception_payload = {
                "schedule_id": current_schedule["id"],
                "date_field": current_schedule["date_field"]
            }

            exception_payload = json.dumps(exception_payload)

            response = requests.post(BASE_SCHEDULE_EXCEPTION_URL, data=exception_payload, headers=headers)

            status = response.status_code

            if status < 200 or status >= 300:
                dispatcher.utter_message(f"Ối, đã xảy ra lỗi, bạn hãy thử lại sau nhé. Mã lỗi:{status}")
                return []
        else:
            payload = json.dumps(payload)

            response = requests.put(BASE_SCHEDULES_URL + f"{current_schedule['id']}/", data=payload, headers=headers)

            status = response.status_code

            if status == 400:
                err = response.json()
                for e in err.keys():
                    dispatcher.utter_message(err[e][0])
                return []

            elif status == 500:
                dispatcher.utter_message("Xin lỗi, có vẻ server đang bận. Thử lại sau nhé")
                return []
            elif status < 200 or status >= 300:
                dispatcher.utter_message(f"Ối, đã xảy ra lỗi, bạn hãy thử lại sau nhé. Mã lỗi:{status}")
                return []

        dispatcher.utter_message("Thay đỏi thành công")

        return [SlotSet("schedule_edited_record", None),
                SlotSet("schedule_current", None),
                SlotSet("schedule_info_provided", False)]
