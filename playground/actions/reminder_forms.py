from datetime import datetime, date
import difflib
from typing import List, Text, Dict, Any, Optional

from custom_date_extractor import date_extractor
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict


# Validation for create reminder form
class ValidateCreateReminderForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_create_reminder_form"

    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> List[Text]:
        fields = ['reminder_date_field',
                  'reminder_time_field',
                  'reminder_content',
                  'reminder_is_recurring']

        if tracker.get_slot('reminder_is_recurring') is True:
            fields.extend(['reminder_recurrence', 'reminder_recurrence_type', 'reminder_separation_count'])
        if tracker.get_slot('reminder_date_field') is not None:
            # print("required slot date field removed")
            fields.remove('reminder_date_field')
        if tracker.get_slot('reminder_time_field') is not None:
            fields.remove('reminder_time_field')
        if tracker.get_slot('reminder_content') is not None:
            fields.remove('reminder_content')

        return fields

    def validate_reminder_date_field(self,
                                     slot_value: Any,
                                     dispatcher: CollectingDispatcher,
                                     tracker: Tracker,
                                     domain: DomainDict,
                                     ) -> Dict[Text, Any]:
        date_field = tracker.slots.get('reminder_date_field_preset')
        if date_field is not None:
            return {"reminder_date_field": date_field}

        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"reminder_date_field": None}
        else:
            return {"reminder_date_field": dates[0]}

    def validate_reminder_time_field(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_field = tracker.slots.get('reminder_time_field_preset')
        if time_field is not None:
            return {"reminder_time_field": time_field}

        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"reminder_time_field": None}
        else:
            return {"reminder_time_field": times[0]}

    def validate_reminder_is_recurring(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        intent = tracker.latest_message['intent'].get('name')

        if intent == 'affirm':
            return {"reminder_is_recurring": True}
        elif intent == 'deny':
            return {"reminder_is_recurring": False}
        else:
            return {"reminder_is_recurring": None}

    def validate_reminder_recurrence(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        recurrence_str = slot_value.lower()
        recurrence_type, separation_count = date_extractor.summary_recurrence(recurrence_str)
        # print(recurrence_type)
        # print(separation_count)

        if recurrence_type is None:
            return {"reminder_recurrence": None}
        else:
            # SlotSet("reminder_recurrence_type", recurrence_type)
            # SlotSet("reminder_separation_count", separation_count)
            return {"reminder_recurrence": recurrence_str,
                    "reminder_recurrence_type": recurrence_type,
                    "reminder_separation_count": separation_count}


# Validation for edit reminder form
class ValidateEditReminderForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_edit_reminder_form"

    async def required_slots(
            self,
            slots_mapped_in_domain: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Optional[List[Text]]:
        if tracker.get_slot('reminder_selected_field') == 'date_field':
            return ['reminder_selected_field', 'reminder_date_field_edit']
        elif tracker.get_slot('reminder_selected_field') == 'time_field':
            return ['reminder_selected_field', 'reminder_time_field_edit']
        elif tracker.get_slot('reminder_selected_field') == 'content':
            return ['reminder_selected_field', 'reminder_content_edit']
        elif tracker.get_slot('reminder_selected_field') == 'all':
            return ['reminder_selected_field', 'reminder_date_field_edit', 'reminder_time_field_edit',
                    'reminder_content_edit']
        else:
            return ['reminder_selected_field']

    def validate_reminder_selected_field(self,
                                         slot_value: Any,
                                         dispatcher: CollectingDispatcher,
                                         tracker: Tracker,
                                         domain: DomainDict) -> Dict[Text, Any]:
        reminder_selected_field = tracker.latest_message.get('text').lower()

        synonyms_all = ["tất cả"]
        synonyms_date_field = ["ngày", "ngày tháng"]
        synonyms_time_field = ["thời gian"]
        synonyms_content = ["nội dung"]

        synonyms = synonyms_all + synonyms_date_field + synonyms_time_field + synonyms_content

        reminder_selected_field = difflib.get_close_matches(reminder_selected_field,
                                                            synonyms,
                                                            n=1)
        # print(reminder_selected_field)

        if len(reminder_selected_field) == 0:
            return {'reminder_selected_field': None}
        else:
            reminder_selected_field = reminder_selected_field[0]

        if reminder_selected_field in synonyms_all:
            return {'reminder_selected_field': 'all'}
        elif reminder_selected_field in synonyms_time_field:
            return {'reminder_selected_field': 'time_field'}
        elif reminder_selected_field in synonyms_date_field:
            return {'reminder_selected_field': 'date_field'}
        elif reminder_selected_field in synonyms_content:
            return {'reminder_selected_field': 'content'}

    def validate_reminder_date_field_edit(self,
                                          slot_value: Any,
                                          dispatcher: CollectingDispatcher,
                                          tracker: Tracker,
                                          domain: DomainDict,
                                          ) -> Dict[Text, Any]:
        date_str = slot_value.lower()
        dates = date_extractor.summary_date(date_str)

        if len(dates) == 0:
            return {"reminder_date_field_edit": None}
        else:
            return {"reminder_date_field_edit": dates[0]}

    def validate_reminder_time_field_edit(
            self,
            slot_value: Any,
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain: "DomainDict",
    ) -> Dict[Text, Any]:
        time_str = slot_value.lower()
        times = date_extractor.summary_time(time_str)

        if len(times) == 0:
            return {"reminder_time_field_edit": None}
        else:
            return {"reminder_time_field_edit": times[0]}
