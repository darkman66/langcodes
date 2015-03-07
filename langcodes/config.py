
import os
import __main__
from ConfigParser import SafeConfigParser
from .models import language, metadata
try:
    from sqlalchemy import create_engine
    from sqlalchemy import MetaData
except ImportError:
    raise Exception("Please install sqlalchemy first to be able to use DB engines!")



class Config(object):

    def __init__(self):
        self.engine = None

    def syncDatabase(self):
        if self.engine:
            metadata.create_all(self.engine)


    def getDBEngine(self):
        """
        get DB engine and syncs tables
        """
        config_filename = os.path.join(os.path.dirname(os.path.abspath(__main__.__file__)), 'langcodes.ini')
        print 'your script is: %s' % config_filename

        if os.path.exists(config_filename):
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
                    'db_echo' : config.get('db', 'echo'),
                    'db_port' : config.get('db', 'port'),
                }



            if db_data['db_engine'] == 'postgresql':
                self.engine = create_engine("postgresql://%(db_user)s:%(db_passwd)s@%(db_host)s:%(db_port)s/%(db_name)s" % db_data,
                                    echo = True if db_data['db_echo'] else False
                                     )
            elif db_data['db_engine'] == 'mysql':
                self.engine = create_engine("mysql://%(db_user)s:%(db_passwd)s@%(db_host)s/%(db_name)s" % db_data,
                                     encoding = db_data['db_encoding'],
                                     echo = True if db_data['db_echo'] else False
                                     )
            else:
                raise Exception("Unknown DB engine (not supported)")

        return self.engine
