import functools

from connector import conn, cur, notconn
import db_container

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
    if {' ', ',', ':', ';', '"', '\'', '[', ']', '\\', '/', '.', '`', '~', '&', '?', '%', '#', '$', '*', '(', ')', '{', '}'} & set(obj):
        return True
    if bloc_symbol and bloc_symbol & set(obj):
        return True
    return False

def sql_decorator(secure_args=False, standart_return=None):
    def active_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if notconn:
                if standart_return:
                    return standart_return
                return {'status': False, 'error': 100}
            if secure_args:
                for arg in args:
                    if secure_sql(arg):
                        return {'status': False, 'error': 401}
                for kw in kwargs:
                    if secure_sql(kwargs[kw]):
                        return {'status': False, 'error': 401}
            res = func(*args, **kwargs)
            return res
        return wrapper
    return active_decorator

@sql_decorator()
def create_table(name_class, name_atribute, type_atribute, len_varchar=50):
    table_name = f'CLS_{name_class}_ATR_{name_atribute}'
    table_atribute = ''
    if type_atribute == str:
        table_atribute = f'VARCHAR({len_varchar})'
    elif type_atribute in (int, float, bool):
        table_atribute = type_atribute.__name__.upper()
    elif db_container.cheaker.this_db_atribute_container_class(type_atribute, this_is_cls=True):
        table_atribute = 'JSON'
    if not table_atribute:
        return {'status': False, 'error': 300}
    cur.execute(f"""CREATE TABLE {table_name}(id INT PRIMARY KEY, {name_atribute} {table_atribute})""")
    conn.commit()

if __name__ == "__main__":
    create_table(name_class='user', name_atribute='name', type_atribute=str)