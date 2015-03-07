
"""
extension to lang-codes which allows you to use redis instead of sqlite
which means that the code is thread safe and much mihc faster
"""
from .db import LanguageDB


class LanguageDBRedis(LanguageDB):

    def __init__(self):
        pass


