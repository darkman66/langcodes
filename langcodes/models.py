import __main__
from ConfigParser import SafeConfigParser
from sqlalchemy import Column, String, MetaData, Text, Table, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
Base = declarative_base()

def sync_db(engine):
    Base.metadata.create_all(engine)

class Language(Base):
    __tablename__ = 'language'
    subtag = Column(Text, primary_key = True)
    script = Column(Text)
    is_macro = Column(Boolean)
    is_collection = Column(Boolean)
    preferred = Column(Text)
    macrolang = Column(Text)



class ExtLang(Base):
    __tablename__ = 'extlang'
    subtag = Column(Text, primary_key = True)
    prefixes = Column(Text)


class LanguageName(Base):
    __tablename__ = 'language_name'
    subtag = Column(Text, primary_key = True)
    language = Column(Text)
    name = Column(Text)
    entry_order = Column(Integer)


class NonStandard(Base):
    __tablename__ = 'nonstandard'
    tag = Column(Text, primary_key = True)
    description = Column(Text)
    preferred = Column(Text)
    is_macro = Column(Boolean)


class NonStandardRegion(Base):
    __tablename__ = 'nonstandard_region'
    subtag = Column(Text, primary_key = True)
    preferred = Column(Text)


class Region(Base):
    __tablename__ = 'region'
    subtag = Column(Text, primary_key = True)
    deprecated = Column(Boolean)
    preferred = Column(Text)


class RegionName(Base):
    __tablename__ = 'region_name'
    subtag = Column(Text, primary_key = True)
    language = Column(Text)
    name = Column(Text)
    entry_order = Column(Integer)


# we have no useful information about scripts except their name
class ScriptName(Base):
    __tablename__ = 'script_name'
    subtag = Column(Text, primary_key = True)
    language = Column(Text)
    name = Column(Text)
    entry_order = Column(Integer)


# was there a reason variants saved their comments?
class Variant(Base):
    __tablename__ = 'variant'
    subtag = Column(Text, primary_key = True)
    prefixes = Column(Text)


class VariantName(Base):
    __tablename__ = 'variant_name'
    subtag = Column(Text, primary_key = True)
    language = Column(Text)
    name = Column(Text)
    entry_order = Column(Integer)
