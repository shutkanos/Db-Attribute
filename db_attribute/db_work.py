import functools
import json
import orjson

import db_attribute.db_class as db_class
import db_attribute.dbtypes as dbtypes

def convert_attribute_type_to_mysql_type(attribute_type, len_varchar=50):
    if attribute_type == str:
        return {'status_code': 200, 'data': f'varchar({len_varchar})'}
    if attribute_type == int:
        return {'status_code': 200, 'data': f'bigint'}
    if attribute_type == float or attribute_type == bool:
        return {'status_code': 200, 'data': attribute_type.__name__.upper()}
    if db_class.cheaker.this_db_attribute_support_class(attribute_type, this_is_cls=True) or attribute_type is dbtypes.JsonType:
        return {'status_code': 200, 'data': 'json'}
    return {'status_code': 300}

def convert_mysql_type_to_attribute_type(mysql_type):
    """Not used!"""
    print('Worn! convert_mysql_type_to_attribute_type is not used not. Without support json')
    convert_dict = {'varchar': str, 'int': int, 'float': float, 'tinyint': bool, 'json': db_class.DbClass}
    if mysql_type in convert_dict:
        return {'status_code': 200, 'data': convert_dict[mysql_type]}
    return {'status_code': 300}

def convert_attribute_value_to_mysql_value(attribute_value, attribute_type):
    if attribute_type in (int, float, bool):
        return {'status_code': 200, 'data': f'{attribute_value}'}
    if attribute_type == str:
        return {'status_code': 200, 'data': json.dumps(attribute_value)}
    if attribute_type is dbtypes.JsonType:
        return {'status_code': 200, 'data': json.dumps(json.dumps(attribute_value))}
    if db_class.cheaker.this_db_attribute_support_class(attribute_type, this_is_cls=True):
        return {'status_code': 200, 'data': f'CAST({json.dumps(attribute_value.dumps())} AS JSON)'}
    if db_class.cheaker.this_support_class(attribute_type, this_is_cls=True):
        return {'status_code': 200, 'data': f'CAST({json.dumps(db_class.cheaker.create_db_class(attribute_value).dumps())} AS JSON)'}
    return {'status_code': 300}

def convert_mysql_value_to_attribute_value(mysql_value, attribute_type, _obj_dbattribute=None, attribute_name=None):
    if attribute_type in (int, float, str):
        return {'status_code': 200, 'data': mysql_value}
    if attribute_type == bool:
        return {'status_code': 200, 'data': True if mysql_value else False}
    if attribute_type is dbtypes.JsonType:
        return {'status_code': 200, 'data': orjson.loads(mysql_value)}
    if issubclass(attribute_type, db_class.DbClass):
        return {'status_code': 200, 'data': db_class.DbClass.loads(mysql_value, _obj_dbattribute=_obj_dbattribute, _name_attribute=attribute_name)}
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

def get_table_name(class_name:str, attribute_name:str):
    return f'cls_{class_name}_atr_{attribute_name}'.lower()

class Db_work:
    def __init__(self, connobj, sittings_for_mysql_types=None):
        """
        :param connobj: obj of connector.Connection
        :param sittings_for_mysql_types: (at this moment not used) example: {str: 'VARCHAR(255)', int: 'BIGINT', bytes: 'BLOB'}
        """
        self.connobj = connobj
        self.sittings_for_mysql_types = {str: 'VARCHAR(255)', int: 'BIGINT', bytes: 'BLOB'}
        if isinstance(sittings_for_mysql_types, dict):
            self.sittings_for_mysql_types |= sittings_for_mysql_types
        self.active_tables = self.get_list_tables()['data']

    @sql_decorator()
    def get_list_tables(self):
        self.connobj.cur.execute(f"""show tables""")
        return {'status_code': 200, 'data': {i[0] for i in self.connobj.cur.fetchall()}}

    @sql_decorator
    def create_table(self, table_name: str, attributes: list[tuple[str, str]]):
        if table_name.lower() in self.active_tables:
            return {'status_code': 301}
        self.connobj.cur.execute(f"""CREATE TABLE {table_name} (id BIGINT PRIMARY KEY{', ' if attributes else ''}{', '.join((f'{attribute[0]} {attribute[1]}' for attribute in attributes))})""")
        self.connobj.conn.commit()
        self.active_tables = self.get_list_tables()['data']
        return {'status_code': 200}

    @sql_decorator
    def deleate_table(self, table_name: str, ignore_302:bool=False):
        if table_name.lower() not in self.active_tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        self.connobj.cur.execute(f"""DROP TABLE {table_name}""")
        self.connobj.conn.commit()
        self.active_tables = self.get_list_tables()['data']
        return {'status_code': 200}

    @sql_decorator
    def get_type_data_table(self, table_name: str):
        if table_name not in self.active_tables:
            return {'status_code': 302}
        self.connobj.cur.execute(f"""SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'data' AND TABLE_SCHEMA = 'db_attribute' AND TABLE_NAME = '{table_name}';""")
        return {'status_code': 200, 'data': self.connobj.cur.fetchall()[-1][0]}

    @sql_decorator
    def get_values_by_id(self, table_name:str, ID:int, ignore_302:bool=False):
        if table_name not in self.active_tables:
            if ignore_302:
                return {'status_code': 200, 'data': []}
            return {'status_code': 302}
        self.connobj.cur.execute(f"""select * from {table_name} where id={ID}""")
        return {'status_code': 200, 'data': [i[-1] for i in self.connobj.cur.fetchall()]}

    @sql_decorator
    def get_ids_by_value(self, table_name:str, value, ignore_302:bool=False):
        if table_name not in self.active_tables:
            if ignore_302:
                return {'status_code': 200, 'data': []}
            return {'status_code': 302}
        self.connobj.cur.execute(f"""select id from {table_name} where data={value}""")
        return {'status_code': 200, 'data': [i[0] for i in self.connobj.cur.fetchall()]}

    @sql_decorator
    def del_value_by_id(self, table_name:str, ID:int, ignore_302:bool=False):
        if table_name not in self.active_tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        self.connobj.cur.execute(f"""delete from {table_name} where id={ID}""")
        return {'status_code': 200}
    
    @sql_decorator
    def add_value_by_id(self, table_name:str, ID:int, value, update_value_if_exists:bool=True, cheak_exists_value:bool=True, ignore_302:bool=False):
        if cheak_exists_value:
            temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
            if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
            if temp_data['status_code'] != 200: return temp_data
            if temp_data['data']:
                if update_value_if_exists:
                    return self.update_value_by_id(table_name=table_name, ID=ID, value=value, cheak_exists_value=False)
                return {'status_code': 303}
        self.connobj.cur.execute(f"""insert into {table_name} values ({ID}, {value})""")
        self.connobj.conn.commit()
        return {'status_code': 200}
    
    @sql_decorator
    def update_value_by_id(self, table_name:str, ID:int, value, add_value_if_not_exists:bool=True, cheak_exists_value:bool=True, ignore_302:bool=False):
        if cheak_exists_value:
            temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
            if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
            if temp_data['status_code'] != 200: return temp_data
            if not temp_data['data']:
                if add_value_if_not_exists:
                    return self.add_value_by_id(table_name=table_name, ID=ID, value=value, cheak_exists_value=False)
                return {'status_code': 304}
        self.connobj.cur.execute(f"""update {table_name} set data = {value} where id = {ID}""")
        self.connobj.conn.commit()
        return {'status_code': 200}

    def create_attribute_table(self, class_name: str, attribute_name: str, attribute_type=None, _cls_dbattribute=None, len_varchar:int=50):
        """
        create attribute table
        :param class_name: name of class attribute (obj.__class__.__name__)
        :param attribute_name: name of attribute, example: 'name', 'id', 'nickname', 'password_hash'
        :param attribute_type: type of attribute (type(obj)), example: str, DbList, int, bool, DbSet, dbtypes.JsonType (for create DbList, DbSet use db_class.cheaker.create_one_db_class)
        :param _cls_dbattribute: db_attribute cls, used if attribute_type is None
        :param len_varchar: len for string attributes, example: with len_varchar=5, attribute name='VeryLongName' convert to 'VeryL'
        :return: {'status_code': 300 | 200 | 100} (for 'status_code' read in connector)
        """
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        if attribute_type is None:
            attribute_type = object.__getattribute__(_cls_dbattribute, '__annotations__')[attribute_name]
        temp_data = convert_attribute_type_to_mysql_type(attribute_type=attribute_type, len_varchar=len_varchar)
        if temp_data['status_code'] != 200: return temp_data
        attribute_table_type = temp_data['data']
        temp_data = self.create_table(table_name=table_name, attributes=[('data', attribute_table_type)])
        if temp_data['status_code'] != 200: return temp_data
        return {'status_code': 200}

    def add_attribute_value(self, class_name: str, attribute_name: str, ID:int, data, attribute_type=None, _cls_dbattribute=None, cheak_exists_value:bool=True, update_value:bool=False, ignore_302:bool=False):
        if attribute_type is None:
            attribute_type = object.__getattribute__(_cls_dbattribute, '__annotations__')[attribute_name]
        temp_data = convert_attribute_value_to_mysql_value(data, attribute_type=attribute_type)
        if temp_data['status_code'] != 200: return temp_data
        value = temp_data['data']
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        if update_value:
            return self.update_value_by_id(table_name=table_name, ID=ID, value=value, cheak_exists_value=cheak_exists_value, ignore_302=ignore_302)
        return self.add_value_by_id(table_name=table_name, ID=ID, value=value, cheak_exists_value=cheak_exists_value, ignore_302=ignore_302)

    def get_attribute_value(self, class_name: str, attribute_name: str, ID:int, attribute_type=None, _obj_dbattribute=None):
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
        if temp_data['status_code'] != 200: return temp_data
        if len(temp_data['data']) == 0: return {'status_code': 304}
        value = temp_data['data'][0]
        if attribute_type is None:
            attribute_type = object.__getattribute__(_obj_dbattribute, '__annotations__')[attribute_name]
        if attribute_type.__name__ in db_class.cheaker.class_name_to_db_class:
            attribute_type = db_class.cheaker.class_name_to_db_class[attribute_type.__name__]
        return convert_mysql_value_to_attribute_value(value, attribute_type=attribute_type, _obj_dbattribute=_obj_dbattribute, attribute_name=attribute_name)

    def found_ids_by_value(self, class_name: str, attribute_name: str, data, attribute_type=None, _cls_dbattribute=None, ignore_302:bool=False):
        if attribute_type is None:
            attribute_type = object.__getattribute__(_cls_dbattribute, '__annotations__')[attribute_name]
        temp_data = convert_attribute_value_to_mysql_value(data, attribute_type=attribute_type)
        if temp_data['status_code'] != 200: return temp_data
        value = temp_data['data']
        table_name = get_table_name(class_name=class_name, attribute_name=attribute_name)
        return self.get_ids_by_value(table_name=table_name, value=value, ignore_302=ignore_302)


if __name__ == '__main__':
    from config import host, user, password, database
    import connector

    connect_obj = connector.Connection(host=host, user=user, password=password, database=database)
    db_work_obj = Db_work(connect_obj)

    db_work_obj.update_value_by_id(table_name='cls_user_atr_age', ID=12, value=10, cheak_exists_value=False)

