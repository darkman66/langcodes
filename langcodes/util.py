import os
import __main__
from pkg_resources import resource_filename
try:
    DATA_ROOT = resource_filename('langcodes', 'data')
except ImportError:
    DATA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__main__.__file__)), 'data')


def data_filename(filename):
    return os.path.join(DATA_ROOT, filename)
