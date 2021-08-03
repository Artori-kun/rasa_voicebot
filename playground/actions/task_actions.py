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

BASE_TASKS_URL = "http://127.0.0.1:7000/tasks/"


# BASE_task_EXCEPTION_URL = "http://127.0.0.1:7000/task-exceptions/"


# RETRIEVE TASKS ACTIONS
# Show tasks
class ActionRetrieveTask(Action):
    def name(self) -> Text:
        return "action_retrieve_task"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        response = None
        tasks = []

        if len(times) == 0:
            if len(dates) == 0:
                dispatcher.utter_message("Xin lỗi, tôi không biết bạn cần thông tin vào thời điểm nào")
                return [SlotSet('task_current'), None]
            else:
                date_param = dates[0]
                response = requests.get(BASE_TASKS_URL + f"?date={date_param}")
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_TASKS_URL + f"?date={date_param}&time1={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_TASKS_URL + f"?date={date_param}&time1={times[0]}")

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
            tasks = response.json()

        # date_param = datetime.strptime(date_param, "%d-%m-%Y")
        # date_param = date_param.strftime("%Y-%m-%d")

        if len(tasks) == 0:
            dispatcher.utter_message("Bạn không có công việc gì")
            return [SlotSet('task_current', None)]
        else:
            for task in tasks:
                date_field = task['date_field']
                time_field = task['time_field']
                content = task['content']

                text = f"{time_field} ngày {date_field}\n" \
                       f"Nội dung: {content}\n"
                dispatcher.utter_message(text)

            return [SlotSet("task_current", tasks)]


class ActionRetrieveTaskRemain(Action):

    def name(self) -> Text:
        return 'action_retrieve_task_remain'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        time_param1 = datetime.now().time()
        time_param1 = time_param1.strftime("%H:%M")

        time_param2 = "24:00"

        date_param = datetime.today().date()
        date_param = date_param.strftime("%d-%m-%Y")

        tasks = []

        response = requests.get(BASE_TASKS_URL + f"?date={date_param}&time1={time_param1}&time2={time_param2}")

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
            tasks = response.json()

        if len(tasks) == 0:
            dispatcher.utter_message("Bạn không có công việc gì")
            return [SlotSet('task_current', None)]
        else:
            for task in tasks:
                date_field = task['date_field']
                time_field = task['time_field']
                content = task['content']

                text = f"{time_field} ngày {date_field}\n" \
                       f"Nội dung: {content}\n"
                dispatcher.utter_message(text)

            return [SlotSet("task_current", tasks)]


class ActionCheckCurrentTask(Action):

    def name(self) -> Text:
        return 'action_check_current_task'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_task = tracker.get_slot('task_current')

        if len(current_task) == 1:
            return [SlotSet('task_current_num', 'one'),
                    SlotSet('task_edited_record', current_task[0]),
                    SlotSet('task_current', current_task[0])]
        elif len(current_task) > 1:
            return [SlotSet('task_current_num', 'many')]
        elif current_task is None:
            return [SlotSet('task_current_num', 'none')]


# CREATE TASK ACTIONS
# submit
class ActionCreateTaskSubmit(Action):
    def name(self) -> Text:
        return "action_create_task_submit"

    async def run(self,
                  dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: DomainDict) -> List[SlotSet]:
        date_field = tracker.get_slot('task_date_field')

        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")

        time_field = tracker.get_slot('task_time_field')
        content = tracker.get_slot('task_content')

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "time_field": time_field,
            "content": content
        }

        payload = json.dumps(payload)

        # print(payload)

        response = requests.post("http://127.0.0.1:7000/tasks/", data=payload, headers=headers)

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
            dispatcher.utter_message("Tạo công việc mới thành công")

        return []


# Confirm info before submit create
class ActionCreateTaskConfirmInfo(Action):

    def name(self) -> Text:
        return "action_create_task_confirm_info"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        date_field = tracker.get_slot('task_date_field')
        time_field = tracker.get_slot('task_time_field')
        content = tracker.get_slot('task_content')

        # print(recurrence_type)
        # print(separation_count)

        dispatcher.utter_message("Đây là công việc bạn vửa tạo:")
        dispatcher.utter_message(f"{time_field} ngày: {date_field}\n"
                                 f"Nội dung: {content}\n")

        dispatcher.utter_message("Bạn có chắc muốn thêm công việc này chứ?")
        return []


class ActionCreateTaskResetForm(Action):

    def name(self) -> Text:
        return 'action_create_task_reset_form'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)

        if len(dates) == 0:
            if len(times) == 0:
                return [SlotSet('task_date_field', None),
                        SlotSet('task_time_field', None),
                        SlotSet('task_content', None)]
            else:
                date_param = date.today()
                date_param = date_param.strftime("%d-%m-%Y")

                return [SlotSet('task_date_field', date_param),
                        SlotSet('task_time_field', times[0]),
                        SlotSet('task_content', None)]
        else:
            if len(times) == 0:
                return [SlotSet('task_date_field', dates[0]),
                        SlotSet('task_time_field', None),
                        SlotSet('task_content', None)]
            else:
                return [SlotSet('task_date_field', dates[0]),
                        SlotSet('task_time_field', times[0]),
                        SlotSet('task_content', None)]


# DELETE TASK ACTIONS
# Confirm info before delete
class ActionDeleteTaskConfirmInfo(Action):
    def name(self) -> Text:
        return "action_delete_task_confirm_info"

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
        tasks = []
        # print(dates)
        # print(times)

        if len(times) == 0:
            if len(dates) == 0:
                dispatcher.utter_message("Xin lỗi, tôi không biết bạn cần xóa công việc vào thời điểm nào.")
                return [SlotSet("task_info_provided", False)]
            else:
                date_param = dates[0]
                response = requests.get(BASE_TASKS_URL + f"?date={date_param}")
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_TASKS_URL + f"?date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_TASKS_URL + f"?date={date_param}&time={times[0]}")

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
            tasks = response.json()

        if len(tasks) == 0:
            dispatcher.utter_message("Có vẻ như bạn không có công việc gì để xóa")
            return [SlotSet("task_info_provided", False)]
        else:
            dispatcher.utter_message("Đây là các công việc bạn muốn xóa:\n")
            for task in tasks:
                date_field = task['date_field']
                time_field = task['time_field']
                content = task['content']

                text = f"{time_field} ngày {date_field}\n" \
                       f"Nội dung: {content}\n"
                dispatcher.utter_message(text)

            if datetime.strptime(date_param, "%d-%m-%Y") < datetime.today():
                dispatcher.utter_message("Đây có vẻ như là công việc từ những ngày trước. Việc "
                                         "xóa chúng có thể làm mất một số thông tin bạn cần sau này")

            # dispatcher.utter_message("Bạn có thực sự muốn xóa lịch không?")

        return [SlotSet('task_current', tasks),
                SlotSet('task_info_provided', True)]


# Delete task
class ActionDeleteTask(Action):
    def name(self) -> Text:
        return "action_delete_task"

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        tasks = tracker.get_slot('task_current')
        fail_tasks = []
        # recurrent_task = []

        if len(tasks) == 0 or tasks is None:
            dispatcher.utter_message("Không có gì để xóa")
            return []

        for task in tasks:
            response = requests.delete(BASE_TASKS_URL + f"{task['id']}/")

            status = response.status_code

            if status < 200 or status >= 300:
                fail_tasks.append(task)

        # if len(recurrent_task) != 0:
        #     SlotSet("task_current_recurrence", recurrent_task)

        if len(fail_tasks) != 0:
            dispatcher.utter_message("Ối, có vẻ đã xảy ra lỗi. Một hoặc một vài công việc mà bạn muốn xóa hiện chưa "
                                     "thể xóa được. Hãy thử lại sau nhé")
        else:
            dispatcher.utter_message("Đã xóa thành công")
        return [SlotSet('task_current', None)]


# EDIT TASK ACTIONS
# Reset form
class ActionEditTaskResetForm(Action):
    def name(self) -> Text:
        return 'action_edit_task_reset_form'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        return [SlotSet("task_selected_field", None),
                SlotSet("task_date_field_edit", None),
                SlotSet("task_time_field_edit", None),
                SlotSet("task_content_edit", None),
                SlotSet("task_change_made", False)]


# Check edit info
class ActionEditTaskConfirmInfo(Action):
    def name(self) -> Text:
        return 'action_edit_task_confirm_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        # SlotSet('task_edited_record', None)
        message = tracker.latest_message.get('text')
        dates = date_extractor.summary_date(message)
        times = date_extractor.summary_time(message)
        response = None
        tasks = []

        if len(times) == 0:
            dispatcher.utter_message("Xin lỗi, bạn cần phải cung cấp đủ thông tin về thời gian và ngày tháng của công "
                                     "việc bạn muốn sửa.")
            return [SlotSet("task_info_provided", False)]
        elif len(dates) == 0:
            date_param = date.today()
            date_param = date_param.strftime("%d-%m-%Y")
            response = requests.get(BASE_TASKS_URL + f"?date={date_param}&time={times[0]}")
        else:
            date_param = dates[0]
            response = requests.get(BASE_TASKS_URL + f"?date={date_param}&time={times[0]}")

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
            tasks = response.json()

        if len(tasks) == 0:
            dispatcher.utter_message("Bạn không có công việc gì")
            return [SlotSet("task_info_provided", False)]
        else:
            dispatcher.utter_message("Đây là công việc bạn yêu cầu:")

            task = tasks[0]
            date_field = task['date_field']
            time_field = task['time_field']
            content = task['content']

            text = f"{time_field} ngày {date_field}\n" \
                   f"Nội dung: {content}\n"
            dispatcher.utter_message(text)

        return [SlotSet("task_edited_record", task),
                SlotSet("task_current", task),
                SlotSet("task_info_provided", True)]


# Reset slots after task edit form
class ActionEditTaskResetSlots(Action):

    def name(self) -> Text:
        return 'action_edit_task_reset_slots'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        current_task = tracker.get_slot('task_edited_record')
        change_made = tracker.get_slot('task_change_made')

        if tracker.get_slot('task_date_field_edit') is not None:
            current_task['date_field'] = tracker.get_slot('task_date_field_edit')
        if tracker.get_slot('task_time_field_edit') is not None:
            current_task['time_field'] = tracker.get_slot('task_time_field_edit')
        if tracker.get_slot('task_content_edit') is not None:
            current_task['content'] = tracker.get_slot('task_content_edit')

        if change_made is False or None:
            change_made = True

        # print(tracker.get_slot('task_change_made'))

        return [SlotSet("task_edited_record", current_task),
                SlotSet("task_selected_field", None),
                SlotSet("task_date_field_edit", None),
                SlotSet("task_time_field_edit", None),
                SlotSet("task_content_edit", None),
                SlotSet("task_change_made", change_made)]


# Confirm edit info
class ActionEditTaskConfirmEditInfo(Action):
    def name(self) -> Text:
        return 'action_edit_task_confirm_edit_info'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edit_task = tracker.get_slot('task_edited_record')

        date_field = edit_task['date_field']
        time_field = edit_task['time_field']
        content = edit_task['content']

        dispatcher.utter_message("Đây là các thông tin bạn vừa thay đổi:\n")
        dispatcher.utter_message(f"Ngày: {date_field}\n"
                                 f"Thời gian: {time_field}\n"
                                 f"Nội dung: {content}\n")

        dispatcher.utter_message("Bạn có chắc muốn lưu các thay đổi này không?")

        return [SlotSet('task_change_made', False)]


# Edit task
class ActionEditTask(Action):
    def name(self) -> Text:
        return 'action_edit_task'

    async def run(self,
                  dispatcher: "CollectingDispatcher",
                  tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        edited_task = tracker.get_slot('task_edited_record')
        current_task = tracker.get_slot('task_current')

        date_field = edited_task['date_field']
        date_field = datetime.strptime(date_field, "%d-%m-%Y")
        date_field = date_field.strftime("%Y-%m-%d")

        time_field = edited_task['time_field']
        content = edited_task['content']

        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }

        payload = {
            "date_field": date_field,
            "time_field": time_field,
            "content": content
        }

        payload = json.dumps(payload)

        response = requests.put(BASE_TASKS_URL + f"{current_task['id']}/", data=payload, headers=headers)

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

        return [SlotSet("task_edited_record", None),
                SlotSet("task_current", None),
                SlotSet("task_info_provided", False)]
