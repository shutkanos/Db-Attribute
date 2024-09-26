from mysql.connector import connect
from _db_info import host, user, password, database

"""Used mysql"""

"""1** - connect errors, 2** - ok work functions, 3** and 4** - errors in project"""

status_cod = {100: {"eng": "There is no connection to the database", "ru": "Нет соединения с базой данных"},
              200: {"eng": "it's ok, no error", "ru": "Функция работает корректно, нет ошибок"},
              300: {"ru": "Данный тип атрибута/объекта не поддерживается"},
              301: {"ru": "Таблица уже существует"},
              302: {"ru": "Таблицы не существует"},
              303: {"ru": "Объект уже в таблице"},
              400: {"eng": "Erroneous use of the function", "ru": "Ошибка использования функции"},
              #not used: 401: {"eng": "Erroneous or intentional use of vulnerabilities", "ru": "Ошибочное или намеренное использование уязвимостей"}
              402: {"ru": "Непредвиденная ошибка функции"},
              403: {"ru": "Не поддерживается данной версией программы"}}

try:
    conn = connect(host=host, user=user, password=password, database=database)
    cur = conn.cursor()
    notconn = False
except:
    conn = None
    cur = None
    notconn = True