from datetime import datetime
from django.shortcuts import render
from ..models.models import *
from rest_framework import viewsets, permissions
from ..serializers.serializers import *


# Create your views here.

class MyScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = MyScheduleSerializer

    permission_classes = [
        permissions.AllowAny
    ]

    def get_queryset(self):
        date = self.request.query_params.get('date')
        time = self.request.query_params.get('time')
        # content = self.request.query_params.get('content')
        queryset = MySchedule.objects.all()

        if date is not None:
            date = datetime.strptime(date, "%d-%m-%Y")
            queryset = queryset.filter(date_field=date)
            if time is not None:
                time = datetime.strptime(time, "%H:%M")
                queryset = queryset.exclude(start_time__gt=time).exclude(end_time__lt=time)

        return queryset
