from datetime import datetime, date
from django.shortcuts import render
from ..models.models import *
from ..util.model_util import check_occurrence_schedule
from rest_framework import viewsets, permissions
from ..serializers.serializers import *
from itertools import chain


# Create your views here.

class MyScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = MyScheduleSerializer

    permission_classes = [
        permissions.AllowAny
    ]

    def get_queryset(self):
        date_param = self.request.query_params.get('date')
        time_param = self.request.query_params.get('time')
        # content = self.request.query_params.get('content')
        if date_param is None:
            date_param = date.today()

        date_param = datetime.strptime(date_param, "%d-%m-%Y")

        exception_queryset = ScheduleInstanceException.objects.filter(date_field=date_param)

        queryset = MySchedule.objects.exclude(id__in=[e.schedule_id for e in exception_queryset])
        queryset = queryset.filter(id__in=[s.id for s in queryset if check_occurrence_schedule(date_param, s)])

        if time_param is not None:
            time_param = datetime.strptime(time_param, "%H:%M")
            queryset = queryset.exclude(start_time__gt=time_param).exclude(end_time__lt=time_param)

        return queryset
