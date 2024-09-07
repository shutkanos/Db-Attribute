import functools

from connector import conn, cur, notconn
import db_class

def convert_atribute_type_to_mysql_type(atribute_type, len_varchar=50):
    if atribute_type == str:
        return {'status_code': 200, 'data': f'varchar({len_varchar})'}
    if atribute_type in (int, float, bool):
        return {'status_code': 200, 'data': atribute_type.__name__.upper()}
    if db_container.cheaker.this_db_atribute_container_class(atribute_type, this_is_cls=True):
        return {'status_code': 200, 'data': 'json'}
    return {'status_code': 300}

def convert_mysql_type_to_atribute_type(mysql_type):
    """for get mysql_type use Db_work.get_type_data_table"""
    convert_dict = {'varchar': str, 'int': int, 'float': float, 'tinyint': bool, 'json': db_container.DbContainer}
    if mysql_type in convert_dict:
        return {'status_code': 200, 'data': convert_dict[mysql_type]}
    return {'status_code': 300}

def convert_atribute_value_to_mysql_value(atribute_value):
    atribute_type = atribute_value.__class__
    if atribute_type in (int, float, bool):
        return {'status_code': 200, 'data': f'{atribute_value}'}
    if atribute_type == str:
        return {'status_code': 200, 'data': conver_to_sql_string(atribute_value)}
    if db_container.cheaker.this_db_atribute_container_class(atribute_type, this_is_cls=True):
        return {'status_code': 200, 'data': atribute_value.dumps()}
    return {'status_code': 300}

def convert_mysql_value_to_atribute_value(mysql_value, mysql_type):
    """for get mysql_type use Db_work.get_type_data_table"""
    temp_data = convert_mysql_type_to_atribute_type(mysql_type)
    if temp_data['status_code'] != 200:
        return temp_data
    atribute_type = temp_data['data']
    if atribute_type in (int, float, bool, str):
        return {'status_code': 200, 'data': mysql_value}
    if isinstance(atribute_type, db_container.DbContainer):
        return {'status_code': 200, 'data': db_container.DbContainer.loads(mysql_value)}
    return {'status_code': 300}

def conver_to_sql_string(string):
    replace_characters = {'\0': '\\0', '\'': '\\\'', '\"': '\\"', '\b': '\\b', '\n': '\\n', '\r': '\\r', '\t': '\\t', '\x1a':'\\x1a', '\\': '\\\\'}
    for i in replace_characters:
        string.replace(i, replace_characters[i])
    return f"'{string}'"

def secure_sql(obj, cheak_container=True, bloc_symbol=None):
    """
    Protect str from SQLi attack, use it if user can change or input this data in programm.
    Secure_sql bloced: #${(,` ;:*&[\./%]~)}"'?
    :param obj: input data, example: name: 'melon' or names: ['melon', 'melon2']
    :param cheak_container: if obj is container and cheak_container is True, check the elements of obj with secure_sql, defaults to True
    :type cheak_container: bool
    :param bloc_symbol: Which symbols should be blocked, example: {'-', '|'}
    :type bloc_symbol: set | None
    :return: if False: it's ok, if True: it's SQLi attack
    :rtype: bool
    """
    if cheak_container:
        if isinstance(obj, (list, db_container.DbList, set, db_container.DbSet)):
            return any((secure_sql(i) for i in obj))
        if isinstance(obj, (dict, db_container.DbDict)):
            return any((secure_sql(obj[i]) for i in obj))
    if type(obj) != str:
        return False
    if obj[0] in "\"'" and obj[-1] in "\"'":
        set_obj = set(obj[1:-1])
    else:
        set_obj = set(obj)
    if {' ', ',', ':', ';', '[', ']', '\\', '/', '.', '`', '~', '&', '?', '%', '#', '$', '*', '(', ')', '{', '}'} & set_obj:
        return True
    if bloc_symbol and bloc_symbol & set_obj:
        return True
    return False

def sql_decorator(standart_return=None, this_class_method=True):
    def active_decorator(func):
        @functools.wraps(func)
        def method_wrapper(self, *args, **kwargs):
            if self.notconn:
                if standart_return:
                    return standart_return
                return {'status_code': 100}
            res = func(self, *args, **kwargs)
            return res

        @functools.wraps(func)
        def func_wrapper(*args, **kwargs):
            if notconn:
                if standart_return:
                    return standart_return
                return {'status_code': 100}
            res = func(*args, **kwargs)
            return res

        if this_class_method:
            return method_wrapper
        return func_wrapper
    return active_decorator

class Db_work:
    def __init__(self, conn_=None, cur_=None, notconn_=None):
        self.conn = conn_
        self.cur = cur_
        self.notconn = notconn_
        if self.conn is None:
            self.conn = conn
        if self.cur is None:
            self.cur = cur
        if self.notconn is None:
            self.notconn = notconn
        self.active_tables = self.list_tables()['data']

    def create_atribute_table(self, class_name: str, atribute_name: str, atribute_type, len_varchar:int=50):
        table_name = f'cls_{class_name}_atr_{atribute_name}'.lower()
        temp_data = convert_atribute_type_to_mysql_type(atribute_type=atribute_type, len_varchar=len_varchar)
        if temp_data['status_code'] != 200: return temp_data
        atribute_table_type = temp_data['data']
        temp_data = self.create_table(table_name=table_name, atributes=[('data', atribute_table_type)])
        if temp_data['status_code'] != 200: return temp_data
        return {'status_code': 200}

    @sql_decorator()
    def list_tables(self):
        self.cur.execute(f"""show tables""")
        return {'status_code': 200, 'data': [i[0] for i in self.cur.fetchall()]}

    @sql_decorator()
    def create_table(self, table_name: str, atributes: list[tuple[str, str]]):
        if table_name.lower() in self.active_tables:
            return {'status_code': 301}
        self.cur.execute(f"""CREATE TABLE {table_name} (id INT PRIMARY KEY{', ' if atributes else ''}{', '.join((f'{atribute[0]} {atribute[1]}' for atribute in atributes))})""")
        self.conn.commit()
        self.active_tables = self.list_tables()['data']
        return {'status_code': 200}

    @sql_decorator()
    def deleate_table(self, table_name: str, ignore_302:bool=False):
        if table_name.lower() not in self.active_tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        self.cur.execute(f"""DROP TABLE {table_name}""")
        self.conn.commit()
        self.active_tables = self.list_tables()['data']
        return {'status_code': 200}

    @sql_decorator()
    def get_type_data_table(self, table_name: str):
        if table_name not in self.active_tables:
            return {'status_code': 302}
        self.cur.execute(f"""SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'db_atribute' AND TABLE_NAME = '{table_name}';""")
        return {'status_code': 200, 'data': self.cur.fetchall()[-1][0]}

    @sql_decorator()
    def get_values_by_id(self, table_name:str, ID:int):
        if table_name not in self.active_tables:
            return {'status_code': 302}
        self.cur.execute(f"""select * from {table_name} where id={ID}""")
        return {'status_code': 200, 'data': [i[-1] for i in self.cur.fetchall()]}

    @sql_decorator()
    def del_value_by_id(self, table_name:str, ID:int, ignore_302:bool=False):
        if table_name not in self.active_tables:
            if ignore_302:
                return {'status_code': 200}
            return {'status_code': 302}
        self.cur.execute(f"""delete from {table_name} where id={ID}""")
        return {'status_code': 200}

    @sql_decorator()
    def add_value_by_id(self, table_name:str, ID:int, value, update_value_if_exists:bool=True, ignore_302:bool=False):
        temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
        if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
        if temp_data['status_code'] != 200: return temp_data
        if temp_data['data']:
            if update_value_if_exists:
                return self.update_value_by_id(table_name=table_name, ID=ID, value=value)
            return {'status_code': 303}
        self.cur.execute(f"""insert into {table_name} values ({ID}, {value})""")
        self.conn.commit()
        return {'status_code': 200}

    @sql_decorator()
    def update_value_by_id(self, table_name:str, ID:int, value, ignore_302:bool=False):
        temp_data = self.get_values_by_id(table_name=table_name, ID=ID)
        if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
        if temp_data['status_code'] != 200: return temp_data
        if not temp_data['data']:
            return self.add_value_by_id(table_name=table_name, ID=ID, value=value, update_value_if_exists=False)
        self.cur.execute(f"""update {table_name} set data = {value} where id = {ID}""")
        self.conn.commit()
        return {'status_code': 200}

    @sql_decorator()
    def add_atribute_value(self, table_name:str, ID:int, data, update_value_if_exists:bool=True, ignore_302:bool=False):
        temp_data = convert_atribute_value_to_mysql_value(data)
        if temp_data['status_code'] != 200:return temp_data
        value = temp_data['data']
        print(value)
        temp_data = self.add_value_by_id(table_name=table_name, ID=ID, value=value, update_value_if_exists=update_value_if_exists)
        if temp_data['status_code'] == 302 and ignore_302: return {'status_code': 200}
        if temp_data['status_code'] != 200: return temp_data
        return {'status_code': 200}

if __name__ == "__main__":
    db_work = Db_work(conn_=conn, cur_=cur, notconn_=notconn)
    print("del_table", db_work.deleate_table('cls_user_atr_age'))
    #print("create_atr_table", db_work.create_atribute_table(class_name='user', atribute_name='age', atribute_type=str))
    print("create_table", db_work.create_table('cls_user_atr_age', [('data', 'json')]))
    print("get_value_type", db_work.get_type_data_table('cls_user_atr_age'))
    #print("add_value", db_work.add_atribute_value('cls_user_atr_age', 513675, 'WhAt'))
    print("add_value", db_work.add_atribute_value('cls_user_atr_age', 513675, '{"key": "its key", "key2": [1, 2, 3, "hello"]}'))
    print("get_value", db_work.get_values_by_id('cls_user_atr_age', 513675))

