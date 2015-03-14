
import json
from util import data_filename
from db_sqlite import LanguageDBsqlite, lazy_property
try:
    from models import NonStandard, Language, LanguageName, NonStandardRegion, ExtLang, Region, ScriptName, RegionName, Variant, VariantName
    from sqlalchemy.orm.exc import NoResultFound
except ImportError:
    print 'no sqlalchemy installed!'

class LanguageDB(LanguageDBsqlite):
    """
    The LanguageDB contains relational data about language subtags. It's
    originally read from a flatfile and .json files using load_subtags.py.
    After that it's available primarily through a SQLite, Postgresql, Mysql databases.

    It uses sqlalchemy for model mapping

    Some information that doesn't fit into the SQL schema is loaded lazily from
    .json files.
    """

    def __init__(self, db_engine):
        if type(db_engine) == str:
            self.initDB(db_engine)
            self.__useSQLalchemy = False
        else:
            self.__useSQLalchemy = True
            self.db_engine = db_engine


    def language_replacements(self, macro = False):
        if self.__useSQLalchemy == True:
            session = self.db_engine.getSession()()
            out = session.query(NonStandard).filter(NonStandard.is_macro == macro, NonStandard.preferred != None)
            session.close()
            return [(x.tag, x.preferred) for x in out]
        return None


    def list_macrolanguages(self):
        if self.__useSQLalchemy == True:
            session = self.db_engine.getSession()()
            out = session.query(Language).filter(Language.macrolang != None)
            session.close()
            return [(x.subtag, x.macrolang) for x in out]
        return None

    def region_replacements(self):
        if self.__useSQLalchemy == True:
            session = self.db_engine.getSession()()
            out = session.query(NonStandardRegion).filter(NonStandardRegion.preferred != None)
            session.close()
            return [(x.tag, x.preferred) for x in out]
        return self._region_replacements()


    def add_script(self, data, datalang):
        if self.__useSQLalchemy == True:
            session = self.db_engine.getSession()()
            subtag = data['Subtag']
            for i, name in enumerate(data['Description']):
                self.__addScriptName(session, subtag, datalang, name, i)
            session.close()
        else:
            self._add_script(data, datalang)


    def __addScriptName(self, session, subtag, datalang, name, entry_order, make_commit = False):
        try:
            session.query(ScriptName).filter_by(subtag = subtag).one()
        except NoResultFound:
            session.add(ScriptName(subtag = subtag, language = datalang, name = name, entry_order = entry_order))
            if make_commit == True:
                session.commit()


    def add_extlang(self, data, _datalang):
        session = self.db_engine.getSession()()
        subtag = data['Subtag']
        prefixes = ';'.join(data.get('Prefix', '*'))
        try:
            session.query(ExtLang).filter_by(subtag = subtag)
        except NoResultFound:
            o = ExtLang(subtag = subtag, prefixes = prefixes)
            session.add(o)
            session.commit()
            session.close()

    def add_language(self, data, datalang):
        session_get = self.db_engine.getSession()()
        subtag = data['Subtag']
        script = data.get('Suppress-Script')
        is_macro = 'Macrolanguage' in data
        is_collection = (data.get('Scope') == 'collection')
        preferred = data.get('Preferred-Value')
        macrolang = data.get('Macrolanguage')

        session = self.db_engine.getSession()()
        try:
            session_get.query(Language).filter_by(subtag = subtag).one()
        except NoResultFound:
            session.add(Language(subtag = subtag, script = script, is_macro = is_macro,
                            is_collection = is_collection, preferred = preferred,
                            macrolang = macrolang))
        session.commit()
        session.close()

        session = self.db_engine.getSession()()

        for i, name in enumerate(data['Description']):
            self.__addLanguageName(session, subtag, datalang, name, i)
        session.commit()
        session.close()
        session_get.close()


    def __addLanguageName(self, session, subtag, language, name, entry_order, make_commit = False):
        """
        adding LanguageName field
        """
        try:
            session.query(LanguageName).filter_by(subtag = subtag).one()
        except NoResultFound:
            session.add(LanguageName(subtag = subtag, language = language, name = name, entry_order = entry_order))
            if make_commit == True:
                session.commit()


    def add_language_mapping(self, tag, desc, preferred, is_macro):
        session = self.db_engine.getSession()()
        try:
            session.query(NonStandard).filter_by(tag = tag).one()
        except NoResultFound:
            session.add(NonStandard(tag = tag, description = desc, preferred = preferred, is_macro = is_macro))
            session.commit()
        session.close()


    def add_region_mapping(self, tag, preferred):
        self.add_language_mapping(tag, None, preferred, False)


    def addNameBasedOnTableName(self, type_name, subtag, langcode, name, order):
        """
        adding items based on dynamic table name
        """
        if self.__useSQLalchemy == True:
            session = self.db_engine.getSession()()
            if type_name == 'language':
                self.__addLanguageName(session, subtag, langcode, name, order, True)
            elif type_name == 'variant':
                self.__variantName(session, subtag, langcode, name, order, True)
            elif type_name == 'script':
                self.__addScriptName(session, subtag, langcode, name, order, True)
            elif type_name == 'region':
                self.__addRegionName(session, subtag, langcode, name, order, True)
            else:
                print("Ignoring type: %s" % type_name)
            session.close()


    def add_region(self, data, datalang):
        session = self.db_engine.getSession()()
        subtag = data['Subtag']
        deprecated = 'Deprecated' in data
        preferred = data.get('Preferred-Value')
        try:
            session.query(Region).filter_by(subtag = subtag).one()
        except NoResultFound:
            session.add(Region(subtag = subtag, deprecated = deprecated, preferred = preferred))
            session.commit()

        for i, name in enumerate(data['Description']):
            self.__addRegionName(session, subtag, datalang, name, i)
        session.commit()
        session.close()


    def __addRegionName(self, session, subtag, datalang, name, entry_order, make_commit = False):
        try:
            session.query(RegionName).filter_by(subtag = subtag).one()
        except NoResultFound:
            session.add(RegionName(subtag = subtag, language = datalang, name = name, entry_order = entry_order))
            if make_commit == True:
                session.commit()


    def add_variant(self, data, datalang):
        session = self.db_engine.getSession()()
        subtag = data['Subtag']
        prefixes = ';'.join(data.get('Prefix', '*'))
        try:
            session.query(Variant).filter_by(subtag = subtag).one()
        except NoResultFound:
            session.add(Variant(subtag = subtag, prefixes = prefixes))
        session.commit()


        for i, name in enumerate(data['Description']):
            self.__variantName(session, subtag, datalang, name, i)
        session.commit()
        session.close()

    def __variantName(self, session, subtag, datalang, name, entry_order, make_commit = False):
        try:
            session.query(VariantName).filter_by(subtag = subtag).one()
        except NoResultFound:
            session.add(VariantName(subtag = subtag, language = datalang, name = name, entry_order = entry_order))
            if make_commit == True:
                session.commit()

    def setup(self):
        if self.__useSQLalchemy == True:
            pass
        else:
            self._setup()


    def __str__(self):
        return "LanguageDB(%s) sqlalchemy: %s" % (self.db_engine, self.__useSQLalchemy)


    def close(self):
        """
        Just to cover old DB close method, if sqlalchemy is not used let's work as it was
        """
        pass


    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
