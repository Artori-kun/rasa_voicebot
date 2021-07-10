from django.contrib import admin
from .models.models import *
# Register your models here.

admin.site.register(Alarm)
admin.site.register(Appointment)
admin.site.register(MySchedule)
admin.site.register(Reminder)



