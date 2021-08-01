from ..models.models import *


def check_occurrence(date_param, recurring_object):
    # schedule_object = MySchedule()

    if recurring_object.is_recurring is False:
        if date_param == recurring_object.date_field:
            return True
        else:
            return False
    else:
        if recurring_object.date_field > date_param:
            return False

        if recurring_object.recurrence_end_date is not None:
            if date_param > recurring_object.recurrence_end_date:
                return False

        if recurring_object.recurring_type == 'daily':
            date_diff = date_param - recurring_object.date_field
            if date_diff.days % (1 * recurring_object.separation_count) == 0:
                return True
            else:
                return False
        elif recurring_object.recurring_type == 'weekly':
            date_diff = date_param - recurring_object.date_field
            if date_diff.days % (7 * recurring_object.separation_count) == 0:
                return True
            else:
                return False
        elif recurring_object.recurring_type == 'monthly':
            date_diff = (date_param.year - recurring_object.date_field.year) * 12 + \
                        date_param.month - recurring_object.date_field.month
            if date_diff % (1 * recurring_object.separation_count) == 0 \
                    and date_param.day == recurring_object.date_field.day:
                return True
            else:
                return False
        elif recurring_object.recurring_type == 'yearly':
            date_diff = date_param.year - recurring_object.date_field.year
            if date_diff % (1 * recurring_object.separation_count) == 0 \
                    and date_param.day == recurring_object.date_field.day \
                    and date_param.month == recurring_object.date_field.month:
                return True
            else:
                return False
