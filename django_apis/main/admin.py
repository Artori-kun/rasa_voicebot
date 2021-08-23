from django.contrib import admin
from .models.models import *


# Register your models here.

@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    exclude = ('date_created', 'last_modified')


# @admin.register(ReminderRecurrentPattern)
# class ReminderRecurrentPatternAdmin(admin.ModelAdmin):
#     exclude = ('date_created', 'last_modified')


@admin.register(ReminderInstanceException)
class ReminderInstanceExceptionAdmin(admin.ModelAdmin):
    exclude = ('date_created', 'last_modified')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    exclude = ('date_created', 'last_modified')


@admin.register(MySchedule)
class MyScheduleAdmin(admin.ModelAdmin):
    exclude = ('date_created', 'last_modified')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    exclude = ('date_created', 'last_modified')


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    exclude = ('date_created', 'last_modified')


# @admin.register(ScheduleRecurrentPattern)
# class ScheduleRecurrentPattern(admin.ModelAdmin):
#     exclude = ('date_created', 'last_modified')


@admin.register(ScheduleInstanceException)
class ScheduleInstanceException(admin.ModelAdmin):
    exclude = ('date_created', 'last_modified')
