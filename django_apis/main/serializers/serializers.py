from rest_framework import serializers
from ..models.models import *
from datetime import datetime


class MyScheduleSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        # date = datetime.strptime(attrs['date_field'], "%d-%m-%Y")
        # attrs['date_field'] = datetime.strftime(date, "%Y-%m-%d")

        if attrs['start_time'] > attrs['end_time']:
            raise serializers.ValidationError("Giờ bắt đầu phải sớm hơn giờ kết thúc")

        schedules = MySchedule.objects.filter(date_field=attrs['date_field'])

        for schedule in schedules:
            if schedule.start_time < attrs['start_time'] < schedule.end_time or schedule.start_time < \
                    attrs['end_time'] < schedule.end_time:
                raise serializers.ValidationError(f"Trùng giờ với lịch đã có")

        return attrs

    # def save(self, **kwargs):
    #
    #     schedules = Myschedule.objects.filter(date_field=self.validated_data['date_field'])
    #
    #     for schedule in schedules:
    #         if schedule.start_time < self.validated_data['start_time'] < schedule.end_time or schedule.start_time < \
    #                 self.validated_data['end_time'] < schedule.end_time:
    #             raise serializers.ValidationError(f"Trùng giờ với lịch đã có")
    #
    #     super().save(**kwargs)

    class Meta:
        model = MySchedule
        fields = "__all__"


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = "__all__"


class AlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alarm
        fields = "__all__"


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = "__all__"
