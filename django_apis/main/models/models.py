# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class MySchedule(models.Model):
    date_field = models.DateField(db_column='date_', blank=True, null=True)  # Field renamed because it ended with '_'.
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    content = models.CharField(max_length=200, db_collation='utf8_general_ci', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'MySchedule'


class Reminder(models.Model):
    date_field = models.DateField(db_column='date_', blank=True, null=True)  # Field renamed because it ended with '_'.
    time_field = models.TimeField(db_column='time_', blank=True, null=True)  # Field renamed because it ended with '_'.
    content = models.CharField(max_length=200, db_collation='utf8_general_ci', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Reminder'


class Appointment(models.Model):
    date_field = models.DateField(db_column='date_', blank=True, null=True)  # Field renamed because it ended with '_'.
    time_field = models.TimeField(db_column='time_', blank=True, null=True)  # Field renamed because it ended with '_'.
    content = models.CharField(max_length=200, db_collation='utf8_general_ci', blank=True, null=True)
    person = models.CharField(max_length=100, db_collation='utf8_general_ci', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Appointment'


class Alarm(models.Model):
    date_field = models.DateField(db_column='date_', blank=True, null=True)  # Field renamed because it ended with '_'.
    time_field = models.TimeField(db_column='time_', blank=True, null=True)  # Field renamed because it ended with '_'.
    redo_after = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'Alarm'
