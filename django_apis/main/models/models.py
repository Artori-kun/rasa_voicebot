# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import datetime
import pytz

from django.db import models
from django.utils.timezone import now


class Reminder(models.Model):
    date_field = models.DateField(db_column='date_')  # Field renamed because it ended with '_'.
    time_field = models.TimeField(db_column='time_', blank=True, null=True)  # Field renamed because it ended with '_'.
    content = models.CharField(max_length=200, db_collation='utf8_general_ci', null=True, blank=True)

    is_recurring = models.BooleanField(default=False)
    recurrence_end_date = models.DateField(blank=True, null=True)
    recurring_type = models.CharField(max_length=50, blank=True, null=True)
    separation_count = models.IntegerField(blank=True, null=True)
    max_number_of_occurrences = models.IntegerField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=now)
    last_modified = models.DateTimeField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Reminder'


class Task(models.Model):
    date_field = models.DateField(db_column='date_')  # Field renamed because it ended with '_'.
    time_field = models.TimeField(db_column='time_', blank=True, null=True)  # Field renamed because it ended with '_'.
    content = models.CharField(max_length=200, db_collation='utf8_general_ci')
    user_id = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(default=now)
    last_modified = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Task'


class MySchedule(models.Model):
    date_field = models.DateField(db_column='date_')  # Field renamed because it ended with '_'.
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    content = models.CharField(max_length=200, db_collation='utf8_general_ci')
    location = models.CharField(max_length=200, db_collation='utf8_general_ci', blank=True, null=True)
    date_created = models.DateTimeField(null=True, default=now)
    last_modified = models.DateTimeField(null=True, default=now)
    is_active = models.BooleanField(default=True)

    is_recurring = models.BooleanField(default=False)
    recurring_type = models.CharField(max_length=50, blank=True, null=True,
                                      choices=[('daily', 'daily'), ('weekly', 'weekly'),
                                               ('monthly', 'monthly'), ('yearly', 'yearly')])
    separation_count = models.IntegerField(blank=True, null=True)
    max_number_of_occurrences = models.IntegerField(blank=True, null=True)
    recurrence_end_date = models.DateField(blank=True, null=True)

    parent_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'MySchedule'


class Contact(models.Model):
    owner_id = models.IntegerField(blank=True, null=True)
    name_field = models.CharField(db_column='name_', max_length=200, db_collation='utf8_general_ci')  # Field renamed
    # because it ended with '_'.
    email = models.CharField(max_length=200, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    description_field = models.CharField(db_column='description_', max_length=200, db_collation='utf8_general_ci', blank=True, null=True)  # Field renamed because it ended with '_'.
    contact_detail = models.CharField(max_length=200, blank=True, null=True)
    date_created = models.DateTimeField(default=now)
    last_modified = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'Contact'


class CustomUser(models.Model):
    username = models.CharField(max_length=20)
    pass_field = models.CharField(db_column='pass', max_length=16)  # Field renamed because it was a Python reserved
    # word.
    firstname = models.CharField(max_length=50, db_collation='utf8_general_ci')
    lastname = models.CharField(max_length=50, db_collation='utf8_general_ci', blank=True, null=True)
    dob = models.DateTimeField(blank=True, null=True)
    gender = models.CharField(max_length=20, db_collation='utf8_general_ci', blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    last_logged = models.DateTimeField(blank=True, null=True)
    date_created = models.DateTimeField(default=now)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'CustomUser'


class ReminderInstanceException(models.Model):
    reminder_id = models.IntegerField()
    is_edited = models.BooleanField(blank=True, null=True)
    is_deleted = models.BooleanField(blank=True, null=True)
    date_field = models.DateField(db_column='date_')  # Field renamed because it ended with '_'.
    time_field = models.TimeField(db_column='time_', null=True, blank=True)  # Field renamed because it ended with '_'.
    content = models.CharField(max_length=200, db_collation='utf8_general_ci', null=True, blank=True)
    user_id = models.IntegerField(blank=True, null=True)
    date_created = models.DateTimeField(default=now)
    last_modified = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'ReminderInstanceException'


class ScheduleInstanceException(models.Model):
    schedule_id = models.IntegerField()
    is_rescheduled = models.BooleanField(blank=True, null=True)
    is_cancelled = models.BooleanField(blank=True, null=True)
    date_field = models.DateField(db_column='date_')  # Field renamed because it ended with '_'.
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    content = models.CharField(max_length=200, db_collation='utf8_general_ci', blank=True, null=True)
    location = models.CharField(max_length=200, db_collation='utf8_general_ci', blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    date_created = models.DateTimeField(default=now)
    last_modified = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'ScheduleInstanceException'
