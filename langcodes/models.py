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


extlang = Table('extlang', metadata,
    Column('subtag', Text, primary_key = True),
    Column('prefixes', Text)
)
language_name = Table('language_name',metadata,
    Column('subtag', Text, primary_key = True),
    Column('language', Text),
    Column('name', Text),
    Column('entry_order', Integer)
)

nonstandard = Table('nonstandard', metadata,
    Column('tag', Text, primary_key = True),
    Column('description', Text),
    Column('preferred', Text),
    Column('is_macro', Integer)
)

nonstandard_region = Table('nonstandard_region', metadata,
    Column('subtag',Text, primary_key = True),
    Column('preferred', Text)
)

region = Table('region', metadata,
    Column('subtag', Text, primary_key = True),
    Column('deprecated', Integer),
    Column('preferred', Text)
)

region_name = Table('region_name', metadata,
    Column('subtag', Text, primary_key = True),
    Column('language', Text),
    Column('name', Text),
    Column('entry_order', Integer)
)

# we have no useful information about scripts except their name
script_name = Table('script_name', metadata,
    Column('subtag',Text, primary_key = True),
    Column('language', Text),
    Column('name', Text),
    Column('entry_order', Integer)
)

# was there a reason variants saved their comments?
variant = Table('variant', metadata,
    Column('subtag',Text, primary_key = True),
    Column('prefixes', Text)
)

variant_name = Table('variant_name', metadata,
    Column('subtag',Text, primary_key = True),
    Column('language', Text),
    Column('name', Text),
    Column('entry_order', Integer)
)
