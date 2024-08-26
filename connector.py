from mysql.connector import connect
from _db_info import host, user, password, database

"""Used mysql"""

errors = {100: {"eng": "There is no connection to the database", "ru": "Нет соединения с базой данных"},
          300: {"ru": "Данный тип атрибута/объекта не поддерживается, смотреть db_work.create_table"},
          400: {"eng": "Erroneous use of the function", "ru": "Ошибка использования функции"},
          401: {"eng": "Erroneous or intentional use of vulnerabilities", "ru": "Ошибочное или намеренное использование уязвимостей"}}

try:
    conn = connect(host=host, user=user, password=password, database=database)
    cur = conn.cursor()
    notconn = False
except:
    conn = None
    cur = None
    notconn = True