from datetime import datetime, date
import difflib
from typing import List, Text, Dict, Any, Optional

from custom_date_extractor import date_extractor
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict


# Validation for create task form
class ValidateCreateTaskForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_create_task_form"

    def validate_task_date_field(self,
                                 slot_value: Any,
                                 dispatcher: CollectingDispatcher,
                                 tracker: Tracker,
                                 domain: DomainDict,
                                 ) -> Dict[Text, Any]:
        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"task_date_field": None}
        else:
            return {"task_date_field": dates[0]}

    def validate_task_time_field(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"task_time_field": None}
        else:
            return {"task_time_field": times[0]}


# Validation for edit task form
class ValidateEditTaskForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_edit_task_form"

    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Optional[List[Text]]:
        if tracker.get_slot('task_selected_field') == 'date_field':
            return ['task_selected_field', 'task_date_field_edit']
        elif tracker.get_slot('task_selected_field') == 'time_field':
            return ['task_selected_field', 'task_time_field_edit']
        elif tracker.get_slot('task_selected_field') == 'content':
            return ['task_selected_field', 'task_content_edit']
        elif tracker.get_slot('task_selected_field') == 'all':
            return ['task_selected_field', 'task_date_field_edit', 'task_time_field_edit',
                    'task_content_edit']
        else:
            return ['task_selected_field']

    def validate_task_selected_field(self,
                                     slot_value: Any,
                                     dispatcher: CollectingDispatcher,
                                     tracker: Tracker,
                                     domain: DomainDict) -> Dict[Text, Any]:
        task_selected_field = tracker.latest_message.get('text').lower()

        synonyms_all = ["tất cả"]
        synonyms_date_field = ["ngày", "ngày tháng"]
        synonyms_time_field = ["thời gian"]
        synonyms_content = ["nội dung"]

        synonyms = synonyms_all + synonyms_date_field + synonyms_time_field + synonyms_content

        task_selected_field = difflib.get_close_matches(task_selected_field,
                                                        synonyms,
                                                        n=1)
        # print(task_selected_field)

        if len(task_selected_field) == 0:
            return {'task_selected_field': None}
        else:
            task_selected_field = task_selected_field[0]

        if task_selected_field in synonyms_all:
            return {'task_selected_field': 'all'}
        elif task_selected_field in synonyms_time_field:
            return {'task_selected_field': 'time_field'}
        elif task_selected_field in synonyms_date_field:
            return {'task_selected_field': 'date_field'}
        elif task_selected_field in synonyms_content:
            return {'task_selected_field': 'content'}

    def validate_task_date_field_edit(self,
                                      slot_value: Any,
                                      dispatcher: CollectingDispatcher,
                                      tracker: Tracker,
                                      domain: DomainDict,
                                      ) -> Dict[Text, Any]:
        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"task_date_field_edit": None}
        else:
            return {"task_date_field_edit": dates[0]}

    def validate_task_time_field_edit(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"task_time_field_edit": None}
        else:
            return {"task_time_field_edit": times[0]}
