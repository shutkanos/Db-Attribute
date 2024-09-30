import collections, json, copy, ast

import db_atribute.UserSet as UserSet

class DbContainer:
    _standart_class=object
    _obj_dbatribute=None
    _name_atribute=None
    _first_container=None
    data=None

    def __new__(cls, iterable=(), _use_db = False, *args, **kwargs):
        if not _use_db:
            obj = cls._standart_class.__new__(cls._standart_class)
            if cls._standart_class == dict:
                obj.__init__(iterable, **kwargs)
            else:
                obj.__init__(iterable)
            return obj
        #print(f'__new__ {cls=} {iterable=}')
        return super().__new__(cls)

    def init(self, iterable=(), _obj_dbatribute=None, _copy_data=True, _name_atribute=None, _first_container=None, set_data=True, *args, **kwargs):
        #print(iterable, type(_obj_dbatribute), type(_name_atribute))
        if _obj_dbatribute:
            self._obj_dbatribute = _obj_dbatribute
        if _name_atribute:
            self._name_atribute = _name_atribute
        if _first_container is None:
            self._first_container = self
        else:
            self._first_container = _first_container
        #print(iterable, type(_first_container))
        if set_data and isinstance(iterable, self.__class__):
            #_cheak_data don't cheak, because DbContainer is cheaked
            if _copy_data:
                self.__dict__['data'] = copy.deepcopy(iterable.data)
            else:
                self.__dict__['data'] = iterable.data
            return True
        return False

    def __copy__(self, *args, **kwargs):
        obj = self.__class__.__new__(self.__class__, iterable=copy.copy(self.data))
        if isinstance(obj, self._standart_class):
            return obj
        obj.__dict__.update(self.__dict__)
        return obj

    def __deepcopy__(self, *args, **kwargs):
        obj = self.__class__.__new__(self.__class__, iterable=copy.deepcopy(self.data))
        if isinstance(obj, self._standart_class):
            return obj
        obj.__dict__.update(self.__dict__)
        return obj

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'data':
            self.update_data()

    def update_data(self):
        if self._first_container and self._first_container._obj_dbatribute:
            self._first_container._obj_dbatribute._db_atribute_container_update(self._first_container._name_atribute, self._first_container)

    def dumps(self):
        data = [convert_atr_value_to_json_value(i) for i in self.data]
        data_value = {convert_atr_key_to_json_key(key): value.__class__.__name__ for key, value in enumerate(self.data) if value.__class__ == tuple}
        """
        'd': 'data' data: [1, [3, 6], 3] | {'1': 2}
        't': 'type this obj': 'DbDict' | 'DbSet' | ...
        'dt': 'data types': {'1': 'DbList'}
        'kt': 'keys types': {'1': int} (for DbDict)
        """
        return f'{"{"}"t": "{self.__class__.__name__}", "dt": {json.dumps(data_value)}, "d": {json.dumps(data)}{"}"}'

    @staticmethod
    def loads(s: str, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        temp_data = json.loads(s)
        if not(isinstance(temp_data, dict) and 'd' in temp_data and 't' in temp_data):
            return {'status_code': 400}
        return cheaker.db_class_name_to_db_class[temp_data['t']].loads(s, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)


class DbDict(DbContainer, collections.UserDict):
    _standart_class=dict

    def __init__(self, iterable=(), _use_db = False, _obj_dbatribute=None, _cheak_data=True, _copy_data=True, _name_atribute=None, _first_container=None, *args, **kwargs):
        temp_data = super().init(iterable=iterable, _obj_dbatribute=_obj_dbatribute, _copy_data=_copy_data, _name_atribute=_name_atribute, _first_container=_first_container)
        if temp_data: return
        if _cheak_data:
            if _copy_data:
                data = dict(iterable, **kwargs)
            else:
                data = iterable
            self.__dict__['data'] = data
            for i in data:
                if cheaker.this_container_class(data[i]):
                    self.__dict__['data'][i] = cheaker.create_one_db_class(data[i], _first_container=self._first_container)
        else:
            self.__dict__['data'] = dict(iterable, **kwargs) if _copy_data else iterable

    def __setitem__(self, key, item):
        data = super().__setitem__(key, cheaker.create_one_db_class(item, _first_container=self._first_container))
        self.update_data()
        return data

    def __delitem__(self, key):
        data = super().__delitem__(key)
        self.update_data()
        return data

    def clear(self):
        data = super().clear()
        self.update_data()
        return data

    def update(self, __m, **kwargs):
        return super().update(__m, **kwargs)

    def pop(self, __key):
        data = super().pop(__key)
        self.update_data()
        return data

    def popitem(self):
        data = super().popitem()
        self.update_data()
        return data

    def dumps(self):
        data = {convert_atr_key_to_json_key(key): convert_atr_value_to_json_value(self.data[key]) for key in self.data}
        data_value = {convert_atr_key_to_json_key(key): self.data[key].__class__.__name__ for key in self.data if self.data[key].__class__ == tuple}
        data_key = {convert_atr_key_to_json_key(key): key.__class__.__name__ for key in self.data if key.__class__ in [tuple, int, bool]}
        return json.dumps({'t': self.__class__.__name__, 'dt': data_value, 'dk': data_key, 'd': data})

    @classmethod
    def loads(cls, s: str, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        temp_data = json.loads(s)
        if not(isinstance(temp_data, dict) and 'd' in temp_data and 't' in temp_data and 'dt' in temp_data and 'dk' in temp_data and temp_data['t'] == cls.__name__):
            return {'status_code': 400}
        obj = cls.__new__(cls=cls, _use_db=True)
        if _first_container is None:
            _first_container = obj
        data = {convert_json_key_to_atr_key(key, temp_data['dk'][key] if key in temp_data['dk'] else None)
                : conver_json_value_to_atr_value(value, temp_data['dt'][key] if key in temp_data['dt'] else None, _first_container=_first_container)
                for key, value in temp_data['d'].items()}
        obj.__init__(data, _use_db=True, _cheak_data=False, _copy_data=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj


class DbList(DbContainer, collections.UserList):
    _standart_class=list

    def __init__(self, iterable=(), _use_db = False, _obj_dbatribute=None, _cheak_data=True, _copy_data=True, _name_atribute=None, _first_container=None, *args, **kwargs):
        temp_data = super().init(iterable=iterable, _obj_dbatribute=_obj_dbatribute, _copy_data=_copy_data, _name_atribute=_name_atribute, _first_container=_first_container)
        if temp_data: return
        if _cheak_data:
            if _copy_data:
                data = list(iterable)
            else:
                data = iterable
            self.__dict__['data'] = data
            for i in range(len(data)):
                if cheaker.this_container_class(data[i]):
                    self.__dict__['data'][i] = cheaker.create_one_db_class(data[i], _obj_dbatribute=_obj_dbatribute, _first_container=self._first_container)
        else:
            self.__dict__['data'] = list(iterable) if _copy_data else iterable

    def __setitem__(self, i, item):
        data = super().__setitem__(i, cheaker.create_one_db_class(item, _first_container=self._first_container))
        self.update_data()
        return data

    def __delitem__(self, i):
        data = super().__delitem__(i)
        self.update_data()
        return data

    def append(self, item):
        data = super().append(cheaker.create_one_db_class(item, _first_container=self._first_container))
        self.update_data()
        return data

    def insert(self, i, item):
        data = super().insert(i, cheaker.create_one_db_class(item, _first_container=self._first_container))
        self.update_data()
        return data

    def pop(self, i=-1):
        data = super().pop(i)
        self.update_data()
        return data

    def remove(self, item):
        data = super().remove(cheaker.create_one_db_class(item, _first_container=self._first_container))
        self.update_data()
        return data

    def clear(self):
        data = super().clear()
        self.update_data()
        return data

    def reverse(self):
        data = super().reverse()
        self.update_data()
        return data

    def sort(self, *args, key=None, reverse=False):
        if args:
            raise TypeError('sort() takes no positional arguments')
        data = super().sort(key=key, reverse=reverse)
        self.update_data()
        return data

    def extend(self, other):
        data = super().extend(other)
        self.update_data()
        return data

    @classmethod
    def loads(cls, s: str, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        temp_data = json.loads(s)
        if not(isinstance(temp_data, dict) and 'd' in temp_data and 't' in temp_data and 'dt' in temp_data and temp_data['t'] == cls.__name__):
            return {'status_code': 400}
        obj = cls.__new__(cls=cls, _use_db=True)
        if _first_container is None:
            _first_container = obj
        data = [conver_json_value_to_atr_value(value, temp_data['dt'][str(key)] if str(key) in temp_data['dt'] else None, _first_container=_first_container)
                for key, value in enumerate(temp_data['d'])]
        obj.__init__(data, _use_db=True, _cheak_data=False, _copy_data=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

class DbSet(DbContainer, UserSet.UserSet):
    _standart_class=set

    def __init__(self, iterable=(), _use_db = False, _obj_dbatribute=None, _cheak_data=True, _copy_data=True, _name_atribute=None, _first_container=None, *args, **kwargs):
        super().init(iterable=iterable, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container, set_data=False)
        if isinstance(iterable, self.__class__):
            self.__dict__['data'] = copy.deepcopy(iterable.data)
        else:
            self.__dict__['data'] = set(iterable)

    def add(self, __element):
        data = super().add(cheaker.create_one_db_class(__element, _first_container=self._first_container))
        self.update_data()
        return data

    def discard(self, __element):
        data = super().discard(cheaker.create_one_db_class(__element, _first_container=self._first_container))
        self.update_data()
        return data

    def update(self, *s):
        data = super().update(*cheaker.create_db_class(*s, _first_container=self._first_container))
        self.update_data()
        return data

    def difference_update(self, *s):
        data = super().difference_update(*s)
        self.update_data()
        return data

    def intersection_update(self, *s):
        data = super().intersection_update(*s)
        self.update_data()
        return data

    def symmetric_difference_update(self, __s):
        data = super().symmetric_difference_update(__s)
        self.update_data()
        return data

    @classmethod
    def loads(cls, s: str, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        temp_data = json.loads(s)
        if not(isinstance(temp_data, dict) and 'd' in temp_data and 't' in temp_data and 'dt' in temp_data and temp_data['t'] == cls.__name__):
            return {'status_code': 400}
        data = temp_data
        obj = cls.__new__(cls=cls, _use_db=True)
        if _first_container is None:
            _first_container = obj
        data = {conver_json_value_to_atr_value(value, data['dt'][str(key)] if str(key) in data['dt'] else None, _first_container=_first_container)
                for key, value in enumerate(data['d'])}
        obj.__init__(data, _use_db=True, _cheak_data=False, _copy_data=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

class Cheaker:
    """
    cheak, if this class is db_class. Convert obj if his class is db_class. And other.

    db_class_name_to_db_class: {'DbList': DbList, 'DbSet': DbSet, 'DbDict': DbDict} | *users db classes*
    class_name_to_db_class = {'list': DbList, 'dict': DbDict, 'set': DbSet} | *users db classes*
    class_to_db_class = {list: DbList, dict: DbDict, set: DbSet} | *users db classes*
    """
    def __init__(self, _users_db_classes:dict = None):
        """
        :param _users_db_classes: example: {datetime.datetime: DbDatetime}
        :type _users_db_classes: dict
        """
        self._users_db_classes = _users_db_classes
        if not _users_db_classes:
            self._users_db_classes = dict()
        self.db_class_name_to_db_class = {'DbList': DbList, 'DbSet': DbSet, 'DbDict': DbDict} | {self._users_db_classes[i.__name__] : i for i in self._users_db_classes}
        self.class_name_to_db_class = {'list': DbList, 'dict': DbDict, 'set': DbSet} | {i: self._users_db_classes[i.__name__] for i in self._users_db_classes}
        self.class_to_db_class = {list: DbList, dict: DbDict, set: DbSet} | self._users_db_classes


    def set_users_db_classes(self, _users_db_classes: dict):
        """
        :param _users_db_classes: example: {datetime.datetime: DbDatetime}
        :type _users_db_classes: dict
        """
        self._users_db_classes = _users_db_classes
        if not _users_db_classes:
            self._users_db_classes = dict()
        self.db_class_name_to_db_class = {'DbList': DbList, 'DbSet': DbSet, 'DbDict': DbDict} | {self._users_db_classes[i.__name__] : i for i in self._users_db_classes}


    def create_db_class(self, *objs, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        """
        Use for create db_class from other classes. example: from list to DbList, but from int to int.
        :param objs: example: [123, '535', {8, 4, 6} #it's set , {1: 2} # it's dict]
        :param _obj_dbatribute:
        :return: example: [123, '535', {8, 4, 6} #it's DbSet , {1: 2} # it's DbDict]
        """
        return [self.create_one_db_class(objs[i], _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container) for i in range(len(objs))]

    def create_one_db_class(self, obj, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        if isinstance(obj, dict):
            return DbDict(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        if isinstance(obj, list):
            return DbList(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        if isinstance(obj, set):
            return DbSet(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        for from_class, to_class in self._users_db_classes.items():
            if isinstance(obj, from_class):
                return to_class(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

    def this_container_class(self, obj, this_is_cls=False):
        if this_is_cls:
            return obj in [dict, list, set] or obj in self._users_db_classes
        return obj.__class__ in [dict, list, set] or obj.__class__ in self._users_db_classes

    def this_db_atribute_container_class(self, obj, this_is_cls=False):
        if this_is_cls:
            return obj in [DbDict, DbList, DbSet] or obj in self._users_db_classes.values()
        return obj.__class__ in [DbDict, DbList, DbSet] or obj.__class__ in self._users_db_classes.values()

def list_to_dict(obj):
    return {i: obj[i] for i in range(len(obj))}

def convert_atr_value_to_json_value(value):
    return value.dumps() if cheaker.this_db_atribute_container_class(value) else json.dumps(value)

def conver_json_value_to_atr_value(value, type_value, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
    res = json.loads(value)
    if type(res) == dict: #Db_class
        return DbContainer.loads(value, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
    if type_value == 'tuple':
        return tuple(res)
    return res

def convert_atr_key_to_json_key(key):
    """For DbDict"""
    res = key
    if key.__class__ == tuple:
        res = str(key)
    elif key.__class__ == bool:
        res = ' True ' if key else ' False '
    return json.dumps(res)

def convert_json_key_to_atr_key(key, type_key):
    """For DbDict"""
    res = json.loads(key)
    if type_key == 'int':
        return int(res)
    if type_key == 'tuple':
        return ast.literal_eval(str(res))
    if type_key == 'bool':
        return True if res == ' True ' else False
    return res

def LoadDecorator(func=None, /, *, auto_step1=True, auto_step2=True, auto_step3=True, auto_step4=True):
    """
    *for args in steps: other args is _obj_dbatribute, _name_atribute, _first_container*

    use yield for loads

    example for realisation step2:

    @classmethod
    @LoadDecorator(auto_step2=False)
    def func(cls, *args, **kwargs):
        data, _obj_dbatribute, _name_atribute, _first_container = yield
        self = cls.__new__(cls=cls, _use_db=True)
        yield self, data, _obj_dbatribute, _name_atribute, _first_container

    example for realisation step1+step3:

    @classmethod
    @LoadDecorator(auto_step2=False)
    def func(cls, *args, **kwargs):
        #step1
        s, _obj_dbatribute, _name_atribute, _first_container = yield
        data = json.loads(s)
        self, data, _obj_dbatribute, _name_atribute, _first_container = yield data, _obj_dbatribute, _name_atribute, _first_container
        #step 3
        new_data = [conver_json_value_to_atr_value(value, type_value=data['dt'][str(key)] if str(key) in data['dt'] else None, _first_container=_first_container)
                    for key, value in enumerate(data['d'])]
        yield new_data, _obj_dbatribute, _name_atribute, _first_container

    example for realisation step1+step2:

    @classmethod
    @LoadDecorator(auto_step2=False)
    def func(cls, *args, **kwargs):
        #step1
        s, _obj_dbatribute, _name_atribute, _first_container = yield
        data = json.loads(s)
        yield data, _obj_dbatribute, _name_atribute, _first_container
        # or data, _obj_dbatribute, _name_atribute, _first_container = yield data, _obj_dbatribute, _name_atribute, _first_container
        #step 2
        self = cls.__new__(cls=cls, _use_db=True)
        yield self, data, _obj_dbatribute, _name_atribute, _first_container


    :param func:
    :param auto_step1: step, where str convert to json (and cheak: is correct data or not). call for 1st step: (s: str, *other args*) and send back: (data: json, *other args*)
    :param auto_step2: step, where create obj (no init, only __new__) (and replace _first_container if is None). call for 2nd step: (data: json, *other args*), send back: (self (this obj | cls.__new__), data: json, *other args*)
    :param auto_step3: step, where load the data. call for 3rd step: (self, data: json, *other args*), send back: (data: Any (list | dict | set | *other*), *other args*)
    :param auto_step4: step, where call obj.__init__. call for 4th step: (self, data, *other args*), send back: ()
    :return:
    """

    def step1(cls, s, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        data = json.loads(s)
        if not(isinstance(data, dict) and 'd' in data and 't' in data and 'dt' in data and data['t'] == cls.__name__):
            return 400
        return data, _obj_dbatribute, _name_atribute, _first_container

    def step2(cls, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        obj = cls.__new__(cls=cls, _use_db=True)
        if _first_container is None:
            _first_container = obj
        return obj, data, _obj_dbatribute, _name_atribute, _first_container

    def step3(cls, self, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        data = {conver_json_value_to_atr_value(value, data['dt'][str(key)] if str(key) in data['dt'] else None, _first_container=_first_container)
                for key, value in enumerate(data['d'])}
        return data, _obj_dbatribute, _name_atribute, _first_container

    def step4(cls, self, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        self.__init__(data, _use_db=True, _cheak_data=False, _copy_data=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)

    def wrap(func):
        def metode_func(cls, s: str, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
            generator = func(cls, *args, **kwargs)
            first_run = True
            if auto_step1:
                data, _obj_dbatribute, _name_atribute, _first_container = step1(cls, s, _obj_dbatribute, _name_atribute, _first_container)
            else:
                if first_run:
                    next(generator)
                    first_run = False
                data, _obj_dbatribute, _name_atribute, _first_container = generator.send(s, _obj_dbatribute, _name_atribute, _first_container)

            if auto_step2:
                self, data, _obj_dbatribute, _name_atribute, _first_container = step2(cls, data, _obj_dbatribute, _name_atribute, _first_container)
            else:
                if first_run:
                    next(generator)
                    first_run = False
                self, data, _obj_dbatribute, _name_atribute, _first_container = generator.send(data, _obj_dbatribute, _name_atribute, _first_container)

            if auto_step3:
                data, _obj_dbatribute, _name_atribute, _first_container = step3(cls, self, data, _obj_dbatribute, _name_atribute, _first_container)
            else:
                if first_run:
                    next(generator)
                    first_run = False
                data, _obj_dbatribute, _name_atribute, _first_container = generator.send(self, data, _obj_dbatribute, _name_atribute, _first_container)

            if auto_step4:
                step4(cls, self, data, _obj_dbatribute, _name_atribute, _first_container)
            else:
                if first_run:
                    next(generator)
                generator.send(self, data, _obj_dbatribute, _name_atribute, _first_container)
            return self
        return metode_func
    if func is None:
        return wrap
    return wrap(func)

def loads(s: str, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
    temp_data = json.loads(s)
    if not(isinstance(temp_data, dict) and 'd' in temp_data and 't' in temp_data):
        return {'status_code': 400}
    return cheaker.db_class_name_to_db_class[temp_data['t']].loads(s, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)

cheaker = Cheaker()




if __name__ == "__main__":

    print(1)
    A = DbDict([[0, 1], [1, 4], [2, 3], [3, 2], [4, 4]], _use_db = True)
    B = DbList([1, 4, 3, 2, 4], _use_db = True)
    C = DbSet([1, 4, 3, 2, 4], _use_db = True)
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4} or B != [1, 4, 3, 2, 4] or C != {1, 2, 3, 4}:
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(2)
    a = A | {8: 5}
    b = B + [1]
    c = C - {3}
    if a != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or b != [1, 4, 3, 2, 4, 1] or c != {1, 2, 4}:
        print(a, type(a))
        print(b, type(b))
        print(c, type(c))

    print(3)
    A |= {8: 5}
    B += [1]
    C -= {3}
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or B != [1, 4, 3, 2, 4, 1] or C != {1, 2, 4}:
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(4)
    A = DbDict([[0, 1], [1, 4], [2, 3], [3, 2], [4, 4]], _use_db = True)
    B = DbList([1, 4, 3, 2, 4], _use_db = True)
    C = DbSet([1, 4, 3, 2, 4], _use_db = True)
    A.update({8:5})
    B.append(1)
    C.remove(3)
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or B != [1, 4, 3, 2, 4, 1] or C != {1, 2, 4}:
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(5)
    A = DbDict([[0, 1], [1, 4], [2, 3], [3, 2], [4, 4]], _use_db = True)
    B = DbList([1, 4, 3, 2, 4], _use_db = True)
    C = DbSet([1, 4, 3, 2, 4], _use_db = True)
    a = dict(A)
    b = list(B)
    c = set(C)
    a |= {8: 5}
    b += [1]
    c -= {3}
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4} or B != [1, 4, 3, 2, 4] or C != {1, 2, 3, 4} or a != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or b != [1, 4, 3, 2, 4, 1] or c != {1, 2, 4} or a == A or b == B or c == C:
        print(a, type(a))
        print(b, type(b))
        print(c, type(c))
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(6)
    A = DbDict([[0, [1, 4, {1}]], [1, {2}], [2, {5:6}], [3, 4]], _use_db = True)
    B = DbList([[1], [4], [3], {2:[5]}, {1, 3, 4}], _use_db = True)
    C = DbSet([(1, 4), (3, 2), 4], _use_db = True)
    A[0][0] = 3
    del A[0][1]
    A[0][1].add(2)
    if A != {0: [3, {1, 2}], 1: {2}, 2: {5: 6}, 3: 4} or B != [[1], [4], [3], {2: [5]}, {1, 3, 4}] or C != {(3, 2), 4, (1, 4)} or type(A) != DbDict or type(B) != DbList or type(C) != DbSet:
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))
    print(7)
    A = DbDict([[0, [1, 4, {1}]], [1, {2}], [2, {5:6}], [3, 4]], _use_db = True)
    B = DbList([[1], [4], [3], {2:[5]}, {1, 3, 4}], _use_db = True)
    a = copy.deepcopy(A)
    b = copy.deepcopy(B)
    a[0][0] = 3
    b[3][1] = 4
    if A != {0: [1, 4, {1}], 1: {2}, 2: {5: 6}, 3: 4} or B != [[1], [4], [3], {2: [5]}, {1, 3, 4}] or a != {0: [3, 4, {1}], 1: {2}, 2: {5: 6}, 3: 4} or b != [[1], [4], [3], {2: [5], 1: 4}, {1, 3, 4}]:
        print(A, type(A))
        print(B, type(B))
        print(a, type(a))
        print(b, type(b))
    print(8)
    A = DbDict({0: [1, 4, {1}], 1: {2}, 2: {5:6}, 3: (7, 8), 4: True, 5: False, (6, 7): [1, 2], '8': [1]}, _use_db = True)
    B = DbList([{2:[5]}, [1], [4], [3], {1, 3, 4}, True, True, (1, 2), (1, 2)], _use_db = True)
    C = DbSet([(1, 4), (3, 2), 4, True, '/Hello\n'], _use_db = True)
    a = DbContainer.loads(A.dumps())
    b = DbContainer.loads(B.dumps())
    c = DbContainer.loads(C.dumps())
    #print(A.dumps())
    #e = json.loads(A.dumps())
    #print(e)
    #print(e['d']['"8"'])
    if A != a or B != b or C != c:
        print(A.dumps(), type(A.dumps()))
        print(A, type(A))
        print(a, type(a))
        print(B.dumps(), type(B.dumps()))
        print(B, type(B))
        print(b, type(b))
        print(C.dumps(), type(C.dumps()))
        print(C, type(C))
        print(c, type(c))
    print(9)
    A = DbDict({0: [1, 4, {1}], 1: {2}, True: 0}, _use_db = True)
    print(A)






