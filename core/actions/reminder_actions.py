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

BASE_REMINDERS_URL = "http://192.168.14.22:7000/reminders/"


# BASE_reminder_EXCEPTION_URL = "http://127.0.0.1:7000/reminder-exceptions/"


# RETRIEVE REMINDERS ACTIONS
# Show reminders
class ActionRetrieveReminder(Action):
    def name(self) -> Text:
        return "action_retrieve_reminder"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot('user_id')

        if user_id is None:
            dispatcher.utter_message("Bạn không có quyền thực hiền hành động này")
            return []

        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        # response = None
        reminders = []

        if len(times) == 0:
            if len(dates) == 0:
                dispatcher.utter_message("Xin lỗi, tôi không biết bạn cần thông tin vào thời điểm nào")
                return [SlotSet('reminder_current'), None]
            else:
                date_param = dates[0]
                response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}")
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}&time={times[0]}")

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
            reminders = response.json()
            print(reminders)

        # date_param = datetime.strptime(date_param, "%d-%m-%Y")
        # date_param = date_param.strftime("%Y-%m-%d")

        if len(reminders) == 0:
            dispatcher.utter_message("Bạn không có nhắc nhở gì")
            return [SlotSet('reminder_current', None)]
        else:
            for reminder in reminders:
                reminder['date_field'] = date_param
                # date_field = reminder['date_field']
                time_field = reminder['time_field']
                content = reminder['content']

                text = f"{time_field} ngày {date_param}\n" \
                       f"Nội dung: {content}\n"
                dispatcher.utter_message(text)

        return [SlotSet("reminder_current", reminders)]


class ActionCheckCurrentReminder(Action):

    def name(self) -> Text:
        return 'action_check_current_reminder'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_reminder = tracker.get_slot('reminder_current')

        if len(current_reminder) == 1:
            return [SlotSet('reminder_current_num', 'one'),
                    SlotSet('reminder_edited_record', current_reminder[0]),
                    SlotSet('reminder_current', current_reminder[0])]
        elif len(current_reminder) > 1:
            return [SlotSet('reminder_current_num', 'many')]
        elif current_reminder is None:
            return [SlotSet('reminder_current_num', 'none')]


# CREATE REMINDER ACTIONS
# submit
class ActionCreateReminderSubmit(Action):
    def name(self) -> Text:
        return "action_create_reminder_submit"

    async def run(self,
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: DomainDict) -> List[SlotSet]:
        user_id = tracker.get_slot('user_id')
        if user_id is None:
            dispatcher.utter_message("Bạn không có quyền thực hiền hành động này")
            return []

        date_field = tracker.get_slot('reminder_date_field')

        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")

        time_field = tracker.get_slot('reminder_time_field')
        content = tracker.get_slot('reminder_content')
        is_recurring = tracker.get_slot('reminder_is_recurring')
        recurrence_type = tracker.get_slot('reminder_recurrence_type')
        separation_count = tracker.get_slot('reminder_separation_count')

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "time_field": time_field,
            "content": content,
            "is_recurring": is_recurring,
            "recurring_type": recurrence_type,
            "separation_count": separation_count,
            "user_id": user_id
        }

        payload = json.dumps(payload)

        # print(payload)

        response = requests.post(BASE_REMINDERS_URL, data=payload, headers=headers)

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
            dispatcher.utter_message("Tạo nhắc nhở mới thành công")

        return []


# Confirm info before submit create
class ActionCreateReminderConfirmInfo(Action):

    def name(self) -> Text:
        return "action_create_reminder_confirm_info"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        date_field = tracker.get_slot('reminder_date_field')
        time_field = tracker.get_slot('reminder_time_field')
        content = tracker.get_slot('reminder_content')
        is_recurring = tracker.get_slot('reminder_is_recurring')
        recurrence_type = tracker.get_slot('reminder_recurrence_type')
        separation_count = tracker.get_slot('reminder_separation_count')

        # print(recurrence_type)
        # print(separation_count)

        dispatcher.utter_message("Đây là nhắc nhở bạn vửa tạo:")
        dispatcher.utter_message(f"{time_field} ngày: {date_field}\n"
                                 f"Nội dung: {content}\n")
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
        dispatcher.utter_message("Bạn có chắc muốn thêm nhắc nhở này chứ?")
        return []


class ActionCreateReminderResetForm(Action):

    def name(self) -> Text:
        return 'action_create_reminder_reset_form'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        message = tracker.latest_message.get('text')
        # print(message)
        dates = date_extractor.summary_date(message)
        # print(dates[0])
        times = date_extractor.summary_time(message)

        if len(dates) == 0:
            if len(times) == 0:
                return [SlotSet('reminder_date_field_preset', None),
                        SlotSet('reminder_time_field_preset', None),
                        SlotSet('reminder_date_field', None),
                        SlotSet('reminder_time_field', None),
                        SlotSet('reminder_content', None),
                        SlotSet('reminder_is_recurring', None),
                        SlotSet('reminder_recurrence', None),
                        SlotSet('reminder_recurrence_type', None),
                        SlotSet('reminder_separation_count', None)]
            else:
                date_param = date.today()
                date_param = date_param.strftime("%d-%m-%Y")

                return [SlotSet('reminder_date_field_preset', date_param),
                        SlotSet('reminder_time_field_preset', times[0]),
                        SlotSet('reminder_date_field', date_param),
                        SlotSet('reminder_time_field', times[0]),
                        SlotSet('reminder_content', None),
                        SlotSet('reminder_is_recurring', None),
                        SlotSet('reminder_recurrence', None),
                        SlotSet('reminder_recurrence_type', None),
                        SlotSet('reminder_separation_count', None)]
        else:
            if len(times) == 0:
                return [SlotSet('reminder_date_field_preset', dates[0]),
                        SlotSet('reminder_time_field_preset', None),
                        SlotSet('reminder_date_field', dates[0]),
                        SlotSet('reminder_time_field', None),
                        SlotSet('reminder_content', None),
                        SlotSet('reminder_is_recurring', None),
                        SlotSet('reminder_recurrence', None),
                        SlotSet('reminder_recurrence_type', None),
                        SlotSet('reminder_separation_count', None)]
            else:
                return [SlotSet('reminder_date_field_preset', dates[0]),
                        SlotSet('reminder_time_field_preset', times[0]),
                        SlotSet('reminder_date_field', dates[0]),
                        SlotSet('reminder_time_field', times[0]),
                        SlotSet('reminder_content', None),
                        SlotSet('reminder_is_recurring', None),
                        SlotSet('reminder_recurrence', None),
                        SlotSet('reminder_recurrence_type', None),
                        SlotSet('reminder_separation_count', None)]


# DELETE reminder ACTIONS
# Confirm info before delete
class ActionDeleteReminderConfirmInfo(Action):
    def name(self) -> Text:
        return "action_delete_reminder_confirm_info"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot('user_id')
        if user_id is None:
            dispatcher.utter_message("Bạn không có quyền thực hiền hành động này")
            return []

        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        # date_param = None
        # time_param = None
        response = None
        reminders = []
        # print(dates)
        # print(times)

        if len(times) == 0:
            if len(dates) == 0:
                dispatcher.utter_message("Xin lỗi, tôi không biết bạn cần xóa nhắc nhở vào thời điểm nào.")
                return [SlotSet("reminder_info_provided", False)]
            else:
                date_param = dates[0]
                response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}")
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}&time={times[0]}")

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
            reminders = response.json()

        if len(reminders) == 0:
            dispatcher.utter_message("Có vẻ như bạn không có nhắc nhở gì để xóa")
            return [SlotSet("reminder_info_provided", False)]
        else:
            dispatcher.utter_message("Đây là các nhắc nhở bạn muốn xóa:\n")
            for reminder in reminders:
                reminder['date_field'] = date_param
                date_field = reminder['date_field']
                time_field = reminder['time_field']
                content = reminder['content']

                text = f"{time_field} ngày {date_field}\n" \
                       f"Nội dung: {content}\n"
                dispatcher.utter_message(text)

            if datetime.strptime(date_param, "%d-%m-%Y") < datetime.today():
                dispatcher.utter_message("Đây có vẻ như là nhắc nhở từ những ngày trước. Việc "
                                         "xóa chúng có thể làm mất một số thông tin bạn cần sau này")

            # dispatcher.utter_message("Bạn có thực sự muốn xóa lịch không?")

        return [SlotSet('reminder_current', reminders),
                SlotSet('reminder_info_provided', True)]


# Delete reminder
class ActionDeleteReminder(Action):
    def name(self) -> Text:
        return "action_delete_reminder"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        reminders = tracker.get_slot('reminder_current')
        reminder_num = tracker.get_slot('reminder_current_num')
        fail_reminders = []
        # recurrent_reminder = []

        if len(reminders) == 0 or reminders is None:
            dispatcher.utter_message("Không có gì để xóa")
            return []

        if reminder_num == 'one':
            if reminders['is_recurring'] is False:
                response = requests.delete(BASE_REMINDERS_URL + str(reminders['id']))
            else:
                response = requests.delete(
                    BASE_REMINDERS_URL + str(reminders['id']) + f"/?date={reminders['date_field']}")

            status = response.status_code

            if status < 200 or status >= 300:
                fail_reminders.append(reminders)
        else:
            for reminder in reminders:
                if reminder['is_recurring'] is False:
                    response = requests.delete(BASE_REMINDERS_URL + str(reminder['id']))
                else:
                    response = requests.delete(
                        BASE_REMINDERS_URL + str(reminder['id']) + f"/?date={reminder['date_field']}")

                status = response.status_code

                if status < 200 or status >= 300:
                    fail_reminders.append(reminder)

        # if len(recurrent_reminder) != 0:
        #     SlotSet("reminder_current_recurrence", recurrent_reminder)

        if len(fail_reminders) != 0:
            dispatcher.utter_message("Ối, có vẻ đã xảy ra lỗi. Một hoặc một vài nhắc nhở mà bạn muốn xóa hiện chưa "
                                     "thể xóa được. Hãy thử lại sau nhé")
        else:
            dispatcher.utter_message("Đã xóa thành công")
        return [SlotSet('reminder_current', None)]


# EDIT REMINDER ACTIONS
# Reset form
class ActionEditReminderResetForm(Action):
    def name(self) -> Text:
        return 'action_edit_reminder_reset_form'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        return [SlotSet("reminder_selected_field", None),
                SlotSet("reminder_date_field_edit", None),
                SlotSet("reminder_time_field_edit", None),
                SlotSet("reminder_content_edit", None),
                SlotSet("reminder_change_made", False)]


# Check edit info
class ActionEditReminderConfirmInfo(Action):
    def name(self) -> Text:
        return 'action_edit_reminder_confirm_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        user_id = tracker.get_slot('user_id')
        if user_id is None:
            dispatcher.utter_message("Bạn không có quyền thực hiền hành động này")
            return []

        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        # response = None
        reminders = []

        if len(times) == 0:
            dispatcher.utter_message("Xin lỗi, bạn cần phải cung cấp đủ thông tin về thời gian và ngày tháng của nhắc "
                                     "nhở bạn muốn sửa.")
            return [SlotSet("reminder_info_provided", False)]
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_REMINDERS_URL + f"?u_id={user_id}&date={date_param}&time={times[0]}")

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
            reminders = response.json()

        if len(reminders) == 0:
            dispatcher.utter_message("Bạn không có nhắc nhở gì")
            return [SlotSet("reminder_info_provided", False)]
        else:
            dispatcher.utter_message("Đây là nhắc nhở bạn yêu cầu:")

            reminder = reminders[0]
            reminder['date_field'] = date_param

            time_field = reminder['time_field']
            content = reminder['content']

            text = f"{time_field} ngày {date_param}\n" \
                   f"Nội dung: {content}\n"
            dispatcher.utter_message(text)

        return [SlotSet("reminder_edited_record", reminder),
                SlotSet("reminder_current", reminder),
                SlotSet("reminder_info_provided", True)]


# Reset slots after reminder edit form
class ActionEditReminderResetSlots(Action):

    def name(self) -> Text:
        return 'action_edit_reminder_reset_slots'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_reminder = tracker.get_slot('reminder_edited_record')
        change_made = tracker.get_slot('reminder_change_made')

        if tracker.get_slot('reminder_date_field_edit') is not None:
            current_reminder['date_field'] = tracker.get_slot('reminder_date_field_edit')
        if tracker.get_slot('reminder_time_field_edit') is not None:
            current_reminder['time_field'] = tracker.get_slot('reminder_time_field_edit')
        if tracker.get_slot('reminder_content_edit') is not None:
            current_reminder['content'] = tracker.get_slot('reminder_content_edit')

        if change_made is False or None:
            change_made = True

        # print(tracker.get_slot('reminder_change_made'))

        return [SlotSet("reminder_edited_record", current_reminder),
                SlotSet("reminder_selected_field", None),
                SlotSet("reminder_date_field_edit", None),
                SlotSet("reminder_time_field_edit", None),
                SlotSet("reminder_content_edit", None),
                SlotSet("reminder_change_made", change_made)]


# Confirm edit info
class ActionEditReminderConfirmEditInfo(Action):
    def name(self) -> Text:
        return 'action_edit_reminder_confirm_edit_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edit_reminder = tracker.get_slot('reminder_edited_record')

        date_field = edit_reminder['date_field']
        time_field = edit_reminder['time_field']
        content = edit_reminder['content']

        dispatcher.utter_message("Đây là các thông tin bạn vừa thay đổi:\n")
        dispatcher.utter_message(f"Ngày: {date_field}\n"
                                 f"Thời gian: {time_field}\n"
                                 f"Nội dung: {content}\n")

        dispatcher.utter_message("Bạn có chắc muốn lưu các thay đổi này không?")

        return [SlotSet('reminder_change_made', False)]


# Edit reminder
class ActionEditReminder(Action):
    def name(self) -> Text:
        return 'action_edit_reminder'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edited_reminder = tracker.get_slot('reminder_edited_record')
        current_reminder = tracker.get_slot('reminder_current')

        date_field = edited_reminder['date_field']
        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")

        time_field = edited_reminder['time_field']
        content = edited_reminder['content']

        # if the reminder is recurring
        # first add an exception record
        # then create a new reminder with edited info

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "time_field": time_field,
            "content": content
        }

        if current_reminder['is_recurring'] is True:
            payload = json.dumps(payload)

            response = requests.put(
                BASE_REMINDERS_URL + f"{current_reminder['id']}" + f"/?date={current_reminder['date_field']}",
                data=payload,
                headers=headers)

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
        else:
            payload = json.dumps(payload)

            response = requests.put(BASE_REMINDERS_URL + f"{current_reminder['id']}/", data=payload, headers=headers)

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

        dispatcher.utter_message("Thay đổi thành công")

        return [SlotSet("reminder_edited_record", None),
                SlotSet("reminder_current", None),
                SlotSet("reminder_info_provided", False)]
