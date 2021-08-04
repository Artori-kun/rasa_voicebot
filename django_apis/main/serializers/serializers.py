from rest_framework import serializers
from ..models.models import *
from ..util.model_util import check_occurrence
from datetime import datetime


class MyScheduleSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        # date = datetime.strptime(attrs['date_field'], "%d-%m-%Y")
        # attrs['date_field'] = datetime.strftime(date, "%Y-%m-%d")

        if attrs['start_time'] > attrs['end_time']:
            raise serializers.ValidationError("Giờ bắt đầu phải sớm hơn giờ kết thúc")

        exceptions = ScheduleInstanceException.objects.filter(date_field=attrs['date_field'])
        exception_schedule_id = [e.schedule_id for e in exceptions]

        schedules = MySchedule.objects.exclude(id__in=exception_schedule_id)

        if self.instance:
            object_id = self.instance.id
            schedules = schedules.exclude(id=object_id)

        # schedules = list(schedules)

        for schedule in schedules:
            if check_occurrence(attrs['date_field'], schedule):
                if schedule.start_time < attrs['start_time'] < schedule.end_time or schedule.start_time < \
                        attrs['end_time'] < schedule.end_time:
                    print(schedule.id)
                    raise serializers.ValidationError(f"Trùng giờ với lịch đã có")

        return attrs

    class Meta:
        model = MySchedule
        exclude = ['date_created', 'last_modified']


# class ScheduleRecurrentPatternSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ScheduleRecurrentPattern
#         exclude = ['date_created', 'last_modified']


class ScheduleInstanceExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleInstanceException
        exclude = ['date_created', 'last_modified']


# class ReminderRecurrentPatternSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ReminderRecurrentPattern
#         exclude = ['date_created', 'last_modified']


class ReminderInstanceExceptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReminderInstanceException
        exclude = ['date_created', 'last_modified']


class ReminderSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        exceptions = ReminderInstanceException.objects.filter(date_field=attrs['date_field'])
        exception_reminder_id = [e.schedule_id for e in exceptions]

        reminder = Reminder.objects.exclude(id__in=exception_reminder_id)
        reminder = reminder.filter(id__in=[r.id for r in reminder if check_occurrence(attrs['date_field'], r)])

        for r in reminder:
            if r.time_field == attrs['time_field']:
                serializers.ValidationError(f"Trùng với một nhắc nhở đã có")

        return attrs
    # recurrent_pattern = ReminderRecurrentPatternSerializer()

    class Meta:
        model = Reminder
        exclude = ['date_created', 'last_modified']
        # fields = [
        #     'date_field',
        #     'time_field',
        #     'content',
        #     'is_recurring',
        #     'recurrence_end_date',
        #     'is_active',
        #     'user_id',
        #     'recurrent_pattern'
        # ]


class TaskSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        tasks = Task.objects.filter(date_field=attrs['date_field'])

        for t in tasks:
            if t.time_field == attrs['time_field']:
                serializers.ValidationError("Trùng với một công việc đã có")

        return attrs

    class Meta:
        model = Task
        exclude = ['date_created', 'last_modified']


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        exclude = ['date_created', 'last_modified']


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
