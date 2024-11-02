from mysql.connector import connect

"""Used mysql"""

"""1** - connect errors, 2** - ok work functions, 3** and 4** - errors in project"""

status_cod = {100: {"eng": "There is no connection to the database", "ru": "Нет соединения с базой данных"},
              200: {"eng": "it's ok, no error", "ru": "Функция работает корректно, нет ошибок"},
              300: {"ru": "Данный тип атрибута/объекта не поддерживается"},
              301: {"ru": "Таблица уже существует"},
              302: {"ru": "Таблицы не существует"},
              303: {"ru": "Объект уже в таблице"},
              304: {"ru": "Объект не найден"},
              400: {"eng": "Erroneous use of the function", "ru": "Ошибка использования функции"},
              #not used: 401: {"eng": "Erroneous or intentional use of vulnerabilities", "ru": "Ошибочное или намеренное использование уязвимостей"}
              402: {"ru": "Непредвиденная ошибка функции"},
              403: {"ru": "Не поддерживается данной версией программы"}}

class Connection:
    """Used mysql db"""
    def __init__(self, /, *, user, password, database, host='127.0.0.1', port=3306, **kwargs):
        """*for params see 'https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html'*"""
        try:
            self.conn = connect(host=host, port=port, user=user, password=password, database=database, **kwargs)
            self.cur = self.conn.cursor()
            self.notconn = False
        except:
            self.conn = None
            self.cur = None
            self.notconn = True
