# -*- coding: utf-8; -*-

import os
import __main__
from ConfigParser import SafeConfigParser
try:
    from sqlalchemy import create_engine
    from sqlalchemy import MetaData
    from sqlalchemy.orm import sessionmaker
    from models import metadata, sync_db
except ImportError:
    raise Exception("Please install sqlalchemy first to be able to use DB engines!")



class Config(object):

    def __init__(self, ini_file = None):
        self.engine = None
        self.session = None
        self.ini_file = ini_file

    def syncDatabase(self):
        if self.engine is not None:
            print 's'*10, self.engine
            # metadata.create_all(self.engine)
            sync_db(self.engine)


    def getDBEngine(self):
        """
        get DB engine and syncs tables
        """
        if self.ini_file:
            config_filename = self.ini_file
        else:
            try:
                config_filename = os.path.join(os.path.dirname(os.path.abspath(__main__.__file__)), 'langcodes.ini') if hasattr(__main__, '__file__') else None
            except AttributeError:
                config_filename = None
        print 'your script is: %s' % config_filename

        if config_filename and os.path.exists(config_filename) and self.engine is None:
            config = SafeConfigParser()
            config.readfp(open(config_filename, 'rb'))

            use_db = config.get('main', 'use_db')
            if use_db not in ('True', True):
                return None

            db_data = {
                    'db_engine' : config.get('db', 'engine'),
                    'db_host' : config.get('db', 'host'),
                    'db_user' : config.get('db', 'user'),
                    'db_passwd' : config.get('db', 'password'),
                    'db_name' : config.get('db', 'name'),
                    'db_encoding' : config.get('db', 'encoding'),
                    'db_echo' : config.getboolean('db', 'echo'),
                    'db_port' : config.getint('db', 'port'),
                }


            if db_data['db_engine'] == 'postgresql':
                self.engine = create_engine("postgresql://%(db_user)s:%(db_passwd)s@%(db_host)s:%(db_port)s/%(db_name)s" % db_data,
                                    echo = True if db_data['db_echo'] == True else False
                                     )
            elif db_data['db_engine'] == 'mysql':
                self.engine = create_engine("mysql://%(db_user)s:%(db_passwd)s@%(db_host)s/%(db_name)s" % db_data,
                                     encoding = db_data['db_encoding'],
                                     echo = True if db_data['db_echo'] == True else False
                                     )
            else:
                raise Exception("Unknown DB engine (not supported)")

        return self.engine

    def getSession(self):
        if self.session is None:
            self.session = sessionmaker()
            self.session.configure(bind = self.engine)
        return self.session
