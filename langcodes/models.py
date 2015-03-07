import os
import __main__
from ConfigParser import SafeConfigParser
from sqlalchemy import Column, String, MetaData, Text, Table, Integer

metadata = MetaData()

language = Table('language', metadata,
    Column('subtag', Text, primary_key = True),
    Column('script', Text),
    Column('is_macro', Integer),
    Column('is_collection', Integer),
    Column('preferred', Text),
    Column('macrolang', Text)
)
