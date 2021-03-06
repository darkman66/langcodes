import sqlite3
import json
import threading
from util import data_filename


class lazy_property(object):
    """
    A lazy_property decorator from StackOverflow:
    http://stackoverflow.com/a/6849299/773754
    """

    def __init__(self, fget):
        self.fget = fget
        self.func_name = fget.__name__

    def __get__(self, obj, cls):
        print '>'*20, obj
        if obj is None:
            return None
        value = self.fget(obj)
        setattr(obj, self.func_name, value)
        return value


class LanguageDBsqlite(object):
    """
    The LanguageDB contains relational data about language subtags. It's
    originally read from a flatfile and .json files using load_subtags.py.
    After that it's available primarily through a SQLite database.

    Some information that doesn't fit into the SQL schema is loaded lazily from
    .json files.
    """

    TABLES = [
        """CREATE TABLE IF NOT EXISTS language(
            subtag TEXT PRIMARY KEY COLLATE NOCASE,
            script TEXT NULL,
            is_macro INTEGER,
            is_collection INTEGER,
            preferred TEXT,
            macrolang TEXT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS extlang(
            subtag TEXT PRIMARY KEY COLLATE NOCASE,
            prefixes TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS language_name(
            subtag TEXT COLLATE NOCASE,
            language TEXT COLLATE NOCASE,
            name TEXT COLLATE NOCASE,
            entry_order INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS nonstandard(
            tag TEXT PRIMARY KEY COLLATE NOCASE,
            description TEXT,
            preferred TEXT NULL,
            is_macro INTEGER
        )""",
        """CREATE TABLE IF NOT EXISTS nonstandard_region(
            tag TEXT PRIMARY KEY COLLATE NOCASE,
            preferred TEXT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS region(
            subtag TEXT PRIMARY KEY COLLATE NOCASE,
            deprecated INTEGER,
            preferred TEXT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS region_name(
            subtag TEXT COLLATE NOCASE,
            language TEXT COLLATE NOCASE,
            name TEXT COLLATE NOCASE,
            entry_order INTEGER
        )""",
        # we have no useful information about scripts except their name
        """CREATE TABLE IF NOT EXISTS script_name(
            subtag TEXT COLLATE NOCASE,
            language TEXT COLLATE NOCASE,
            name TEXT COLLATE NOCASE,
            entry_order INTEGER
        )""",
        # was there a reason variants saved their comments?
        """CREATE TABLE IF NOT EXISTS variant(
            subtag TEXT PRIMARY KEY COLLATE NOCASE,
            prefixes TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS variant_name(
            subtag TEXT COLLATE NOCASE,
            language TEXT COLLATE NOCASE,
            name TEXT COLLATE NOCASE,
            entry_order INTEGER
        )""",
        """CREATE VIEW IF NOT EXISTS macrolanguages AS
            SELECT DISTINCT macrolang FROM language where macrolang is not NULL""",
    ]
    NAMES_TO_INDEX = ['language_name', 'region_name', 'script_name', 'variant_name']
    condition = threading.Condition()

    def initDB(self, db_filename):
        print 'f'*10, db_filename
        self.filename = db_filename

        with self.condition:
            self.conn = sqlite3.connect(db_filename, check_same_thread=False)
            self.condition.notifyAll()


    def __str__(self):
        return "LanguageDB(%s)" % self.filename

    # Methods for initially creating the schema
    # =========================================

    def _setup(self):
        print 'setup-'*10
        with self.condition:
            for stmt in self.TABLES:
                self.conn.execute(stmt)
            self._make_indexes()
            self.condition.notifyAll()


    def _make_indexes(self):
        with self.condition:
            for table_name in self.NAMES_TO_INDEX:
                self.conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS {0}_uniq ON {0}(subtag, language, name)".format(table_name)
                )
                self.conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS {0}_lookup ON {0}(subtag, language, name)".format(table_name)
                )
            self.condition.notifyAll()



    def _add_row(self, table_name, values):
        """
        Methods for building the database
        """
        tuple_template = ', '.join(['?'] * len(values))
        template = "INSERT OR IGNORE INTO %s VALUES (%s)" % (table_name, tuple_template)
        # I know, right? The sqlite3 driver doesn't let you parameterize the
        # table name. Good thing little Bobby Tables isn't giving us the names.
        with self.condition:
            self.conn.execute(template, values)
            self.condition.notifyAll()


    def _add_name(self, table, subtag, datalang, name, i):
        self._add_row('%s_name' % table, (subtag, datalang, name, i))

    def _add_language(self, data, datalang):
        subtag = data['Subtag']
        script = data.get('Suppress-Script')
        is_macro = 'Macrolanguage' in data
        is_collection = (data.get('Scope') == 'collection')
        preferred = data.get('Preferred-Value')
        macrolang = data.get('Macrolanguage')

        self._add_row(
            'language',
            (subtag, script, is_macro, is_collection, preferred, macrolang)
        )
        for i, name in enumerate(data['Description']):
            self.add_name('language', subtag, datalang, name, i)

    def _add_extlang(self, data, _datalang):
        subtag = data['Subtag']
        prefixes = ';'.join(data.get('Prefix', '*'))
        self._add_row('extlang', (subtag, prefixes))

    def add_nonstandard(self, data, _datalang):
        tag = data['Tag']
        desc = ';'.join(data.get('Description'))
        preferred = data.get('Preferred-Value')
        self.add_language_mapping(tag, desc, preferred, False)

    def _add_language_mapping(self, tag, desc, preferred, is_macro):
        self._add_row('nonstandard', (tag, desc, preferred, is_macro))

    def _add_region(self, data, datalang):
        subtag = data['Subtag']
        deprecated = 'Deprecated' in data
        preferred = data.get('Preferred-Value')

        self._add_row('region', (subtag, deprecated, preferred))
        for i, name in enumerate(data['Description']):
            self.add_name('region', subtag, datalang, name, i)

    def _add_region_mapping(self, tag, preferred):
        self._add_row('nonstandard_region', (tag, preferred))

    def _add_script(self, data, datalang):
        subtag = data['Subtag']
        for i, name in enumerate(data['Description']):
            self.add_name('script', subtag, datalang, name, i)

    def _add_variant(self, data, datalang):
        subtag = data['Subtag']
        prefixes = ';'.join(data.get('Prefix', '*'))
        self._add_row('variant', (subtag, prefixes))

        for i, name in enumerate(data['Description']):
            self.add_name('variant', subtag, datalang, name, i)

    # Iterating over things in the database
    # =====================================

    def query(self, query, *args):
        with self.condition:
            c = self.conn.cursor()
            c.execute(query, args)
            out = c.fetchall()
            self.condition.notifyAll()
        return out

    def _list_macrolanguages(self):
        return self.query(
            "select subtag, macrolang from language "
            "where macrolang is not null"
        )

    def _language_replacements(self, macro=False):
        return self.query(
            "select tag, preferred from nonstandard where is_macro=? "
            "and preferred is not null", macro
        )

    def _region_replacements(self):
        return self.query(
            "select tag, preferred from nonstandard_region "
            "where preferred is not null"
        )

    def _list_suppressed_scripts(self):
        return self.query(
            "select subtag, script from language "
            "where script is not null"
        )

    # Looking up names of things
    # ==========================

    def names_for(self, table_name, subtag):
        results = {}
        items = self.query(
            ("select language, name from {}_name "
             "where subtag == ? order by subtag, language, entry_order"
             .format(table_name)), subtag
        )
        for language, name in items:
            if language not in results:
                results[language] = name
        return results

    def lookup_name(self, table_name, name, language):
        """
        Given a table name ('language', 'script', 'region', or 'variant'),
        map a name of one of those things to a code.

        Returns a list of matching codes, which there should be 0 or 1 of.
        """
        return [row[0] for row in self.query(
            "select subtag from {}_name where language == ? and "
            "name == ?".format(table_name),
            language, name
        )]

    def lookup_name_in_any_language(self, table_name, name):
        return [row for row in self.query(
            "select subtag, language from {}_name where name == ? "
            .format(table_name),
            name
        )]

    def lookup_name_prefix(self, table_name, name, language):
        """
        Given a table name ('language', 'script', 'region', or 'variant'),
        map a prefix of a name of one of those things to a code.

        Returns a list of matching codes, which there may be more than one of
        in case of ambiguity.
        """
        return self.query(
            "select subtag, name from {}_name where language == ? and "
            "(name == ? or name like ?)".format(table_name),
            language, name, name + '%'
        )

    # Cached dictionaries of information
    # ==================================

    @lazy_property
    def normalized_languages(self):
        """
        Non-standard codes that should be unconditionally replaced.
        """
        results = {orig.lower(): new.lower()
                   for (orig, new) in self.language_replacements()}

        # one more to handle the 'root' locale
        results['root'] = 'und'
        return results

    @lazy_property
    def normalized_macrolanguages(self):
        """
        Codes that the Unicode Consortium would rather replace with macrolanguages.
        """
        return {
            orig.lower(): new
            for (orig, new) in self.language_replacements(macro=True)
        }

    @lazy_property
    def macrolanguages(self):
        """
        Mappings for all languages that have macrolanguages.
        """
        return {lang: macro for (lang, macro) in self.list_macrolanguages()}

    @lazy_property
    def normalized_regions(self):
        """
        Regions that have been renamed, merged, or re-coded. (This package doesn't
        handle the ones that have been split, like Yugoslavia.)
        """
        return {
            orig.upper(): new.upper()
            for (orig, new) in self.region_replacements()
        }

    @lazy_property
    def default_scripts(self):
        """
        Most languages imply a particular script that they should be written in.
        This data is used by the `assume_script` and `simplify_script` methods.
        """
        return {
            lang: script
            for (lang, script) in self.list_suppressed_scripts()
        }

    @lazy_property
    def parent_locales(self):
        """
        CLDR's list of which locales are "parents" of other locales.
        """
        pl_json = json.load(
            open(data_filename('cldr/supplemental/parentLocales.json'))
        )
        return pl_json['supplemental']['parentLocales']['parentLocale']

    @lazy_property
    def likely_subtags(self):
        """
        Information on which subtag values are most likely given other subtags.
        """
        ls_json = json.load(
            open(data_filename('cldr/supplemental/likelySubtags.json'))
        )
        return ls_json['supplemental']['likelySubtags']

    @lazy_property
    def language_matching(self):
        """
        Information about the strength of match between certain pairs of
        languages.
        """
        match_json = json.load(
            open(data_filename('cldr/supplemental/languageMatching.json'))
        )
        matches = {}
        match_data = match_json['supplemental']['languageMatching']['written']
        for item in match_data:
            match = item['languageMatch']
            desired = match['_desired']
            supported = match['_supported']
            value = match['_percent']
            if (desired, supported) not in matches:
                matches[(desired, supported)] = int(value)
            if match.get('_oneway') != 'true':
                if (supported, desired) not in matches:
                    matches[(supported, desired)] = int(value)
        return matches


    def close(self):
        """
        Using the database as a context manager
        """
        with self.condition:
            self.conn.commit()
            self.conn.close()
            self.condition.notifyAll()


    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
