from datetime import datetime, date
import difflib
from typing import List, Text, Dict, Any, Optional

from custom_date_extractor import date_extractor
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict


# Validation for create schedule form
class ValidateCreateScheduleForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_create_schedule_form"

    def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> List[Text]:
        if tracker.get_slot('schedule_is_recurring') is False or None:
            return ['schedule_date_field',
                    'schedule_start_time',
                    'schedule_end_time',
                    'schedule_content',
                    'schedule_location',
                    'schedule_is_recurring']
        else:
            return ['schedule_date_field',
                    'schedule_start_time',
                    'schedule_end_time',
                    'schedule_content',
                    'schedule_location',
                    'schedule_is_recurring',
                    'schedule_recurrence']

    def validate_schedule_date_field(self,
                                     slot_value: Any,
                                     dispatcher: CollectingDispatcher,
                                     tracker: Tracker,
                                     domain: DomainDict,
                                     ) -> Dict[Text, Any]:
        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"schedule_date_field": None}
        else:
            return {"schedule_date_field": dates[0]}

    def validate_schedule_start_time(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"schedule_start_time": None}
        else:
            return {"schedule_start_time": times[0]}

    def validate_schedule_end_time(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"schedule_end_time": None}
        else:
            return {"schedule_end_time": times[0]}

    def validate_schedule_location(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        location_str = slot_value.lower()
        intent = tracker.latest_message['intent'].get('name')

        if intent == 'skip':
            return {"schedule_location": 'Không có'}
        else:
            return {"schedule_location": location_str}

    def validate_schedule_is_recurring(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        intent = tracker.latest_message['intent'].get('name')

        if intent == 'affirm':
            return {"schedule_is_recurring": True}
        elif intent == 'deny':
            return {"schedule_is_recurring": False}
        else:
            return {"schedule_is_recurring": None}

    def validate_schedule_recurrence(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        recurrence_str = slot_value.lower()
        recurrence_type, separation_count = date_extractor.summary_recurrence(recurrence_str)

        if recurrence_type is None and separation_count is None:
            return {"schedule_recurrence": None}
        else:
            SlotSet("schedule_recurrence_type", recurrence_type)
            SlotSet("schedule_separation_count", separation_count)
            return {"schedule_recurrence": recurrence_str}


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
        if tracker.get_slot('schedule_selected_field') == 'date_field':
            return ['schedule_selected_field', 'schedule_date_field_edit']
        elif tracker.get_slot('schedule_selected_field') == 'start_time':
            return ['schedule_selected_field', 'schedule_start_time_edit']
        elif tracker.get_slot('schedule_selected_field') == 'end_time':
            return ['schedule_selected_field', 'schedule_end_time_edit']
        elif tracker.get_slot('schedule_selected_field') == 'content':
            return ['schedule_selected_field', 'schedule_content_edit']
        elif tracker.get_slot('schedule_selected_field') == 'location':
            return ['schedule_selected_field', 'schedule_location_edit']
        elif tracker.get_slot('schedule_selected_field') == 'all':
            return ['schedule_selected_field', 'schedule_date_field_edit', 'schedule_start_time_edit',
                    'schedule_end_time_edit', 'schedule_content_edit', 'schedule_location_edit']
        else:
            return ['schedule_selected_field']

    def validate_schedule_selected_field(self,
                                         slot_value: Any,
                                         dispatcher: CollectingDispatcher,
                                         tracker: Tracker,
                                         domain: DomainDict) -> Dict[Text, Any]:
        schedule_selected_field = tracker.latest_message.get('text').lower()

        synonyms_all = ["tất cả"]
        synonyms_date_field = ["ngày", "ngày tháng"]
        synonyms_start_time = ["thời gian bắt đầu"]
        synonyms_end_time = ["thời gian kết thúc"]
        synonyms_content = ["nội dung"]
        synonyms_location = ["địa điểm"]

        synonyms = synonyms_all + synonyms_date_field + synonyms_start_time + synonyms_end_time + synonyms_content + synonyms_location

        schedule_selected_field = difflib.get_close_matches(schedule_selected_field,
                                                            synonyms,
                                                            n=1)
        # print(schedule_selected_field)

        if len(schedule_selected_field) == 0:
            return {'schedule_selected_field': None}
        else:
            schedule_selected_field = schedule_selected_field[0]

        if schedule_selected_field in synonyms_all:
            return {'schedule_selected_field': 'all'}
        elif schedule_selected_field in synonyms_start_time:
            return {'schedule_selected_field': 'start_time'}
        elif schedule_selected_field in synonyms_end_time:
            return {'schedule_selected_field': 'end_time'}
        elif schedule_selected_field in synonyms_date_field:
            return {'schedule_selected_field': 'date_field'}
        elif schedule_selected_field in synonyms_content:
            return {'schedule_selected_field': 'content'}
        elif schedule_selected_field in synonyms_location:
            return {'schedule_selected_field': 'location'}

    def validate_date_field_edit(self,
                                 slot_value: Any,
                                 dispatcher: CollectingDispatcher,
                                 tracker: Tracker,
                                 domain: DomainDict,
                                 ) -> Dict[Text, Any]:
        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"schedule_date_field_edit": None}
        else:
            return {"schedule_date_field_edit": dates[0]}

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
            return {"schedule_start_time_edit": None}
        else:
            return {"schedule_start_time_edit": times[0]}

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
            return {"schedule_end_time_edit": None}
        else:
            return {"schedule_end_time_edit": times[0]}
