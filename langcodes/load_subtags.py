# -*- coding: utf-8; -*-

import json
import sys
from config import Config
from registry_parser import parse_registry
from db import LanguageDB
from util import data_filename
from pathlib import Path



def load_registry(db, registry_data, datalang='en'):
    for item in registry_data:
        typ = item['Type']
        if typ == 'language':
            db.add_language(item, datalang)
        elif typ == 'extlang':
            db.add_extlang(item, datalang)
        elif typ in {'grandfathered', 'redundant'}:
            db.add_nonstandard(item, datalang)
        elif typ == 'region':
            db.add_region(item, datalang)
        elif typ == 'script':
            db.add_script(item, datalang)
        elif typ == 'variant':
            db.add_variant(item, datalang)
        else:
            print("Ignoring type: %s" % typ)


def load_cldr_file(db, typ, langcode, path):
    data = json.load(path.open(encoding='utf-8'))
    closer = data['main'][langcode]['localeDisplayNames']
    for actual_data in closer.values():
        for subtag, name in actual_data.items():
            order = 1
            if '-alt-' in subtag:
                subtag, _ = subtag.split('-alt-', 1)
                order = 2
            if typ == 'variant':
                subtag = subtag.lower()

            db.addNameBasedOnTableName(typ, subtag, langcode, name, order)


def load_cldr_aliases(db, path):
    data = json.load(path.open(encoding='utf-8'))
    lang_aliases = data['supplemental']['metadata']['alias']['languageAlias']
    for subtag, value in lang_aliases.items():
        if '_replacement' in value:
            preferred = value['_replacement']
            is_macro = value['_reason'] == 'macrolanguage'
            db.add_language_mapping(subtag, None, preferred, is_macro)
    region_aliases = data['supplemental']['metadata']['alias']['territoryAlias']
    for subtag, value in region_aliases.items():
        if '_replacement' in value:
            preferred = value['_replacement']
            if ' ' in preferred:
                # handling regions that have split up is a difficult detail that
                # we don't care to implement yet
                preferred = None
            db.add_region_mapping(subtag, preferred)


def load_bibliographic_aliases(db, path):
    for line in path.open(encoding='utf-8'):
        biblio, preferred, name = line.rstrip().split(',', 2)
        desc = '%s (bibliographic code)' % name
        db.add_language_mapping(biblio, desc, preferred, False)


def load_cldr(db, cldr_path):
    main_path = cldr_path / 'main'
    for subpath in main_path.iterdir():
        if subpath.is_dir() and (subpath / 'languages.json').exists():
            langcode = subpath.name
            load_cldr_file(db, 'language', langcode, subpath / 'languages.json')
            load_cldr_file(db, 'region', langcode, subpath / 'territories.json')
            load_cldr_file(db, 'script', langcode, subpath / 'scripts.json')
            load_cldr_file(db, 'variant', langcode, subpath / 'variants.json')
    load_cldr_aliases(db, cldr_path / 'supplemental' / 'metadata.json')


def do_setup(db):
    db.setup()
    load_registry(db, parse_registry(), 'en')
    load_cldr(db, Path(data_filename('cldr')))
    load_bibliographic_aliases(db, Path(data_filename('bibliographic_codes.csv')))

def main(db_filename = None):
    # Create the database
    with LanguageDB(db_filename) as db:
        do_setup(db)

def sync_with_sqlalchemy(ini_file = None):
    # lets try to specify ini file if its available
    db_engine = Config(ini_file)
    if db_engine.getDBEngine():
        db_engine.syncDatabase()
        db = LanguageDB(db_engine)
        do_setup(db)
    else:
        print 'Nothing will happen! Neither ini file nor attribute for script specified'


if __name__ == '__main__':
    db_filename = sys.argv[1] if len(sys.argv) > 1 else None
    if db_filename and 'ini' not in db_filename:
        print 'Using SQLalchemy as default storage'
        main(db_filename)
    else:
        sync_with_sqlalchemy(db_filename)
