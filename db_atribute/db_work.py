import functools
import json

import db_atribute.db_class as db_class

def convert_atribute_type_to_mysql_type(atribute_type, len_varchar=50):
    if atribute_type == str:
        return {'status_code': 200, 'data': f'varchar({len_varchar})'}
    if atribute_type in (int, float, bool):
        return {'status_code': 200, 'data': atribute_type.__name__.upper()}
    if db_class.cheaker.this_db_atribute_container_class(atribute_type, this_is_cls=True):
        return {'status_code': 200, 'data': 'json'}
    return {'status_code': 300}

def convert_mysql_type_to_atribute_type(mysql_type):
    """for get mysql_type use Db_work.get_type_data_table"""
    convert_dict = {'varchar': str, 'int': int, 'float': float, 'tinyint': bool, 'json': db_class.DbContainer}
    if mysql_type in convert_dict:
        return {'status_code': 200, 'data': convert_dict[mysql_type]}
    return {'status_code': 300}

def convert_atribute_value_to_mysql_value(atribute_value):
    atribute_type = atribute_value.__class__
    if atribute_type in (int, float, bool):
        return {'status_code': 200, 'data': f'{atribute_value}'}
    if atribute_type == str:
        return {'status_code': 200, 'data': json.dumps(atribute_value)}
    if db_class.cheaker.this_db_atribute_container_class(atribute_type, this_is_cls=True):
        return {'status_code': 200, 'data': json.dumps(atribute_value.dumps())}
    if db_class.cheaker.this_container_class(atribute_type, this_is_cls=True):
        return {'status_code': 300}
    return {'status_code': 300}

def convert_mysql_value_to_atribute_value(mysql_value, atribute_type, _obj_dbatribute=None, atribute_name=None):
    if atribute_type in (int, float, str):
        return {'status_code': 200, 'data': mysql_value}
    if atribute_type == bool:
        return {'status_code': 200, 'data': True if mysql_value else False}
    if issubclass(atribute_type, db_class.DbContainer):
        return {'status_code': 200, 'data': db_class.DbContainer.loads(mysql_value, _obj_dbatribute=_obj_dbatribute, _name_atribute=atribute_name)}
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

def get_table_name(class_name:str, atribute_name:str):
    return f'cls_{class_name}_atr_{atribute_name}'.lower()

class Db_work:
    def __init__(self, connobj):
        self.connobj = connobj
        self.active_tables = self.list_tables()['data']

    @sql_decorator()
    def list_tables(self):
        self.connobj.cur.execute(f"""show tables""")
        return {'status_code': 200, 'data': [i[0] for i in self.connobj.cur.fetchall()]}

    @sql_decorator
    def create_table(self, table_name: str, atributes: list[tuple[str, str]]):
        if table_name.lower() in self.active_tables:
            return {'status_code': 301}
        self.connobj.cur.execute(f"""CREATE TABLE {table_name} (id INT PRIMARY KEY{', ' if atributes else ''}{', '.join((f'{atribute[0]} {atribute[1]}' for atribute in atributes))})""")
        self.connobj.conn.commit()
        self.active_tables = self.list_tables()['data']
        return {'status_code': 200}

    @sql_decorator
    def deleate_table(self, table_name: str, ignore_302:bool=False):
        if table_name.lower() not in self.active_tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        self.connobj.cur.execute(f"""DROP TABLE {table_name}""")
        self.connobj.conn.commit()
        self.active_tables = self.list_tables()['data']
        return {'status_code': 200}

    @sql_decorator
    def get_type_data_table(self, table_name: str):
        #print(table_name)
        if table_name not in self.active_tables:
            return {'status_code': 302}
        self.connobj.cur.execute(f"""SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'data' AND TABLE_SCHEMA = 'db_atribute' AND TABLE_NAME = '{table_name}';""")
        #print(f"""SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'db_atribute' AND TABLE_NAME = '{table_name}';""")
        return {'status_code': 200, 'data': self.connobj.cur.fetchall()[-1][0]}

    @sql_decorator
    def get_values_by_id(self, table_name:str, ID:int):
        if table_name not in self.active_tables:
            return {'status_code': 302}
        self.connobj.cur.execute(f"""select * from {table_name} where id={ID}""")
        return {'status_code': 200, 'data': [i[-1] for i in self.connobj.cur.fetchall()]}

    @sql_decorator
    def del_value_by_id(self, table_name:str, ID:int, ignore_302:bool=False):
        if table_name not in self.active_tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        self.connobj.cur.execute(f"""delete from {table_name} where id={ID}""")
        return {'status_code': 200}

    def add_value_by_id(self, table_name:str, ID:int, value, update_value_if_exists:bool=True, ignore_302:bool=False):
        temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
        if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
        if temp_data['status_code'] != 200: return temp_data
        if temp_data['data']:
            if update_value_if_exists:
                return self.update_value_by_id(table_name=table_name, ID=ID, value=value)
            return {'status_code': 303}
        self.connobj.cur.execute(f"""insert into {table_name} values ({ID}, {value})""")
        self.connobj.conn.commit()
        return {'status_code': 200}

    def update_value_by_id(self, table_name:str, ID:int, value, ignore_302:bool=False):
        temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
        if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
        if temp_data['status_code'] != 200: return temp_data
        if not temp_data['data']:
            return self.add_value_by_id(table_name=table_name, ID=ID, value=value, update_value_if_exists=False)
        self.connobj.cur.execute(f"""update {table_name} set data = {value} where id = {ID}""")
        self.connobj.conn.commit()
        return {'status_code': 200}

    def create_atribute_table(self, class_name: str, atribute_name: str, atribute_type, len_varchar:int=50):
        """
        create atribute table
        :param class_name: name of class atribute (obj.__class__.__name__)
        :param atribute_name: name of atribute, example: 'name', 'id', 'nickname', 'password_hash'
        :param atribute_type: type of atribute (type(obj)), example: str, DbList, int, bool, DbSet (for create DbList, DbSet use db_class.cheaker.create_one_db_class)
        :param len_varchar: len for string atributes, example: with len_varchar=5, atribute name='VeryLongName' convert to 'VeryL'
        :return: {'status_code': 300 | 200 | 100} (for 'status_code' read in connector)
        """
        table_name = get_table_name(class_name=class_name, atribute_name=atribute_name)
        temp_data = convert_atribute_type_to_mysql_type(atribute_type=atribute_type, len_varchar=len_varchar)
        if temp_data['status_code'] != 200: return temp_data
        atribute_table_type = temp_data['data']
        temp_data = self.create_table(table_name=table_name, atributes=[('data', atribute_table_type)])
        if temp_data['status_code'] != 200: return temp_data
        return {'status_code': 200}

    def add_atribute_value(self, class_name: str, atribute_name: str, ID:int, data, update_value_if_exists:bool=True, ignore_302:bool=False):
        table_name = get_table_name(class_name=class_name, atribute_name=atribute_name)
        temp_data = convert_atribute_value_to_mysql_value(data)
        if temp_data['status_code'] != 200: return temp_data
        value = temp_data['data']
        temp_data = self.add_value_by_id(table_name=table_name, ID=ID, value=value, update_value_if_exists=update_value_if_exists)
        if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
        if temp_data['status_code'] != 200: return temp_data
        return {'status_code': 200}

    def get_atribute_value(self, class_name: str, atribute_name: str, ID:int, atribute_type=None, _obj_dbatribute=None):
        table_name = get_table_name(class_name=class_name, atribute_name=atribute_name)
        temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
        if temp_data['status_code'] != 200: return temp_data
        if len(temp_data['data']) == 0: return {'status_code': 304}
        value = temp_data['data'][0]
        if atribute_type is None:
            atribute_type = object.__getattribute__(_obj_dbatribute, '__annotations__')[atribute_name]
        if atribute_type.__name__ in db_class.cheaker.class_name_to_db_class:
            atribute_type = db_class.cheaker.class_name_to_db_class[atribute_type.__name__]
        return convert_mysql_value_to_atribute_value(value, atribute_type=atribute_type, _obj_dbatribute=_obj_dbatribute, atribute_name=atribute_name)

if __name__ == "__main__":
    pass
    """
    print("del_table", db_work.deleate_table('cls_user_atr_age'))
    print("create_atr_table", db_work.create_atribute_table(class_name='user', atribute_name='age', atribute_type=int))
    print("add_atribute_value", db_work.add_atribute_value(class_name='user', atribute_name='age', ID=513675, data=100))
    print("get_atribute", db_work.get_atribute_value(class_name='user', atribute_name='age', ID=513675))

    print("get_value_type", db_work.get_type_data_table('cls_user_atr_age'))
    A = db_class.DbDict({0: [1, 4, {1}], 1: {2}, 2: {5: 6}, 3: (7, 8), 4: True, 5: False, (6, 7): [1, 3], True: 0}, _use_db = True)
    B = db_class.DbList([{2:[5]}, [1], [4], [3], {1, 3, 4}, True, True, (1, 2), (1, 2)], _use_db = True)
    C = db_class.DbSet([(1, 4), (3, 2), 4, True, '/Hello\n'], _use_db = True)
    print("add_value", db_work.add_atribute_value('cls_user_atr_age', 513675, A))
    print("get_atribute", db_work.get_atribute_value('cls_user_atr_age', 513675))
    a = db_work.get_atribute_value('cls_user_atr_age', 513675)['data']
    print(A, type(A))
    print(a, type(a))

    print("add_value", db_work.add_atribute_value('cls_user_atr_age', 513676, B))
    print("get_atribute", db_work.get_atribute_value('cls_user_atr_age', 513676))
    b = db_work.get_atribute_value('cls_user_atr_age', 513676)['data']
    print(b, type(b))

    print("add_value", db_work.add_atribute_value('cls_user_atr_age', 513677, C))
    print("get_atribute", db_work.get_atribute_value('cls_user_atr_age', 513677))
    c = db_work.get_atribute_value('cls_user_atr_age', 513677)['data']
    print(c, type(c))"""

