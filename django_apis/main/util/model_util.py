from ..models.models import *


def check_occurrence_schedule(date_param, schedule_object):
    # schedule_object = MySchedule()

    if not schedule_object.is_recurring:
        if date_param == schedule_object.date_field:
            return True
        else:
            return False
    else:
        if schedule_object.date_field > date_param:
            return False

        if schedule_object.recurrence_end_date is not None:
            if date_param > schedule_object.recurrence_end_date:
                return False

        if schedule_object.recurring_type == 'daily':
            date_diff = date_param - schedule_object.date_field
            if date_diff.days % (1 * schedule_object.separation_count) == 0:
                return True
        elif schedule_object.recurring_type == 'weekly':
            date_diff = date_param - schedule_object.date_field
            if date_diff.days % (7 * schedule_object.separation_count) == 0:
                return True
        elif schedule_object.recurring_type == 'monthly':
            date_diff = (date_param.year - schedule_object.date_field) * 12 + \
                        date_param.month - schedule_object.date_field.month
            if date_diff % (1 * schedule_object.separation_count) == 0 \
                    and date_param.day == schedule_object.date_field.day:
                return True
        elif schedule_object.recurring_type == 'yearly':
            date_diff = date_param.year - schedule_object.date_field.year
            if date_diff % (1 * schedule_object.separation_count) == 0 \
                    and date_param.day == schedule_object.date_field.day \
                    and date_param.month == schedule_object.date_field.month:
                return True
