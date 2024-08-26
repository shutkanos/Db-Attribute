from mysql.connector import connect
from _db_info import host, user, password, database

try:
    conn = connect(host=host, user=user, password=password, database=database)
    cur = conn.cursor()
    notconn = False
except:
    conn = None
    cur = None
    notconn = True