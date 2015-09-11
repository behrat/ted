# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models
from positional import PositionalSortMixIn

class Output(PositionalSortMixIn, models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class OutputChannel(models.Model):
    output = models.ForeignKey(Output, null=True, blank=True)
    jack_client = models.CharField(max_length=255)
    jack_port = models.CharField(max_length=255)

    def __unicode__(self):
        return self.jack_client + ":" + self.jack_port

class Input(PositionalSortMixIn, models.Model):
    name = models.CharField(max_length=255)
    local_out = models.ForeignKey(Output, unique=True, null=True)

    def __unicode__(self):
        return self.name

class InputChannel(models.Model):
    input = models.ForeignKey(Input, null=True, blank=True)
    jack_client = models.CharField(max_length=255)
    jack_port = models.CharField(max_length=255)

