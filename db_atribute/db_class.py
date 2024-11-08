import copy, ast, functools, inspect, sys
import datetime
import pickle
import json as json
import collections

def MethodDecorator(func=None, /, convert_arguments=True, call_the_decoreted_func=False, call_update_obj=True):
    """
    decorator for methods, where updated obj | args can convert
    :param convert_arguments: if True (default), convert all arguments from args and kwargs to DbClass objects (if this type obj is supported) (not convert if this class methode)
    :param call_the_decoreted_func: if False (default), call this func from self._standart_class, if True, call from self.__class__
    :param call_update_obj: if True (default), call the self._update_obj(), set False if func not updated the obj
    :return:
    """
    def wrap(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if convert_arguments:
                args = (cheaker.create_db_class(i, _first_container=self._first_container if self._first_container else _FirstContainer(self)) for i in args)
                kwargs = {key: cheaker.create_db_class(kwargs[key], _first_container=self._first_container if self._first_container else _FirstContainer(self)) for key in kwargs}

            if call_the_decoreted_func:
                data = func(self, *args, **kwargs)
                if call_update_obj:
                    self._update_obj()
                return data

            data = getattr(self._standart_class, func.__name__)(self, *args, **kwargs)
            if call_update_obj:
                self._update_obj()
            return data
        return wrapper
    if func:
        return wrap(func)
    return wrap

def LoadDecorator(func=None, /, *, auto_step1=True, auto_step2=True, auto_step3=True, step1=None, step2=None, step3=None):
    """
    the all db class objects dumped in json, structure:
    key 't': type - type of this obj, example: {'t': DbList, 'd': [1, 2, 3]}
    key 'd': data - main data,
    example1 (DbDict): {'t': DbDict, 'd': {'0': 1, '1': 2, '2': 3}, 'dk': {'0': 'int', '1': 'int', '2': 'int'}}
    example2 (Develp's Db Class): {'t': DbUserClass, 'd': {'name': *name*, 'age': *age*, 'books': *jsonDbList*}}
    *and others keys | Develop's keys*
    key 'dk': data key (used DbDict)
    Develop ken create his own keys in dump, and use in load

    use yield for loads function

    example for realisation step1:

    @classmethod
    @LoadDecorator(auto_step1=False)
    def func(cls, *args, **kwargs):
        data, _obj_dbatribute, _name_atribute, _first_container = yield
        self = cls.__new__(cls=cls, _use_db=True)
        yield self, data, _obj_dbatribute, _name_atribute, _first_container

    realisation of DbDict:
    @classmethod
    @LoadDecorator(auto_step2=False, auto_step3=False)
    def loads(cls, *args, **kwargs):
        self, data, _obj_dbatribute, _name_atribute, _first_container = yield
        newdata = {convert_json_key_to_atr_key(key, data['dk'][key] if key in data['dk'] else None)
                : conver_json_value_to_atr_value(value, data['dt'][key] if key in data['dt'] else None, _first_container=_first_container)
                for key, value in data['d'].items()}
        self.__init__(newdata, _use_db=True, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        yield data, _obj_dbatribute, _name_atribute, _first_container

    example for realisation step1+step3:

    @classmethod
    @LoadDecorator(auto_step1=False, auto_step3=False)
    def func(cls, *args, **kwargs):
        #step1
        data, _obj_dbatribute, _name_atribute, _first_container = yield
        self = cls.__new__(cls=cls, _use_db=True)
        self, newdata, _obj_dbatribute, _name_atribute, _first_container = yield self, data, _obj_dbatribute, _name_atribute, _first_container
        #not 'yield self, data, _obj_dbatribute, _name_atribute, _first_container'
        #step 3
        self.__init__(newdata, _use_db=True, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        yield

    example for realisation step1+step2:

    @classmethod
    @LoadDecorator(auto_step1=False, auto_step2=False)
    def func(cls, *args, **kwargs):
        #step1
        data, _obj_dbatribute, _name_atribute, _first_container = yield
        self = cls.__new__(cls=cls, _use_db=True)
        self, data, _obj_dbatribute, _name_atribute, _first_container = yield data, _obj_dbatribute, _name_atribute, _first_container
        #or use 'not_used_data = yield data, _obj_dbatribute, _name_atribute, _first_container'
        #or use 'yield data, _obj_dbatribute, _name_atribute, _first_container'
        #step2
        data = [conver_json_value_to_atr_value(value, data['dt'][str(key)] if str(key) in data['dt'] else None, _first_container=_first_container)
                for key, value in enumerate(data['d'])]
        yield data, _obj_dbatribute, _name_atribute, _first_container

    if any auto_step is True, decorator call step1|step2|step3 (this functions not decorator!)

    standart auto_step1:
    def step1(cls, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        obj = cls.__new__(cls=cls, _use_db=True)
        if _first_container is None:
            _first_container = obj
        return obj, data, _obj_dbatribute, _name_atribute, _first_container

    standart auto_step2:
    def step2(cls, self, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        data = {key: conver_json_value_to_atr_value(value, data['dt'][key] if key in data['dt'] else None, _first_container=_first_container)
                for key, value in data['d'].items()}
        return data, _obj_dbatribute, _name_atribute, _first_container

    standart auto_step3:
    def step3(cls, self, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        self.__init__(**data, _use_db=True, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)

    *for args in steps: other args is _obj_dbatribute, _name_atribute, _first_container*

    :param func:
    :param auto_step1: step, where create obj (no init, only __new__) (and replace _first_container if is None). call for 2nd step: (data: json, *other args*), send back: (self (this obj | cls.__new__), data: json, *other args*)
    :param auto_step2: step, where load the data. call for 3rd step: (self, data: json, *other args*), send back: (data: Any (list | dict | set | *other*), *other args*)
    :param auto_step3: step, where call obj.__init__. call for 4th step: (self, data, *other args*), send back: ()
    :param step1: if you don't use auto_step1, tou can replace step1 function
    :param step2: if you don't use auto_step1, tou can replace step1 function
    :param step3: if you don't use auto_step1, tou can replace step1 function
    :return:
    """
    def standart_step1(cls, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        obj = cls.__new__(cls, _use_db=True)
        if _first_container is None:
            _first_container = obj
        return obj, data, _obj_dbatribute, _name_atribute, _first_container

    def standart_step2(cls, self, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        data = {key: conver_json_value_to_atr_value(value, _first_container=_first_container)
                for key, value in data['d'].items()}
        return data, _obj_dbatribute, _name_atribute, _first_container

    def standart_step3(cls, self, data, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
        self.__init__(**data, _use_db=True, _cheak_data=False, _copy_data=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)

    def wrap(func):
        def metode_func(cls, s: str, _obj_dbatribute=None, _name_atribute=None, _first_container=None, *args, **kwargs):
            generator = func(cls, *args, **kwargs)
            first_run = True
            if isinstance(s, str):
                tempdata = json.loads(s)
            else:
                tempdata = s
            if not(isinstance(tempdata, dict) and 'd' in tempdata and 't' in tempdata and 'dt' in tempdata and tempdata['t'] == cls.__name__):
                return {'status_code': 400}

            if auto_step1:
                if step1:
                    self, tempdata, _obj_dbatribute, _name_atribute, _first_container = step1(cls, tempdata, _obj_dbatribute, _name_atribute, _first_container)
                else:
                    self, tempdata, _obj_dbatribute, _name_atribute, _first_container = standart_step1(cls, tempdata, _obj_dbatribute, _name_atribute, _first_container)
            else:
                if first_run:
                    next(generator)
                    first_run = False
                self, tempdata, _obj_dbatribute, _name_atribute, _first_container = generator.send((tempdata, _obj_dbatribute, _name_atribute, _first_container))

            if auto_step2:
                if step2:
                    data, _obj_dbatribute, _name_atribute, _first_container = step2(cls, self, tempdata, _obj_dbatribute, _name_atribute, _first_container)
                else:
                    data, _obj_dbatribute, _name_atribute, _first_container = standart_step2(cls, self, tempdata, _obj_dbatribute, _name_atribute, _first_container)
            else:
                if first_run:
                    next(generator)
                    first_run = False
                data, _obj_dbatribute, _name_atribute, _first_container = generator.send((self, tempdata, _obj_dbatribute, _name_atribute, _first_container))

            if auto_step3:
                if step3:
                    step3(cls, self, data, _obj_dbatribute, _name_atribute, _first_container)
                else:
                    standart_step3(cls, self, data, _obj_dbatribute, _name_atribute, _first_container)
            else:
                if first_run:
                    next(generator)
                generator.send((self, data, _obj_dbatribute, _name_atribute, _first_container))
            return self
        return metode_func
    if func is None:
        return wrap
    return wrap(func)

def DbClassDecorator(cls):
    if len(cls.__mro__) == 2 or (not issubclass(cls.__mro__[1], DbClass)):
        cls._standart_class = cls.__mro__[1]
    else:
        cls._standart_class = cls.__mro__[2]

    def getimethod(truefunc):
        def wrapper(self, *args, _update=True, **kwargs):
            obj = truefunc(self, *args, **kwargs)
            if _update and isinstance(obj, DbClass): obj._update_obj()
            return obj
        return wrapper

    def getmethod(truefunc):
        def wrapper(self, *args, _update=True, **kwargs):
            data = truefunc(self, *args, **kwargs)
            if _update: self._update_obj()
            return data
        return wrapper

    for namefunc in ['__iadd__', '__isub__', '__imul__', '__imatmul__', '__ipow__', '__idiv__', '__ifloordiv__', '__itruediv__', '__ilshift__', '__irshift__', '__imod__', '__ior__', '__iand__', '__ixor__']:
        if hasattr(cls, namefunc) and namefunc not in cls.__dict__:
            func = getimethod(getattr(cls, namefunc))
            setattr(cls, namefunc, func)
    for namefunc in ['__setitem__', '__delitem__', '__setattr__', '__delattr__']:
        if hasattr(cls, namefunc) and namefunc not in cls.__dict__:
            func = getmethod(getattr(cls, namefunc))
            setattr(cls, namefunc, func)
    return cls

class _FirstContainer:
    def __init__(self, _first_container=None):
        self.container = _first_container.container if isinstance(_first_container, _FirstContainer) else _first_container

@DbClassDecorator
class DbClass:
    _standart_class = object
    _obj_dbatribute = None
    _name_atribute = None
    _first_container = None
    _call_init_when_reconstruct = False

    @staticmethod
    def __method_decorator(func):
        func.truefunc = None
        @functools.wraps(func)
        def wrapper(self, *args, _update=True, **kwargs):
            data = func.truefunc(self, *args, **kwargs)
            if _update: self._update_obj()
            return data
        return wrapper

    @staticmethod
    def __imethod_decorator(func):
        func.truefunc = None
        @functools.wraps(func)
        def wrapper(self, *args, _update=True, **kwargs):
            obj = func.truefunc(self, *args, **kwargs)
            if _update and isinstance(obj, DbClass): self._update_obj()
            return obj
        return wrapper

    def __new__(cls, *args, _use_db=False, _obj_dbatribute=None, _convert_arguments=True, _name_atribute=None, _first_container=None, **kwargs):
        if not _use_db:
            obj = cls._standart_class.__new__(cls._standart_class, *args, **kwargs)
            obj.__init__(*args, **kwargs)
            return obj
        return cls._standart_class.__new__(cls, *args, **kwargs)

    def __init__(self, *args, _call_super_init=True, _use_db=False, _obj_dbatribute=None, _convert_arguments=True, _name_atribute=None, _first_container=None, **kwargs):
        """
        set _obj_dbatribute, _name_atribute, _first_container, call super().__init__(*args, **kwargs)
        if _convert_arguments is True, convert all atributes from args and kwargs to DbClass for super().__init__(*args, **kwargs)
        :param _call_super_init: (this parametr only for call DbClass __init__, don't use it for your class __init__) if True, the DbClass.__init__ call super().__init__(*args, **kwargs)
        """
        if _obj_dbatribute:
            self.__dict__['_obj_dbatribute'] = _obj_dbatribute
        if _name_atribute:
            self.__dict__['_name_atribute'] = _name_atribute
        if self._first_container is None:
            if _first_container is None:
                self.__dict__['_first_container'] = _FirstContainer(self)
            else:
                self.__dict__['_first_container'] = _first_container
        if _call_super_init and _convert_arguments:
            args = (cheaker.create_db_class(i, _first_container=self._first_container) for i in args)
            kwargs = {key: cheaker.create_db_class(kwargs[key], _first_container=self._first_container) for key in kwargs}
        if _call_super_init:
            super().__init__(*args, **kwargs)

    def __reduce_ex__(self, protocol):
        temp = super().__reduce_ex__(protocol)
        if len(temp) >= 3 and temp[2] is not None:
            temp = list(temp)
            temp[2] = {key: convert_atr_value_to_json_value(temp[2][key]) for key in temp[2] if key not in {'_obj_dbatribute', '_name_atribute', '_first_container'}}
            if len(temp[2]) == 0:
                temp[2] = None
            temp = tuple(temp)
        return temp

    def _update_obj(self):
        #print(f'update {self} {self._first_container.container if self._first_container else self._first_container}')
        if self._first_container and self._first_container.container and self._first_container.container._obj_dbatribute:
            self._first_container.container._obj_dbatribute._db_atribute_container_update(self._first_container.container._name_atribute, self._first_container.container)

    def dumps(self, _return_json=True):
        """
        key 't': type - type of this obj, example: {'t': DbList, 'd': [1, 2, 3]}
        key 'd': data - main data,
        example1 (DbDict): {'t': DbDict, 'd': {'0': 1, '1': 2, '2': 3}, 'dk': {'0': 'int', '1': 'int', '2': 'int'}}
        example2 (Develp's Db class): {'t': DbUserClass, 'd': {'name': *name*, 'age': *age*, 'books': *jsonDbList*}}
        *and others keys | Develop's keys*
        key 'dk': data key (used DbDict)
        Develop ken create his own keys in dump, and use in load
        """
        data = pickle.dumps(self).decode('latin1')
        if _return_json:
            return json.dumps({'t': self.__class__.__name__, 'd': data})
        return {'t': self.__class__.__name__, 'd': data}

    @classmethod
    def loads(cls, tempdata: str | dict, *, _call_the_super=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        """
        if you create loads methode in tour 'Db class', type(tempdata) is dict (not str)
        please, in first line write:
        'if _call_the_super: return super().loads(tempdata, _call_the_super=_call_the_super, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)'
        because
        1) the DbClass.loads call the loads func if the tempdata['t'] is your class
        example: your class is 'DbMyClass', but tempdata is {'t': 'DbOtherClass', ...},
        and the DbClass.loads don't call the DbMyClass.loads, it's call the DbOtherClass.loads(tempdata, _call_the_super=False, ...)
        2) the DbClass.loads replace tempdata for json.loads(tempdata), if isinstance(tempdata, str)
        example: tempdata = '{...}' (not {...})

        for create loads methode you can:
        1) see the loads methodes of DbList, DbDict, DbDatetime and other...
        2) see the LoadDecorator

        :param tempdata: the dumps obj, example: tempdata = {'t': DbList, 'd': [1, 2, 3]}, or json.loads(tempdata) = {'t': DbList, 'd': [1, 2, 3]}
        :param _call_the_super: uses, when the DbClass call the loads func from tempdata['t'] (cls of dumps obj)
        :param _obj_dbatribute: link to dbatribute obj
        :param _name_atribute: name this atribute
        :param _first_container: link to 'first container', example: a = [1, [2]] for [2] the 'first container' the [1, [2]]
        :return:
        """
        if isinstance(tempdata, str):
            temp = json.loads(tempdata)
        else:
            temp = tempdata
        if (not isinstance(temp, dict)) or 't' not in temp:
            raise Exception(
                f"load error: {temp} is not dict or don't have the 't' key"
            )
        if temp['t'] not in cheaker.db_class_name_to_db_class:
            raise Exception(
                f"load error: cheaker don't support the {temp['t']}, add this class to cheaker"
            )
        loadcls = cheaker.db_class_name_to_db_class[temp['t']]
        if loadcls.__dict__.get('loads', None):
            return loadcls.loads(temp, _call_the_super=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return cheaker.create_db_class(pickle.loads(temp['d'].encode('latin1')), _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)

@DbClassDecorator
class DbList(DbClass, list):
    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None, **kwargs):
        super().__init__(*args, _call_super_init=False, _use_db=_use_db, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container, **kwargs)
        iterable = list(args[0])
        if _convert_arguments:
            iterable = [cheaker.create_db_class(i, _first_container=self._first_container) for i in iterable]
        list.__init__(self, iterable)

    @MethodDecorator
    def append(self, item, /): pass
    @MethodDecorator
    def insert(self, i, item): pass
    @MethodDecorator
    def pop(self, i=-1): pass
    @MethodDecorator
    def remove(self, item): pass
    @MethodDecorator
    def clear(self): pass
    @MethodDecorator
    def reverse(self): pass
    @MethodDecorator
    def sort(self, /, key=None, reverse=False): pass
    @MethodDecorator
    def extend(self, other): pass

    def dumps(self, _return_json=True):
        data = [convert_atr_value_to_json_value(i) for i in self]
        if _return_json:
            return json.dumps({'t': self.__class__.__name__, 'd': data})
        return {'t': self.__class__.__name__, 'd': data}

    @classmethod
    def loads(cls, tempdata: dict, *, _call_the_super=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        if _call_the_super: return super().loads(tempdata, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        obj = cls.__new__(cls, _use_db=True)
        if _first_container is None:
            _first_container = _FirstContainer(obj)
        data = [conver_json_value_to_atr_value(value, _first_container=_first_container) for value in tempdata['d']]
        obj.__init__(data, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

@DbClassDecorator
class DbSet(DbClass, set):
    _call_init_when_reconstruct = True

    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None, **kwargs):
        super().__init__(*args, _call_super_init=False, _use_db=_use_db, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container, **kwargs)
        iterable = set(args[0])
        if _convert_arguments:
            iterable = {cheaker.create_db_class(i, _first_container=self._first_container) for i in iterable}
        set.__init__(self, iterable)

    def __repr__(self):
        return set(self).__repr__()

    @MethodDecorator
    def add(self, __element, /): pass
    @MethodDecorator
    def remove(self, __element, /): pass
    @MethodDecorator
    def discard(self, __element, /): pass
    @MethodDecorator
    def update(self, *s): pass
    @MethodDecorator
    def difference_update(self, *s): pass
    @MethodDecorator
    def intersection_update(self, *s): pass
    @MethodDecorator
    def symmetric_difference_update(self, __s, /): pass

    def dumps(self, _return_json=True):
        data = [convert_atr_value_to_json_value(i) for i in self]
        if _return_json:
            return json.dumps({'t': self.__class__.__name__, 'd': data})
        return {'t': self.__class__.__name__, 'd': data}

    @classmethod
    def loads(cls, tempdata: dict, *, _call_the_super=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        if _call_the_super: return super().loads(tempdata, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        obj = cls.__new__(cls, _use_db=True)
        if _first_container is None:
            _first_container = _FirstContainer(obj)
        data = {conver_json_value_to_atr_value(value, _first_container=_first_container) for value in tempdata['d']}
        obj.__init__(data, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

@DbClassDecorator
class DbDict(DbClass, dict):
    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None, **kwargs):
        super().__init__(*args, _call_super_init=False, _use_db=_use_db, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container, **kwargs)
        iterable = dict(args[0]) | kwargs
        if _convert_arguments:
            iterable = {key: cheaker.create_db_class(iterable[key], _first_container=self._first_container) for key in iterable}
        dict.__init__(self, iterable)

    @MethodDecorator
    def clear(self): pass
    @MethodDecorator
    def pop(self, __key, /): pass
    @MethodDecorator
    def popitem(self): pass
    @MethodDecorator
    def update(self, __m, /, **kwargs): pass

    def dumps(self, _return_json=True):
        data = {convert_atr_key_to_json_key(i): convert_atr_value_to_json_value(self[i]) for i in self}
        data_key = {convert_atr_key_to_json_key(key): key.__class__.__name__ for key in self if key.__class__ in [tuple, int, bool]}
        if _return_json:
            return json.dumps({'t': self.__class__.__name__, 'dk': data_key, 'd': data})
        return {'t': self.__class__.__name__, 'dk': data_key, 'd': data}

    @classmethod
    def loads(cls, tempdata, *, _call_the_super=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        if _call_the_super: return super().loads(tempdata, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        obj = cls.__new__(cls, _use_db=True)
        if _first_container is None:
            _first_container = _FirstContainer(obj)
        data = {convert_json_key_to_atr_key(key, tempdata['dk'][key] if key in tempdata['dk'] else None)
                : conver_json_value_to_atr_value(value, _first_container=_first_container)
                for key, value in tempdata['d'].items()}
        obj.__init__(data, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

@DbClassDecorator
class DbTuple(DbClass, tuple):
    _call_init_when_reconstruct = True
    def __new__(cls, *args, _use_db=False, _loads_iterable=False, _obj_dbatribute=None, _convert_arguments=True, _name_atribute=None, _first_container=None, **kwargs):
        if not _use_db:
            return DbClass.__new__(DbTuple, *args, **kwargs)

        if _first_container is None:
            _first_container = _FirstContainer()

        iterable = tuple(args[0])
        if (not _loads_iterable) and _convert_arguments:
            iterable = tuple((cheaker.create_db_class(i, _first_container=_first_container) for i in iterable))
        if _loads_iterable:
            iterable = tuple((conver_json_value_to_atr_value(value, _first_container=_first_container) for value in iterable))

        obj = tuple.__new__(DbTuple, iterable)
        if _first_container.container is None:
            _first_container.container = obj
        obj.__dict__['_first_container'] = _first_container
        return obj

    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None, **kwargs):
        super().__init__(*args, _call_super_init=False, _use_db=_use_db, _convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container, **kwargs)

    def __iadd__(self, other):
        obj = self.__class__(self.__add__(other), _use_db=True, _obj_dbatribute=self._obj_dbatribute, _name_atribute=self._name_atribute, _first_container=self._first_container)
        if self._first_container.container is self:
            obj.__dict__['_first_container'].container = obj
        return obj

    def dumps(self, _return_json=True):
        data = [convert_atr_value_to_json_value(i) for i in self]
        if _return_json:
            return json.dumps({'t': self.__class__.__name__, 'd': data})
        return {'t': self.__class__.__name__, 'd': data}

    @classmethod
    def loads(cls, tempdata: dict, *, _call_the_super=True, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        if _call_the_super: return super().loads(tempdata, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        obj = cls.__new__(cls, tempdata['d'], _use_db=True, _loads_iterable=True, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        obj.__init__(_convert_arguments=False, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

class Dbfrozenset(DbClass, frozenset): pass

class DbDeque(DbClass, collections.deque): pass

class DbDatetime(DbClass, datetime.datetime): pass

class DbDate(DbClass, datetime.date): pass

class DbTime(DbClass, datetime.time): pass

class DbTimedelta(DbClass, datetime.timedelta): pass

class Cheaker:
    """
    cheak, if this class is db_class. Convert obj if his class is db_class. And other.

    db_class_name_to_db_class: {'DbList': DbList, 'DbSet': DbSet, 'DbDict': DbDict} | *other db classes*
    class_name_to_db_class = {'list': DbList, 'dict': DbDict, 'set': DbSet} | *other db classes*
    class_to_db_class = {list: DbList, dict: DbDict, set: DbSet} | *other db classes*
    """
    def __init__(self, _db_classes:dict = None):
        """
        :param _db_classes: example: {datetime.datetime: DbDatetime}
        :type _db_classes: dict
        """
        self._db_classes = _db_classes
        if not _db_classes:
            self._db_classes = dict()
        self.db_class_name_to_db_class = {self._db_classes[i].__name__ : self._db_classes[i] for i in self._db_classes}
        self.class_name_to_db_class = {i.__name__: self._db_classes[i] for i in self._db_classes}
        self.db_class_name_to_clasic_class = {self._db_classes[i].__name__: i for i in self._db_classes}


    def set_db_classes(self, _db_classes: dict):
        """
        :param _db_classes: example: {datetime.datetime: DbDatetime}
        :type _db_classes: dict
        """
        self._db_classes = _db_classes
        if not _db_classes:
            self._db_classes = dict()
        self.db_class_name_to_db_class = {self._db_classes[i].__name__ : self._db_classes[i] for i in self._db_classes}
        self.class_name_to_db_class = {i.__name__: self._db_classes[i] for i in self._db_classes}
        self.db_class_name_to_clasic_class = {self._db_classes[i].__name__: i for i in self._db_classes}

    def add_db_class(self, _db_class: tuple):
        """:param _db_class: example: (datetime.datetime: DbDatetime)"""
        self._db_classes[_db_class[0]] = _db_class[1]
        self.db_class_name_to_db_class[_db_class[1].__name__] = _db_class[1]
        self.class_name_to_db_class[_db_class[0].__name__] = _db_class[1]
        self.db_class_name_to_clasic_class[_db_class[1].__name__] = _db_class[0]

    def remove_db_class(self, name_clasic_class=None, name_db_class=None):
        if name_clasic_class is None and name_db_class is None:
            return
        if name_db_class:
            name_clasic_class = self.db_class_name_to_clasic_class[name_db_class].__name__
        elif name_clasic_class:
            name_db_class = self.class_name_to_db_class[name_clasic_class].__name__
        db_class = self.db_class_name_to_db_class[name_db_class]
        del self._db_classes[db_class]
        del self.db_class_name_to_db_class[name_db_class]
        del self.class_name_to_db_class[name_clasic_class]
        del self.db_class_name_to_clasic_class[name_db_class]

    def create_any_db_classes(self, *objs, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        """
        Use for create db_class from other classes. example: from list to DbList, but from int to int.
        :param objs: example: [123, '535', {8, 4, 6} #it's set , {1: 2} # it's dict]
        :param _obj_dbatribute:
        :return: example: [123, '535', {8, 4, 6} #it's DbSet , {1: 2} # it's DbDict]
        """
        return [self.create_db_class(objs[i], _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container) for i in range(len(objs))]

    def create_db_class(self, obj, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        if type(obj) in self._db_classes:
            reductor = getattr(obj, "__reduce_ex__", None)
            if reductor is not None:
                rv = reductor(4)
            else:
                reductor = getattr(obj, "__reduce__", None)
                if reductor:
                    rv = reductor()
                else:
                    raise Exception(f"uncopyable object of type {type(obj)}")
            if isinstance(rv, str):
                raise Exception(f"uncopyable object of type {type(obj)}")
            rv = list(rv)
            if rv[0].__name__ == '__newobj__':
                rv[0] = __newobj__
            elif rv[0].__name__ == '__newobj_ex__':
                rv[0] = __newobj_ex__
            else:
                rv[0] = __newobj__
                rv[1] = (1,) + rv[1]
            rv[1] = (self._db_classes[type(obj)],) + rv[1][1:]
            obj = self._reconstruct(*rv,  _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
        return obj

    def _reconstruct(self, func, args, state=None, listiter=None, dictiter=None, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
        y = func(*args)
        if _first_container is None:
            _first_container = _FirstContainer(y)
        if y._call_init_when_reconstruct:
            y.__init__(*args[1:])
        if state is not None:
            if hasattr(y, '__setstate__'):
                y.__setstate__(state)
            else:
                if isinstance(state, tuple) and len(state) == 2:
                    state, slotstate = state
                else:
                    slotstate = None
                if state is not None:
                    state = {key: self.create_db_class(state[key], _first_container=_first_container) for key in state}
                    y.__dict__.update(state)
                if slotstate is not None:
                    slotstate = {key: self.create_db_class(slotstate[key], _first_container=_first_container) for key in slotstate}
                    for key, value in slotstate.items():
                        setattr(y, key, value)
        if listiter is not None:
            for item in listiter:
                y.append(self.create_db_class(item, _first_container=_first_container))
        if dictiter is not None:
            for key, value in dictiter:
                y[key] = self.create_db_class(value, _first_container=_first_container)
        temp = {'_first_container': _first_container}
        if _obj_dbatribute:
            temp['_obj_dbatribute'] = _obj_dbatribute
        if _name_atribute:
            temp['_name_atribute'] = _name_atribute
        if hasattr(y, '__dict__'):
            y.__dict__.update(temp)
        else:
            for key, value in temp.items():
                setattr(y, key, value)
        return y

    def this_support_class(self, obj, this_is_cls=False):
        if this_is_cls:
            return obj in self._db_classes
        return type(obj) in self._db_classes

    def this_db_atribute_support_class(self, obj, this_is_cls=False):
        if this_is_cls:
            return obj in self._db_classes.values()
        return type(obj) in self._db_classes.values()

def __newobj_ex__(cls, args, kwargs):
    return cls.__new__(cls, *args, *kwargs, _use_db=True)
def __newobj__(cls, *args):
    obj = cls.__new__(cls, *args, _use_db=True)
    return obj

def convert_atr_value_to_json_value(value):
    return value.dumps(_return_json=False) if cheaker.this_db_atribute_support_class(value) else value

def conver_json_value_to_atr_value(value, _obj_dbatribute=None, _name_atribute=None, _first_container=None):
    if type(value) == dict:
        return DbClass.loads(value, _obj_dbatribute=_obj_dbatribute, _name_atribute=_name_atribute, _first_container=_first_container)
    return value

def convert_atr_key_to_json_key(key):
    """For DbDict"""
    res = key
    if key.__class__ == tuple:
        res = str(key)
    elif key.__class__ == bool:
        res = ' True ' if key else ' False '
    return res

def convert_json_key_to_atr_key(key, type_key):
    """For DbDict"""
    if type_key == 'int':
        return int(key)
    if type_key == 'tuple':
        return ast.literal_eval(str(key))
    if type_key == 'bool':
        return True if key == ' True ' else False
    return key

cheaker = Cheaker({set: DbSet, list: DbList, dict: DbDict, tuple: DbTuple})

if __name__ == "__main__":
    print(0)
    A = DbTuple([[1], 2, 3], _use_db = True)
    A += (4,)
    A[0].append(2)
    if A[0]._first_container.container is not A or A != ([1, 2], 2, 3, 4):
        print(A, type(A))
        print(A[0], type(A[0]))
        print(A[0]._first_container.container)

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
    if a != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or b != [1, 4, 3, 2, 4, 1] or c != {1, 2, 4} or type(a) != dict or type(b) != list or type(c) != set:
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
    if type(a) != dict or type(b) != list or A != {0: [1, 4, {1}], 1: {2}, 2: {5: 6}, 3: 4} or B != [[1], [4], [3], {2: [5]}, {1, 3, 4}] or a != {0: [3, 4, {1}], 1: {2}, 2: {5: 6}, 3: 4} or b != [[1], [4], [3], {2: [5], 1: 4}, {1, 3, 4}]:
        print(A, type(A))
        print(B, type(B))
        print(a, type(a))
        print(b, type(b))
    print(8)
    A = DbDict({0: [1, 4, {1}], 1: {2}, 2: {5:6}, 3: (7, 8), 4: True, 5: False, (6, 7): [1, 2], '8': [1]}, _use_db = True)
    B = DbList([{2:[5]}, [1], [4], [3], {1, 3, 4}, True, True, (1, 2), (1, 2)], _use_db = True)
    C = DbSet([4, True, '/Hello\n', (1, 2)], _use_db = True)
    #print(C.dumps())
    a = DbClass.loads(A.dumps())
    b = DbClass.loads(B.dumps())
    c = DbClass.loads(C.dumps())
    if A != a:
        print('A')
        print(A.dumps(), type(A.dumps()))
        print(A, type(A))
        print(a, type(a))
    if B != b:
        print('B')
        print(B.dumps(), type(B.dumps()))
        print(B, type(B))
        print(b, type(b))
    if C != c:
        print('C')
        print(C.dumps(), type(C.dumps()))
        print(C, type(C))
        print(c, type(c))
    print(9)
    A = DbDict({0: [1, 4, {1}], 1: 0}, _use_db = True)
    B = DbTuple((1, 2, [3]), _use_db=True)
    print(DbTuple.loads(B.dumps()))
