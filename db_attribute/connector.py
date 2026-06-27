"""1** - connect errors, 2** - ok work functions, 3** and 4** - errors in project"""

status_cod = {100: {"eng": "There is no connection to the database", "ru": "Нет соединения с базой данных"},
              200: {"eng": "it's ok, no error", "ru": "Функция работает корректно, нет ошибок"},
              300: {"eng": "This attribute / object type is not supported", "ru": "Данный тип атрибута/объекта не поддерживается"},
              301: {"eng": "The table already exists", "ru": "Таблица уже существует"},
              302: {"eng": "The table doesn't exist", "ru": "Таблицы не существует"},
              303: {"eng": "The object is already in the table", "ru": "Объект уже находится в таблице"},
              304: {"eng": "Object not found", "ru": "Объект не найден"},
              305: {"eng": "The object argument has neither a default value nor a value in the database.", "ru": "Аргумент объекта не имеет ни значения по умолчанию, ни значения в database."},
              306: {"eng": "Cheaker don't support this class (when loaded from db)"},
              400: {"eng": "Erroneous use of the function", "ru": "Ошибка использования функции"},
              402: {"eng": "Unexpected function error", "ru": "Непредвиденная ошибка функции"},
              403: {"eng": "Not supported by this version of the program", "ru": "Не поддерживается данной версией программы"}}


class MySQLDialect:
    """SQL dialect for MySQL."""

    sql_name = 'MySQL'

    def quote(self, name: str) -> str:
        return f'`{name}`'

    def show_tables_sql(self) -> str:
        return "SHOW TABLES"

    def create_table_sql(self, quoted_table: str, col_defs: str) -> str:
        """col_defs — already-built column fragment, e.g. 'data VARCHAR(50)'"""
        sep = ', ' if col_defs else ''
        return f"CREATE TABLE {quoted_table} (id BIGINT PRIMARY KEY AUTO_INCREMENT{sep}{col_defs})"

    def upsert_data_sql(self, quoted_table: str, id_: int, value: str) -> str:
        return (
            f"INSERT IGNORE INTO {quoted_table} (id, data) VALUES ({id_}, {value}) "
            f"ON DUPLICATE KEY UPDATE data=VALUES(data)"
        )

    def upsert_id_sql(self, quoted_table: str, id_: int) -> str:
        return (
            f"INSERT INTO {quoted_table} (id) VALUES ({id_}) "
            f"ON DUPLICATE KEY UPDATE id=VALUES(id)"
        )

    def new_id_sql(self, quoted_table: str) -> str:
        return f"INSERT INTO {quoted_table} () VALUES ()"

    def json_col_type(self) -> str:
        return 'json'

    def bool_col_type(self) -> str:
        return 'BOOL'

    def json_cast(self, json_literal: str) -> str:
        """Wrap a JSON string literal for use as a JSON column value."""
        return f'CAST({json_literal} AS JSON)'

    def quote_string_literal(self, s: str) -> str:
        """Wrap a string value as an SQL string literal safe for WHERE clauses."""
        # MySQL: use double-quoted strings (already the default from json.dumps)
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

    def upsert_data_param_sql(self, quoted_table: str, id_: int, param_value) -> tuple:
        """
        Return (sql, args) for a parameterised upsert.
        MySQL uses %s placeholders.
        """
        sql = (
            f"INSERT INTO {quoted_table} (id, data) VALUES ({id_}, %s) "
            f"ON DUPLICATE KEY UPDATE data=VALUES(data)"
        )
        return sql, (param_value,)

    def is_table_not_found_error(self, exc: Exception) -> bool:
        from mysql.connector import errorcode
        return getattr(exc, 'errno', None) == errorcode.ER_NO_SUCH_TABLE

    def json_extract_d_or_whole(self, json_expr: str) -> str:
        """
        Extract '$.d' from a JSON expression if it exists, otherwise return the whole JSON.
        For use in WHERE clauses when comparing DbClass values.

        :param json_expr: SQL expression that evaluates to JSON (e.g., column name or JSON literal)
        :return: SQL expression that extracts $.d if present, else the whole value
        """
        # MySQL: CASE WHEN JSON_CONTAINS_PATH(expr, 'one', '$.d') THEN JSON_UNQUOTE(JSON_EXTRACT(expr, '$.d')) ELSE expr END
        return f"CASE WHEN JSON_CONTAINS_PATH({json_expr}, 'one', '$.d') THEN JSON_UNQUOTE(JSON_EXTRACT({json_expr}, '$.d')) ELSE {json_expr} END"


class SQLiteDialect:
    """SQL dialect for SQLite."""

    sql_name = 'SQLite'

    def quote(self, name: str) -> str:
        return f'"{name}"'

    def show_tables_sql(self) -> str:
        return "SELECT name FROM sqlite_master WHERE type='table'"

    def create_table_sql(self, quoted_table: str, col_defs: str) -> str:
        sep = ', ' if col_defs else ''
        # SQLite requires INTEGER (not BIGINT) for rowid alias + AUTOINCREMENT
        return f"CREATE TABLE {quoted_table} (id INTEGER PRIMARY KEY AUTOINCREMENT{sep}{col_defs})"

    def upsert_data_sql(self, quoted_table: str, id_: int, value: str) -> str:
        return f"INSERT OR REPLACE INTO {quoted_table} (id, data) VALUES ({id_}, {value})"

    def upsert_id_sql(self, quoted_table: str, id_: int) -> str:
        return f"INSERT OR IGNORE INTO {quoted_table} (id) VALUES ({id_})"

    def new_id_sql(self, quoted_table: str) -> str:
        return f"INSERT INTO {quoted_table} DEFAULT VALUES"

    def json_col_type(self) -> str:
        # SQLite has no native JSON column type; TEXT stores JSON strings fine
        return 'TEXT'

    def bool_col_type(self) -> str:
        return 'INTEGER'

    def json_cast(self, json_literal: str) -> str:
        # No CAST needed — SQLite stores JSON as plain TEXT
        return json_literal

    def quote_string_literal(self, s: str) -> str:
        """Wrap a string value as an SQL string literal safe for WHERE clauses."""
        # SQLite: single-quoted strings; escape inner single quotes by doubling
        escaped = s.replace("'", "''")
        return f"'{escaped}'"

    def upsert_data_param_sql(self, quoted_table: str, id_: int, param_value) -> tuple:
        """
        Return (sql, args) for a parameterised upsert.
        SQLite uses ? placeholders.
        """
        sql = f"INSERT OR REPLACE INTO {quoted_table} (id, data) VALUES ({id_}, ?)"
        return sql, (param_value,)

    def is_table_not_found_error(self, exc: Exception) -> bool:
        import sqlite3
        return isinstance(exc, sqlite3.OperationalError) and 'no such table' in str(exc).lower()

    def json_extract_d_or_whole(self, json_expr: str) -> str:
        """
        Extract '$.d' from a JSON expression if it exists, otherwise return the whole JSON.
        For use in WHERE clauses when comparing DbClass values.

        :param json_expr: SQL expression that evaluates to JSON (e.g., column name or JSON literal)
        :return: SQL expression that extracts $.d if present, else the whole value
        """
        # SQLite: CASE WHEN json_type(expr, '$.d') IS NOT NULL THEN json_extract(expr, '$.d') ELSE expr END
        return f"CASE WHEN json_type({json_expr}, '$.d') IS NOT NULL THEN json_extract({json_expr}, '$.d') ELSE {json_expr} END"


class MySQLConnection:
    """MySQL connection."""

    def __init__(self, /, *, host='127.0.0.1', port=3306, user, password, database, **kwargs):
        """*for params see https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html*"""
        from mysql.connector import connect
        self.dialect = MySQLDialect()
        self.sql_name = self.dialect.sql_name
        self.database = database
        try:
            self.conn = connect(host=host, port=port, user=user, password=password, database=database, **kwargs)
            self.cur = self.conn.cursor()
            self.notconn = False
        except Exception:
            self.conn = None
            self.cur = None
            self.notconn = True


class SQLiteConnection:
    """SQLite connection."""

    def __init__(self, path: str, **kwargs):
        """
        :param path: path to the SQLite database file, or ':memory:' for an in-memory database
        """
        import sqlite3
        self.dialect = SQLiteDialect()
        self.sql_name = self.dialect.sql_name
        self.database = path
        try:
            self.conn = sqlite3.connect(path, check_same_thread=False, **kwargs)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.cur = self.conn.cursor()
            self.notconn = False
        except Exception:
            self.conn = None
            self.cur = None
            self.notconn = True


class _CursorWrapper:
    def __init__(self, cursor, print_func=None):
        self._cursor = cursor
        self._print_func = print_func if print_func else print

    def execute(self, query, *args, **kwargs):
        if args or kwargs:
            self._print_func(f"[DEBUG SQL] {query}\n  args: {args}\n  kwargs: {kwargs}", flush=True)
        else:
            self._print_func(f"[DEBUG SQL] {query}", flush=True)
        return self._cursor.execute(query, *args, **kwargs)

    def executemany(self, query, *args, **kwargs):
        if args or kwargs:
            self._print_func(f"[DEBUG SQL MANY] {query}\n  args: {args}\n  kwargs: {kwargs}", flush=True)
        else:
            self._print_func(f"[DEBUG SQL MANY] {query}", flush=True)
        return self._cursor.executemany(query, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class DebugMySQLConnection(MySQLConnection):
    def __init__(self, print_func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.notconn:
            self.cur = _CursorWrapper(self.cur, print_func=print_func)


class DebugSQLiteConnection(SQLiteConnection):
    def __init__(self, print_func=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.notconn:
            self.cur = _CursorWrapper(self.cur, print_func=print_func)