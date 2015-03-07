import sqlite3

conn = sqlite3.connect('langcodes/data/subtags.db', detect_types = sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

c = conn.cursor()
c.execute("select count(*) from language_name")

print '>>', c.fetchall()
