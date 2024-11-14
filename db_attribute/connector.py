from mysql.connector import connect

"""Used mysql"""

"""1** - connect errors, 2** - ok work functions, 3** and 4** - errors in project"""

status_cod = {100: {"eng": "There is no connection to the database", "ru": "Нет соединения с базой данных"},
              200: {"eng": "it's ok, no error", "ru": "Функция работает корректно, нет ошибок"},
              300: {"eng": "This attribute / object type is not supported", "ru": "Данный тип атрибута/объекта не поддерживается"},
              301: {"eng": "The table already exists", "ru": "Таблица уже существует"},
              302: {"eng": "The table doesn't exist", "ru": "Таблицы не существует"},
              303: {"eng": "The object is already in the table", "ru": "Объект уже находится в таблице"},
              304: {"eng": "Object not found", "ru": "Объект не найден"},
              400: {"eng": "Erroneous use of the function", "ru": "Ошибка использования функции"},
              402: {"eng": "Unexpected function error", "ru": "Непредвиденная ошибка функции"},
              403: {"eng": "Not supported by this version of the program", "ru": "Не поддерживается данной версией программы"}}

class Connection:
    """Used mysql db"""
    def __init__(self, /, *, host='127.0.0.1', port=3306, user, password, database, **kwargs):
        """*for params see 'https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html'*"""
        try:
            self.conn = connect(host=host, port=port, user=user, password=password, database=database, **kwargs)
            self.cur = self.conn.cursor()
            self.notconn = False
        except:
            self.conn = None
            self.cur = None
            self.notconn = True
