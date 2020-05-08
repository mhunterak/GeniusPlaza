"""
MODELS

Relational database models for a URL Shortener
"""
from datetime import datetime as dt
import hashlib
import time
import urllib

from peewee import *

# Designate the database type here
DATABASE = SqliteDatabase(None)


class URL(Model):
    '''
    The model for the urls being shortened.
    '''
    # the hash of the url, can be set to custom
    hashstr = CharField(max_length=32, unique=True)
    # the link where the user is redirected
    link = CharField(max_length=256)
    # the date the link was created
    created = DateField(default=dt.now)

    class Meta:
        database = DATABASE


class Visit(Model):
    '''
    The model holding the record of a link being accessed
    '''
    # date the link was visited
    date = DateField(default=dt.now)
    # the url that was accessed (the model, not the actual link)
    url = ForeignKeyField(URL, related_name='visit')

    class Meta:
        database = DATABASE


def initialize():
    DATABASE.init('DB.sqlite')
    DATABASE.connect()
    DATABASE.create_tables(
        [URL, Visit],
        safe=True)
    DATABASE.close()
