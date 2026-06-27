import functools
import json
import orjson
import collections

import db_attribute.db_class as db_class
import db_attribute.db_types as db_types
import db_attribute


def get_default_value_from_type(attribute_type):
    if attribute_type == str:
        return {'status_code': 200, 'data': ''}
    if attribute_type == int:
        return {'status_code': 200, 'data': '0'}
    if attribute_type == float:
        return {'status_code': 200, 'data': '0.0'}
    if attribute_type == bool:
        return {'status_code': 200, 'data': 'False'}
    if attribute_type is db_types.JsonType:
        return {'status_code': 200, 'data': json.dumps(json.dumps(dict()))}
    return {'status_code': 300}


def convert_attribute_type_to_sql_type(attribute_type, dialect, len_varchar=50):
    """Convert a Python type to an SQL column type string using the given dialect."""
    if attribute_type == str:
        return {'status_code': 200, 'data': f'varchar({len_varchar})'}
    if attribute_type == int or issubclass(attribute_type, db_attribute.DbAttribute):
        return {'status_code': 200, 'data': 'bigint'}
    if attribute_type == float:
        return {'status_code': 200, 'data': 'FLOAT'}
    if attribute_type == bool:
        return {'status_code': 200, 'data': dialect.bool_col_type()}
    if (db_class.DbClassCheaker.this_db_attribute_support_class(attribute_type, this_is_cls=True)
            or db_class.DbClassCheaker.this_support_class(attribute_type, this_is_cls=True)
            or attribute_type is db_types.JsonType):
        return {'status_code': 200, 'data': dialect.json_col_type()}
    return {'status_code': 300}

def convert_attribute_value_to_sql_param(attribute_value, attribute_type):
    """
    Convert a Python attribute value to a (sql_placeholder, python_param) pair.

    sql_placeholder — fragment to embed directly in the SQL string (for scalar
                      types and FK ids, this is already the final literal).
                      For JSON/DbClass types it is the sentinel string '__PARAM__',
                      meaning the caller must use a bind parameter instead.
    python_param    — the actual Python value to bind when sql_placeholder is
                      '__PARAM__', otherwise None.

    '__PARAM__' is used so that _add_value_by_id can decide:
      - MySQL:  replace '__PARAM__' with dialect.json_cast(json_literal)
      - SQLite: use execute(sql, (python_param,)) with '?' placeholder
    """
    if attribute_type in (int, float, bool):
        return {'status_code': 200, 'data': f'{attribute_value}', 'param': None}
    if attribute_type == str:
        return {'status_code': 200, 'data': json.dumps(attribute_value, ensure_ascii=False), 'param': None}
    if attribute_type is db_types.JsonType:
        # Store double-encoded JSON so the round-trip through TEXT/JSON column works
        python_val = json.dumps(attribute_value)
        return {'status_code': 200, 'data': '__PARAM__', 'param': python_val}
    if issubclass(attribute_type, db_attribute.discriptor.ConditionCore):
        return {'status_code': 200, 'data': attribute_value._get_condition_repr(), 'param': None}
    if issubclass(attribute_type, db_attribute.DbAttribute):
        if type(attribute_value) is int:
            return {'status_code': 200, 'data': f'{attribute_value}', 'param': None}
        return {'status_code': 200, 'data': f'{object.__getattribute__(attribute_value, "id")}', 'param': None}
    if (db_class.DbClassCheaker.this_db_attribute_support_class(attribute_type, this_is_cls=True)
            or db_class.DbClassCheaker.this_support_class(attribute_type, this_is_cls=True)):
        if db_class.DbClassCheaker.this_db_attribute_support_class(attribute_value):
            python_val = attribute_value.dumps()          # already a JSON string
        else:
            python_val = db_class.DbClassConverter.convert_to_db(attribute_value).dumps()
        return {'status_code': 200, 'data': '__PARAM__', 'param': python_val}
    return {'status_code': 300}

def convert_attribute_value_to_sql_value(attribute_value, attribute_type, dialect=None):
    """
    Legacy interface: returns result['data'] as a SQL literal string.
    Used for WHERE clauses (condition repr) and backwards-compat callers.
    """
    if attribute_type in (int, float, bool):
        return {'status_code': 200, 'data': f'{attribute_value}'}
    if attribute_type == str:
        s = json.dumps(attribute_value, ensure_ascii=False)
        if dialect is not None and hasattr(dialect, 'quote_string_literal'):
            s = dialect.quote_string_literal(attribute_value)
        return {'status_code': 200, 'data': s}
    if attribute_type is db_types.JsonType:
        inner = json.dumps(attribute_value)
        if dialect is not None and hasattr(dialect, 'quote_string_literal'):
            return {'status_code': 200, 'data': dialect.quote_string_literal(inner)}
        return {'status_code': 200, 'data': json.dumps(inner)}
    if issubclass(attribute_type, db_attribute.discriptor.ConditionCore):
        return {'status_code': 200, 'data': attribute_value._get_condition_repr()}
    if issubclass(attribute_type, db_attribute.DbAttribute):
        if type(attribute_value) is int:
            return {'status_code': 200, 'data': f'{attribute_value}'}
        return {'status_code': 200, 'data': f'{object.__getattribute__(attribute_value, "id")}'}
    if db_class.DbClassCheaker.this_db_attribute_support_class(attribute_type, this_is_cls=True) or db_class.DbClassCheaker.this_support_class(attribute_type, this_is_cls=True):
        if db_class.DbClassCheaker.this_db_attribute_support_class(attribute_value):
            dumps_str = attribute_value.dumps()
        else:
            dumps_str = db_class.DbClassConverter.convert_to_db(attribute_value).dumps()
        if dialect is not None and hasattr(dialect, 'quote_string_literal'):
            json_literal = dialect.quote_string_literal(dumps_str)
        else:
            raw = json.dumps(dumps_str, ensure_ascii=False)
            json_literal = f'CAST({raw} AS JSON)'
        if dialect is not None and hasattr(dialect, 'json_extract_d_or_whole'):
            return {'status_code': 200, 'data': dialect.json_extract_d_or_whole(json_literal)}
        return {'status_code': 200, 'data': json_literal}
    return {'status_code': 300}


def convert_sql_value_to_attribute_value(sql_value, attribute_type, _obj_dbattribute=None, attribute_name=None):
    if attribute_type in (int, float, str):
        return {'status_code': 200, 'data': sql_value}
    if attribute_type == bool:
        return {'status_code': 200, 'data': True if sql_value else False}
    if attribute_type is db_types.JsonType:
        return {'status_code': 200, 'data': orjson.loads(sql_value)}
    if issubclass(attribute_type, db_attribute.DbAttribute):
        return {'status_code': 200, 'data': attribute_type.get(id=sql_value)}
    if db_class.DbClassCheaker.this_support_class(attribute_type, this_is_cls=True) or db_class.DbClassCheaker.this_db_attribute_support_class(attribute_type, this_is_cls=True):
        try:
            return {'status_code': 200, 'data': db_class.DbClass.loads(
                sql_value, _obj_dbattribute=_obj_dbattribute, _name_attribute=attribute_name)}
        except db_types.LoadError as e:
            return {'status_code': 306, 'data': sql_value, 'info': e.info}
    return {'status_code': 300}


def sql_decorator(func_d=None, /, standart_return=None):
    def active_decorator(func):
        @functools.wraps(func)
        def method_wrapper(self, *args, **kwargs):
            if self.connobj.notconn:
                if standart_return:
                    return standart_return
                return {'status_code': 100}
            res = func(self, *args, **kwargs)
            return res
        return method_wrapper
    if func_d is None:
        return active_decorator
    return active_decorator(func_d)


def get_table_name(class_name: str, attribute_name: str):
    if ' ' in class_name:
        raise Exception(f'The "{class_name}" class has the space (" ") in the name')
    if ' ' in attribute_name:
        raise Exception(f'The "{attribute_name}" attribute has the space (" ") in the name')
    return f'cls {class_name} atr {attribute_name}'.lower()


def get_id_table_name(class_name: str):
    return f'cls {class_name} ids'.lower()


def screening(name, db_name="MySQL"):
    if db_name == "MySQL":
        return f'`{name}`'
    return f'"{name}"'


class Db_work:
    def __init__(self, connobj, sittings_for_mysql_types=None):
        """
        :param connobj: obj of connector.Connection or connector.SQLiteConnection
        :param sittings_for_mysql_types: (at this moment not used)
        """
        self.connobj = connobj
        self.sittings_for_mysql_types = {str: 'VARCHAR(255)', int: 'BIGINT', bytes: 'BLOB'}
        if isinstance(sittings_for_mysql_types, dict):
            self.sittings_for_mysql_types |= sittings_for_mysql_types
        self.tables = self.get_tables_list()['data']
        self.class_names = self.get_class_names_list()

    @property
    def _dialect(self):
        return self.connobj.dialect

    def get_class_names_list(self):
        Res = collections.defaultdict(list)
        for i in self.tables:
            try:
                temp = i.split()
                if temp[0] == 'cls' and temp[2] == 'atr':
                    Res[temp[1]].append(i)
            except Exception:
                pass
        return dict(Res)

    @sql_decorator()
    def get_tables_list(self):
        self.connobj.cur.execute(self._dialect.show_tables_sql())
        return {'status_code': 200, 'data': {i[0] for i in self.connobj.cur.fetchall()}}

    @sql_decorator
    def _create_table(self, table_name: str, attributes: list[tuple[str, str]]):
        if table_name.lower() in self.tables:
            return {'status_code': 301}
        d = self._dialect
        quoted = d.quote(table_name)
        col_defs = ', '.join(f'{attr[0]} {attr[1]}' for attr in attributes)
        self.connobj.cur.execute(d.create_table_sql(quoted, col_defs))
        self.connobj.conn.commit()
        self.tables = self.get_tables_list()['data']
        self.class_names = self.get_class_names_list()
        return {'status_code': 200}

    @sql_decorator
    def _create_id_table(self, table_name: str):
        if table_name.lower() in self.tables:
            return {'status_code': 301}
        d = self._dialect
        quoted = d.quote(table_name)
        self.connobj.cur.execute(d.create_table_sql(quoted, ''))
        self.connobj.conn.commit()
        self.tables = self.get_tables_list()['data']
        self.class_names = self.get_class_names_list()
        return {'status_code': 200}

    @sql_decorator
    def _deleate_table(self, table_name: str, ignore_302: bool = False):
        if table_name.lower() not in self.tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        quoted = self._dialect.quote(table_name)
        self.connobj.cur.execute(f"DROP TABLE {quoted}")
        self.connobj.conn.commit()
        self.tables = self.get_tables_list()['data']
        self.class_names = self.get_class_names_list()
        return {'status_code': 200}

    @sql_decorator
    def _get_type_data_table(self, table_name: str):
        if table_name not in self.tables:
            return {'status_code': 302}
        d = self._dialect
        if d.sql_name == 'MySQL':
            self.connobj.cur.execute(
                f"SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
                f"WHERE COLUMN_NAME = 'data' "
                f"AND TABLE_SCHEMA = '{self.connobj.database}' "
                f"AND TABLE_NAME = '{table_name}';"
            )
            return {'status_code': 200, 'data': self.connobj.cur.fetchall()[-1][0]}
        else:
            self.connobj.cur.execute(f"PRAGMA table_info({d.quote(table_name)})")
            for row in self.connobj.cur.fetchall():
                if row[1] == 'data':
                    return {'status_code': 200, 'data': row[2]}
            return {'status_code': 304}

    @sql_decorator
    def _get_values_by_id(self, table_name: str, ID: int, operator: str = "=", ignore_302: bool = False):
        if table_name not in self.tables:
            if ignore_302:
                return {'status_code': 200, 'data': []}
            return {'status_code': 302}
        quoted = self._dialect.quote(table_name)
        self.connobj.cur.execute(f"SELECT * FROM {quoted} WHERE id {operator} {ID}")
        return {'status_code': 200, 'data': [i[-1] for i in self.connobj.cur.fetchall()]}

    @sql_decorator
    def _get_ids_by_value(self, table_name: str, value, operator: str = "=", ignore_302: bool = False):
        if table_name not in self.tables:
            if ignore_302:
                return {'status_code': 200, 'data': []}
            return {'status_code': 302}
        quoted = self._dialect.quote(table_name)
        self.connobj.cur.execute(f"SELECT id FROM {quoted} WHERE data {operator} {value}")
        return {'status_code': 200, 'data': {i[0] for i in self.connobj.cur.fetchall()}}

    @sql_decorator
    def _get_all_ids(self, table_name: str, ignore_302: bool = False):
        if table_name not in self.tables:
            if ignore_302:
                return {'status_code': 200, 'data': []}
            return {'status_code': 302}
        quoted = self._dialect.quote(table_name)
        self.connobj.cur.execute(f"SELECT id FROM {quoted}")
        return {'status_code': 200, 'data': {i[0] for i in self.connobj.cur.fetchall()}}

    @sql_decorator
    def _get_ids_by_condition(self, class_name: str, condition: str, field_names=None, ignore_302: bool = False):
        if class_name not in self.class_names:
            if ignore_302:
                return {'status_code': 200, 'data': []}
            return {'status_code': 302}
        d = self._dialect
        id_table = get_id_table_name(class_name)
        scr_id_table = d.quote(id_table)
        scr_id = d.quote('id')

        if field_names is None:
            attr_tables = [d.quote(t) for t in self.class_names[class_name]]
        else:
            candidate_tables = [get_table_name(class_name, attr) for attr in field_names]
            attr_tables = [d.quote(t) for t in candidate_tables if t in self.tables]

        joins = ' '.join(
            f'LEFT JOIN {t} ON {scr_id_table}.{scr_id} = {t}.{scr_id}'
            for t in attr_tables
        )
        self.connobj.cur.execute(
            f"SELECT {scr_id_table}.{scr_id} FROM {scr_id_table} {joins} WHERE {condition}"
        )
        return {'status_code': 200, 'data': {i[0] for i in self.connobj.cur.fetchall()}}

    @sql_decorator
    def _del_value_by_id(self, table_name: str, ID: int, ignore_302: bool = False):
        if table_name not in self.tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        quoted = self._dialect.quote(table_name)
        self.connobj.cur.execute(f"DELETE FROM {quoted} WHERE id={ID}")
        self.connobj.conn.commit()
        return {'status_code': 200}

    @sql_decorator
    def _add_value_by_id(self, table_name: str, ID: int, value: str, param=None, ignore_302: bool = False):
        """
        Insert or update a (id, data) row.

        :param value:  SQL literal fragment, or '__PARAM__' when param is not None.
        :param param:  Python value to bind when value == '__PARAM__'.
        """
        try:
            d = self._dialect
            quoted = d.quote(table_name)
            if param is not None:
                # Parameterised path — needed for SQLite JSON / DbClass values
                sql, args = d.upsert_data_param_sql(quoted, ID, param)
                self.connobj.cur.execute(sql, args)
            else:
                self.connobj.cur.execute(d.upsert_data_sql(quoted, ID, value))
            self.connobj.conn.commit()
        except Exception as e:
            if d.is_table_not_found_error(e):
                return {'status_code': 200} if ignore_302 else {'status_code': 302}
            raise
        return {'status_code': 200}

    @sql_decorator
    def _add_id(self, table_name: str, ID: int, ignore_302: bool = False):
        try:
            d = self._dialect
            quoted = d.quote(table_name)
            self.connobj.cur.execute(d.upsert_id_sql(quoted, ID))
            self.connobj.conn.commit()
        except Exception as e:
            if d.is_table_not_found_error(e):
                return {'status_code': 200} if ignore_302 else {'status_code': 302}
            raise
        return {'status_code': 200}

    @sql_decorator
    def _get_new_id(self, table_name: str):
        try:
            d = self._dialect
            quoted = d.quote(table_name)
            self.connobj.cur.execute(d.new_id_sql(quoted))
            next_id = self.connobj.cur.lastrowid
            self.connobj.conn.commit()
        except Exception as e:
            if d.is_table_not_found_error(e):
                return {'status_code': 302}
            raise
        return {'status_code': 200, 'data': next_id}

    def create_attribute_table(self, class_name: str, attribute_name: str, db_field: db_types.DbField = None, _cls_dbattribute = None, len_varchar:int=50):
        """
        create attribute table
        :param class_name: name of class attribute (obj.__class__.__name__)
        :param attribute_name: name of attribute, example: 'name', 'id', 'nickname', 'password_hash'
        :param db_field: Db Field of this Field
        :param _cls_dbattribute: db_attribute cls, used if attribute_type is None
        :param len_varchar: len for string attributes, example: with len_varchar=5, attribute name='VeryLongName' convert to 'VeryL'
        :return: {'status_code': 300 | 200 | 100} (for 'status_code' read in connector)
        """
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        if db_field is None:
            db_field: db_types.DbField = object.__getattribute__(_cls_dbattribute, '__db_fields__')[attribute_name]
        attribute_type = db_field.python_type
        if attribute_type in [str, int, float, bool, db_types.JsonType] and db_field.sql_type is not db_types.MISSING:
            attribute_table_type = db_field.sql_type
        else:
            temp_data = convert_attribute_type_to_sql_type(
                attribute_type=attribute_type,
                dialect=self._dialect,
                len_varchar=len_varchar,
            )
            if temp_data['status_code'] != 200:
                return temp_data
            attribute_table_type = temp_data['data']
        temp_data = self._create_table(table_name=table_name, attributes=[('data', attribute_table_type)])
        if temp_data['status_code'] != 200:
            return temp_data
        return {'status_code': 200}

    def create_id_table(self, class_name: str):
        return self._create_id_table(get_id_table_name(class_name=class_name))

    def add_attribute_value(self, class_name: str, attribute_name: str, ID: int, data, attribute_type=None, _cls_dbattribute=None, ignore_302: bool = False):
        if attribute_type is None:
            attribute_type = object.__getattribute__(_cls_dbattribute, '__db_fields__')[attribute_name].python_type
        temp_data = convert_attribute_value_to_sql_param(data, attribute_type=attribute_type)
        if temp_data['status_code'] != 200:
            return temp_data
        value = temp_data['data']
        param = temp_data['param']
        # For MySQL, convert __PARAM__ back to an inline CAST literal
        if value == '__PARAM__' and self._dialect.sql_name == 'MySQL':
            raw = json.dumps(param, ensure_ascii=False)
            value = self._dialect.json_cast(raw)
            param = None
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        return self._add_value_by_id(table_name=table_name, ID=ID, value=value, param=param, ignore_302=ignore_302)

    def add_id(self, class_name: str, ID: int, ignore_302: bool = False):
        return self._add_id(table_name=get_id_table_name(class_name), ID=ID, ignore_302=ignore_302)

    def get_new_id(self, class_name: str):
        return self._get_new_id(table_name=get_id_table_name(class_name))

    def get_attribute_value(self, class_name: str, attribute_name: str, ID: int, attribute_type=None, _obj_dbattribute=None):
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        temp_data = self._get_values_by_id(table_name=table_name, ID=ID)
        if temp_data['status_code'] != 200: return temp_data
        if len(temp_data['data']) == 0: return {'status_code': 304}
        value = temp_data['data'][0]
        if attribute_type is None:
            attribute_type = object.__getattribute__(_obj_dbattribute, '__db_fields__')[attribute_name].python_type
        return convert_sql_value_to_attribute_value(value, attribute_type=attribute_type, _obj_dbattribute=_obj_dbattribute, attribute_name=attribute_name)

    def get_all_ids(self, class_name: str, ignore_302: bool = False):
        return self._get_all_ids(table_name=get_id_table_name(class_name=class_name), ignore_302=ignore_302)

    def del_attribute_value(self, class_name: str, attribute_name: str, ID: int, ignore_302: bool = False):
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        return self._del_value_by_id(table_name=table_name, ID=ID, ignore_302=ignore_302)

    def found_ids_by_value(self, class_name: str, attribute_name: str, data, attribute_type=None, _cls_dbattribute=None, operator: str = "=", ignore_302: bool = False):
        """
        :param class_name: ex: 'User'
        :param attribute_name: ex: 'name'/'age'
        :param data: any data, ex: 10 / {3, 5, 6} / 'Bob'
        :param attribute_type: ex: int, bool, list, User (Db attribute type)
        :param _cls_dbattribute: User
        :param operator: '=' / '!=' / '<>' / '<' / '>' / '>=' / '<=' / 'Like'
        :param ignore_302: bool, if true, ignore 302 error, return 200 and empty data
        :return: set of id's
        """
        if attribute_type is None:
            attribute_type = object.__getattribute__(_cls_dbattribute, '__db_fields__')[attribute_name].python_type
        temp_data = convert_attribute_value_to_sql_value(data, attribute_type=attribute_type, dialect=self._dialect)
        if temp_data['status_code'] != 200:
            return temp_data
        value = temp_data['data']
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        return self._get_ids_by_value(table_name=table_name, value=value, operator=operator, ignore_302=ignore_302)

    def found_ids_by_condition(self, class_name: str, condition: str, field_names=None, ignore_302: bool = False):
        return self._get_ids_by_condition(class_name=class_name.lower(), condition=condition, field_names=field_names, ignore_302=ignore_302)

    def cheak_exists_attribute_table(self, class_name: str, attribute_name: str):
        return get_table_name(class_name, attribute_name) in self.tables

    def cheak_exists_id_table(self, class_name: str):
        return get_id_table_name(class_name) in self.tables


if __name__ == '__main__':
    from config import host, user, password, database
    import db_attribute.connector as connector

    connect_obj = connector.MySQLConnection(host=host, user=user, password=password, database=database)
    db_work_obj = Db_work(connect_obj)
    #print(db_work_obj.class_names)
    #print(db_work_obj.tables)
    #db_work_obj.create_attribute_table('User', 'name', str)
    #db_work_obj.add_attribute_value('User', 'name', 10, 'Bob', str)
    #print(db_work_obj.get_attribute_value('User', 'name', 10, str))
    print(db_work_obj.tables)
    print(db_work_obj.class_names)
    #db_work_obj._deleate_table('cls dbattributemetaclass ids')
    #for i in db_work_obj.tables:
    #    db_work_obj._deleate_table(i)
    #    print(i)

    #db_work_obj.deleate_table('cls_a_atr_b_obj')

    #db_work_obj.update_value_by_id(table_name='cls_user_atr_age', ID=12, value=10, cheak_exists_value=False)
