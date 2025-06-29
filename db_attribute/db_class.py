import copy, ast, functools, inspect, sys
import datetime
import pickle
import json
import orjson
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

def DbClassDecorator(cls=None, /, convert_arguments_ioperation_methodes=False, convert_arguments_changes_methodes=True, list_of_non_replaceable_methodes=None, list_of_methodes_with_converted_arguments=None, methode__new__needs_arguments=False):
    """
    Use DbClassDecorator for
    1) set cls._standart_class (example: for DbList standart class is list)
    2) automatic create __setitem__, __delitem__, __setattr__, __delattr__, __iadd__, __isub__, __imul__, __imatmul__, __ipow__, __idiv__, __ifloordiv__, __itruediv__, __ilshift__, __irshift__, __imod__, __ior__, __iand__, __ixor__
    (DbClassDecorator not created __add__, __sub__, __mul__ and other methodes!)
    If a class has any methods (example: __iadd__), these methods are not replaced.
    But if the parent class has these methods, they will be replaced.
    So use the list_of_non_replaceable_methodes to set a list of non-replaceable methods
    :param convert_arguments_ioperation_methodes: convert input arguments of i operation metodes (__iadd__) to DbClasses
    :param convert_arguments_changes_methodes: convert input arguments of changes metodes (__delitem__, __setattr__) to DbClasses
    :param list_of_non_replaceable_methodes: list of method names that belong to the parent class and will not be replaced by the decorator, ex: ['__iadd__']
    :param list_of_methodes_with_converted_arguments: list of methods that need to be individually replaced with arguments, but param convert_arguments... is False, ex: ['__iadd__']
    :return:
    """
    if list_of_non_replaceable_methodes is None:
        list_of_non_replaceable_methodes = []
    if list_of_methodes_with_converted_arguments is None:
        list_of_methodes_with_converted_arguments = []
    def wrapper(cls):
        if cls.__dict__.get('_standart_class', None) is None:
            ind = cls.__mro__.index(DbClass)
            if ind + 1 == len(cls.__mro__):
                raise f'The DbClass the last in {cls}.__mro__, please set _standart_class, or add perent to class'
            cls._standart_class = cls.__mro__[ind + 1]
        if cls.__dict__.get('_methode__new__needs_arguments', None) is None:
            cls._methode__new__needs_arguments = methode__new__needs_arguments

        def getimethod(truefunc, namefunc=''):
            convert_arguments = convert_arguments_ioperation_methodes
            if namefunc in list_of_methodes_with_converted_arguments:
                convert_arguments = True
            def wrapper(self, *args, _update=True, **kwargs):
                if convert_arguments:
                    args = (cheaker.create_db_class(i, _first_container=self._first_container) for i in args)
                    kwargs = {key: cheaker.create_db_class(kwargs[key], _first_container=self._first_container) for key in kwargs}
                obj = truefunc(self, *args, **kwargs)
                if _update and isinstance(obj, DbClass):
                    obj._update_obj()
                return obj
            return wrapper

        def getmethod(truefunc, namefunc=''):
            convert_arguments = convert_arguments_changes_methodes
            if namefunc in list_of_methodes_with_converted_arguments:
                convert_arguments = True
            def wrapper(self, *args, _update=True, **kwargs):
                if convert_arguments:
                    args = (cheaker.create_db_class(i, _first_container=self._first_container) for i in args)
                    kwargs = {key: cheaker.create_db_class(kwargs[key], _first_container=self._first_container) for key in kwargs}

                data = truefunc(self, *args, **kwargs)
                if _update: self._update_obj()
                return data
            return wrapper

        for namefunc in ['__iadd__', '__isub__', '__imul__', '__imatmul__', '__ipow__', '__idiv__', '__ifloordiv__', '__itruediv__', '__ilshift__', '__irshift__', '__imod__', '__ior__', '__iand__', '__ixor__']:
            if hasattr(cls, namefunc) and namefunc not in cls.__dict__ and namefunc not in list_of_non_replaceable_methodes:
                func = getimethod(getattr(cls, namefunc), namefunc)
                setattr(cls, namefunc, func)
        for namefunc in ['__setitem__', '__delitem__', '__setattr__', '__delattr__']:
            if hasattr(cls, namefunc) and namefunc not in cls.__dict__ and namefunc not in list_of_non_replaceable_methodes:
                func = getmethod(getattr(cls, namefunc), namefunc)
                setattr(cls, namefunc, func)
        return cls
    if cls is None:
        return wrapper
    return wrapper(cls)

class _FirstContainer:
    def __init__(self, _first_container=None):
        self.container = _first_container.container if isinstance(_first_container, _FirstContainer) else _first_container

@DbClassDecorator
class DbClass:
    _standart_class = object
    _obj_dbattribute = None
    _name_attribute = None
    _first_container = None
    _call_init_when_reconstruct = False
    _methode__new__needs_arguments = False

    def __new__(cls, *args, _use_db=False, _obj_dbattribute=None, _convert_arguments=True, _name_attribute=None, _first_container=None, **kwargs):
        if not _use_db:
            if cls._methode__new__needs_arguments:
                obj = cls._standart_class.__new__(cls._standart_class, *args, **kwargs)
            else:
                obj = cls._standart_class.__new__(cls._standart_class)
            obj.__init__(*args, **kwargs)
            return obj
        if cls._methode__new__needs_arguments:
            return cls._standart_class.__new__(cls, *args, **kwargs)
        return cls._standart_class.__new__(cls)

    def __init__(self, *args, _use_db=False, _obj_dbattribute=None, _convert_arguments=True, _name_attribute=None, _first_container=None, _call_init=True, **kwargs):
        if _obj_dbattribute:
            self.__dict__['_obj_dbattribute'] = _obj_dbattribute
        if _name_attribute:
            self.__dict__['_name_attribute'] = _name_attribute
        if self._first_container is None:
            if _first_container is None:
                self.__dict__['_first_container'] = _FirstContainer(self)
            else:
                if not isinstance(_first_container, _FirstContainer):
                    _first_container = _FirstContainer(_first_container)
                self.__dict__['_first_container'] = _first_container
        if _call_init:
            super().__init__(*args, **kwargs)

    def __reduce_ex__(self, protocol):
        temp = super().__reduce_ex__(protocol)
        if len(temp) >= 3 and temp[2] is not None:
            temp = list(temp)
            temp[2] = {key: convert_atr_value_to_json_value(temp[2][key]) for key in temp[2] if key not in {'_obj_dbattribute', '_name_attribute', '_first_container'}}
            if len(temp[2]) == 0:
                temp[2] = None
            temp = tuple(temp)
        return temp

    def _update_obj(self):
        #print(f'update {self} {self._first_container.container if self._first_container else self._first_container}')
        if self._first_container and self._first_container.container and self._first_container.container._obj_dbattribute:
            self._first_container.container._obj_dbattribute._db_attribute_container_update(self._first_container.container._name_attribute, self._first_container.container)

    def dumps(self, _return_json=True):
        """
        If you create dumps methode for your class, yours methode must return the dict object with keys:
        key 't': type - type of this obj, example: {'t': 'DbList', 'd': [1, 2, 3]} (required key).
        key 'd': data - main data (if you realeseted loads methode, tou can rename this key: use 'd'/'data' and other, it doesn't matter),
        example1 (DbDict): {'t': 'DbDict', 'd': {'0': 1, '1': 2, '2': 3}, 'dk': {'0': 'int', '1': 'int', '2': 'int'}}
        example2 (Develp's Db class): {'t': 'DbUserClass', 'd': {'name': *name*, 'age': *age*, 'books': *jsonDbList*}}
        *and others keys | Develop's keys*
        key 'dk': data key (used DbDict)
        Develop ken create his own keys in dump, and use in load - all dict object dump and load, with json
        required param: _return_json - see documentation
        :param _return_json: if false - return dict, if true - return str: json.dumps(dict)
        """
        data = pickle.dumps(self).decode('latin1')
        if _return_json:
            return json.dumps({'t': self.__class__.__name__, 'd': data}, ensure_ascii=False)
        return {'t': self.__class__.__name__, 'd': data}

    @classmethod
    def loads(cls, tempdata: str | dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        """
        (the use of these parameters (_obj_dbattribute, _name_attribute and _first_container) is not intended - they are used inside the project.)
        If you need to create a "loads" method, please give it the name "_loads".
        For create loads methode you can:
        1) see the _loads methodes of DbList, DbDict, DbDatetime and other... (for example)
        2) It's all :) What do you do? Do you read this? Who are you? How much time do you spend on documentation?
        Did you know that this documentation is already outdated by several versions?
        An anecdote: A programmer once created a function and wrote its documentation.
        After a few versions, the function changed completely, and the documentation became outdated.
        Another programmer read the anecdote and was confused about the documentation, as it was no longer relevant.

        :param tempdata: the dumps obj, example: tempdata = {'t': DbList, 'd': [1, 2, 3]}, or json.loads(tempdata) = {'t': DbList, 'd': [1, 2, 3]}
        :param _obj_dbattribute: link to dbattribute obj
        :param _name_attribute: name this attribute
        :param _first_container: link to 'first container', example: a = [1, [2]] for [2] the 'first container' the [1, [2]]
        :return:
        """
        if isinstance(tempdata, str):
            tempdata = orjson.loads(tempdata)
        if (not isinstance(tempdata, dict)) or 't' not in tempdata:
            raise Exception(
                f"load error: {tempdata} is not dict or don't have the 't' key"
            )
        loadcls = cheaker.db_class_name_to_db_class.get(tempdata['t'], None)
        if loadcls is None:
            raise Exception(
                f"load error: cheaker don't support the {tempdata['t']}, add this class to cheaker"
            )
        if hasattr(loadcls, '_loads'):
            return loadcls._loads(tempdata, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        return cheaker.create_db_class(pickle.loads(tempdata['d'].encode('latin1')), _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

@DbClassDecorator(list_of_methodes_with_converted_arguments=['__iadd__'])
class DbList(DbClass, list):
    _methode__new__needs_arguments = True
    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False)
        list.__init__(self, *args, **kwargs)
        if _convert_arguments:
            self.__convert_arguments__()

    @classmethod
    def __convert_to_db__(cls, obj: list, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        """Converted obj to db object: changed type from list to DbList (you can create yourclass method '__convert_to_db__')"""
        if isinstance(obj, Tlist):
            obj.__class__ = cls
            DbClass.__init__(obj, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
            obj.__convert_arguments__()
            return obj
        return cls(obj, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

    def __convert_from_db__(self):
        """
        Currently, this method is not implemented and is not supported. However, we plan to implement and support it in future updates.
        Converted db object to object: changed type from DbList to list (you can create yourclass method '__convert_from_db__')
        """
        return NotImplemented

    def __convert_arguments__(self):
        """Only DbList uses this method"""
        _first_container = self._first_container
        setitem = list.__setitem__
        for key in range(len(self)):
            setitem(self, key, cheaker.create_db_class(self[key], _first_container=_first_container))

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
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        obj = cls.__new__(cls, _use_db=True)
        if _first_container is None:
            _first_container = _FirstContainer(obj)
        data = [conver_json_value_to_atr_value(value, _first_container=_first_container) for value in tempdata['d']]
        obj.__init__(data, _convert_arguments=False, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        return obj

@DbClassDecorator(list_of_methodes_with_converted_arguments=['__ior__', '__iand__'])
class DbSet(DbClass, set):
    _call_init_when_reconstruct = True
    _methode__new__needs_arguments = True

    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False)
        iterable = set(args[0])
        if _convert_arguments:
            iterable = {cheaker.create_db_class(i, _first_container=self._first_container) for i in iterable}
        set.__init__(self, iterable)

    def __repr__(self):
        return set(self).__repr__()

    @classmethod
    def __convert_to_db__(cls, obj: set, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls(obj, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

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
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        obj = cls.__new__(cls, _use_db=True)
        if _first_container is None:
            _first_container = _FirstContainer(obj)
        data = {conver_json_value_to_atr_value(value, _first_container=_first_container) for value in tempdata['d']}
        obj.__init__(data, _convert_arguments=False, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        return obj

@DbClassDecorator(list_of_methodes_with_converted_arguments=['__ior__'])
class DbDict(DbClass, dict):
    _methode__new__needs_arguments = True
    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False)
        dict.__init__(self, *args, **kwargs)
        if _convert_arguments:
            _first_container = self._first_container
            setitem = dict.__setitem__
            for key in self:
                setitem(self, key, cheaker.create_db_class(self[key], _first_container=_first_container))

    @classmethod
    def __convert_to_db__(cls, obj: dict, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls(obj, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

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
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        obj = cls.__new__(cls, _use_db=True)
        if _first_container is None:
            _first_container = _FirstContainer(obj)
        data = {convert_json_key_to_atr_key(key, tempdata['dk'][key] if key in tempdata['dk'] else None)
                : conver_json_value_to_atr_value(value, _first_container=_first_container)
                for key, value in tempdata['d'].items()}
        obj.__init__(data, _convert_arguments=False, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        return obj

@DbClassDecorator
class DbTuple(DbClass, tuple):
    _methode__new__needs_arguments = True
    _call_init_when_reconstruct = True
    def __new__(cls, *args, _use_db=False, _loads_iterable=False, _obj_dbattribute=None, _convert_arguments=True, _name_attribute=None, _first_container=None, **kwargs):
        if not _use_db:
            return tuple.__new__(DbTuple, *args, **kwargs)

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

    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False)

    def __iadd__(self, other):
        obj = self.__class__(self.__add__(other), _use_db=True, _obj_dbattribute=self._obj_dbattribute, _name_attribute=self._name_attribute, _first_container=self._first_container)
        if self._first_container.container is self:
            obj.__dict__['_first_container'].container = obj
        return obj

    @classmethod
    def __convert_to_db__(cls, obj: tuple, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls(obj, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

    def dumps(self, _return_json=True):
        data = [convert_atr_value_to_json_value(i) for i in self]
        if _return_json:
            return json.dumps({'t': self.__class__.__name__, 'd': data})
        return {'t': self.__class__.__name__, 'd': data}

    @classmethod
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        obj = cls.__new__(cls, tempdata['d'], _use_db=True, _loads_iterable=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        obj.__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        return obj

@DbClassDecorator
class Dbfrozenset(DbClass, frozenset): pass

@DbClassDecorator
class DbDeque(DbClass, collections.deque):
    _methode__new__needs_arguments = True
    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False)

        iterable = args[0]
        if _convert_arguments:
            iterable = [cheaker.create_db_class(i, _first_container=self._first_container) for i in iterable]
        collections.deque.__init__(self, iterable)

    @classmethod
    def __convert_to_db__(cls, obj: collections.deque, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls(obj, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

@DbClassDecorator
class DbDatetime(DbClass, datetime.datetime):
    _methode__new__needs_arguments = True
    def __init__(self, year, month=None, day=None, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False, **kwargs)
    def __iadd__(self, other):
        obj = cheaker.create_db_class(self.__add__(other), _obj_dbattribute=self._obj_dbattribute, _name_attribute=self._name_attribute, _first_container=self._first_container)
        if self._first_container.container is self: obj.__dict__['_first_container'].container = obj
        return obj
    def __isub__(self, other):
        obj = cheaker.create_db_class(self.__sub__(other), _obj_dbattribute=self._obj_dbattribute, _name_attribute=self._name_attribute, _first_container=self._first_container)
        if self._first_container.container is self: obj.__dict__['_first_container'].container = obj
        return obj

    @classmethod
    def __convert_to_db__(cls, obj: datetime.datetime, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls(year=obj.year, month=obj.month, day=obj.day, hour=obj.hour, minute=obj.minute, second=obj.second, microsecond=obj.microsecond, tzinfo=obj.tzinfo, fold=obj.fold, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

    def dumps(self, _return_json=True):
        if _return_json: return json.dumps({'t': self.__class__.__name__, 'd': self.isoformat()})
        return {'t': self.__class__.__name__, 'd': self.isoformat()}

    @classmethod
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls.__convert_to_db__(cls.fromisoformat(tempdata['d']), _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

@DbClassDecorator
class DbDate(DbClass, datetime.date):
    _methode__new__needs_arguments = True
    def __init__(self, year, month=None, day=None, *, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(year=year, month=month, day=day, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False, **kwargs)
    def __iadd__(self, other):
        obj = cheaker.create_db_class(self.__add__(other), _obj_dbattribute=self._obj_dbattribute, _name_attribute=self._name_attribute, _first_container=self._first_container)
        if self._first_container.container is self: obj.__dict__['_first_container'].container = obj
        return obj
    def __isub__(self, other):
        obj = cheaker.create_db_class(self.__sub__(other), _obj_dbattribute=self._obj_dbattribute, _name_attribute=self._name_attribute, _first_container=self._first_container)
        if self._first_container.container is self: obj.__dict__['_first_container'].container = obj
        return obj
    @classmethod
    def __convert_to_db__(cls, obj: datetime.datetime, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls(year=obj.year, month=obj.month, day=obj.day, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
    def dumps(self, _return_json=True):
        if _return_json: return json.dumps({'t': self.__class__.__name__, 'd': self.isoformat()})
        return {'t': self.__class__.__name__, 'd': self.isoformat()}
    @classmethod
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls.__convert_to_db__(cls.fromisoformat(tempdata['d']), _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

@DbClassDecorator
class DbTime(DbClass, datetime.time):
    _methode__new__needs_arguments = True
    def __init__(self, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(_obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False, **kwargs)

    def __iadd__(self, other):
        obj = cheaker.create_db_class(self.__add__(other), _obj_dbattribute=self._obj_dbattribute, _name_attribute=self._name_attribute, _first_container=self._first_container)
        if self._first_container.container is self: obj.__dict__['_first_container'].container = obj
        return obj
    def __isub__(self, other):
        obj = cheaker.create_db_class(self.__sub__(other), _obj_dbattribute=self._obj_dbattribute, _name_attribute=self._name_attribute, _first_container=self._first_container)
        if self._first_container.container is self: obj.__dict__['_first_container'].container = obj
        return obj

    @classmethod
    def __convert_to_db__(cls, obj: datetime.time, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return DbTime(hour=obj.hour, minute=obj.minute, second=obj.second, microsecond=obj.microsecond, tzinfo=obj.tzinfo, fold=obj.fold, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

    def dumps(self, _return_json=True):
        if _return_json: return json.dumps({'t': self.__class__.__name__, 'd': self.isoformat()})
        return {'t': self.__class__.__name__, 'd': self.isoformat()}
    @classmethod
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls.__convert_to_db__(cls.fromisoformat(tempdata['d']), _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

@DbClassDecorator
class DbTimedelta(DbClass, datetime.timedelta):
    _methode__new__needs_arguments = True
    def __init__(self, *args, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
        super().__init__(*args, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False, **kwargs)

    def dumps(self, _return_json=True):
        if _return_json: return json.dumps({'t': self.__class__.__name__, 'd': self.total_seconds()})
        return {'t': self.__class__.__name__, 'd': self.total_seconds()}

    @classmethod
    def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        return cls(seconds=tempdata['d'], _use_db=True, _first_container=_first_container)

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
        self.all_db_classes = set(_db_classes.values())


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
        self.all_db_classes = set(_db_classes.values())

    def add_db_class(self, _db_class: tuple):
        """:param _db_class: example: (datetime.datetime, DbDatetime)"""
        self._db_classes[_db_class[0]] = _db_class[1]
        self.db_class_name_to_db_class[_db_class[1].__name__] = _db_class[1]
        self.class_name_to_db_class[_db_class[0].__name__] = _db_class[1]
        self.db_class_name_to_clasic_class[_db_class[1].__name__] = _db_class[0]
        self.all_db_classes.add(_db_class[1])

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
        self.all_db_classes.discard(db_class)

    def create_any_db_classes(self, *objs, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        """
        Use for create db_class from other classes. example: from list to DbList, but from int to int.
        :param objs: example: [123, '535', {8, 4, 6} #it's set , {1: 2} # it's dict]
        :param _obj_dbattribute:
        :return: example: [123, '535', {8, 4, 6} #it's DbSet , {1: 2} # it's DbDict]
        """
        return [self.create_db_class(objs[i], _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container) for i in range(len(objs))]

    def create_db_class(self, obj, *, attribute_type=None, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        if (attribute_type is None and type(obj) in self._db_classes) or (attribute_type in self._db_classes):
            if attribute_type is None:
                attribute_type = type(obj)
            cls = self._db_classes[attribute_type]
            if hasattr(cls, '__convert_to_db__'):
                return cls.__convert_to_db__(obj, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
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
            rv[1] = (cls,) + rv[1][1:]
            obj = self._reconstruct(*rv,  _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        return obj

    def _reconstruct(self, func, args, state=None, listiter=None, dictiter=None, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
        y = func(*args, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
        if _first_container is None:
            _first_container = _FirstContainer(y)
        if y.__dict__.get('_first_container', None) is None:
            y.__dict__['_first_container'] = _first_container
        if y._call_init_when_reconstruct:
            y.__init__(*args[1:], _obj_dbattribute=None, _name_attribute=None, _first_container=None)
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
        if _obj_dbattribute:
            temp['_obj_dbattribute'] = _obj_dbattribute
        if _name_attribute:
            temp['_name_attribute'] = _name_attribute
        if hasattr(y, '__dict__'):
            y.__dict__.update(temp)
        else:
            for key, value in temp.items():
                setattr(y, key, value)
        return y

    def this_support_class(self, obj, this_is_cls=False):
        return obj in self._db_classes if this_is_cls else type(obj) in self._db_classes

    def this_db_attribute_support_class(self, obj, this_is_cls=False):
        return obj in self.all_db_classes if this_is_cls else type(obj) in self.all_db_classes

class Tlist(list): pass
class Tset(set): pass
class Tdict(dict): pass


def __newobj_ex__(cls, args, kwargs, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
    return cls.__new__(cls, *args, *kwargs, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
def __newobj__(cls, *args, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
    return cls.__new__(cls, *args, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

def convert_atr_value_to_json_value(value):
    return value.dumps(_return_json=False) if cheaker.this_db_attribute_support_class(value) else value

def conver_json_value_to_atr_value(value, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
    if isinstance(value, dict):
        return DbClass.loads(value, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)
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

cheaker = Cheaker({set: DbSet, list: DbList, dict: DbDict, tuple: DbTuple, datetime.datetime: DbDatetime, datetime.timedelta: DbTimedelta, datetime.date: DbDate, datetime.time: DbTime})

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
        print('8.A error:')
        print(A.dumps(), type(A.dumps()))
        print(A, type(A))
        print(a, type(a))
    if B != b:
        print('8.B error:')
        print(B.dumps(), type(B.dumps()))
        print(B, type(B))
        print(b, type(b))
    if C != c:
        print('8.C error:')
        print(C.dumps(), type(C.dumps()))
        print(C, type(C))
        print(c, type(c))
    print(9, 'cheack _first_container')
    temp_func = lambda inp: {id(inp._first_container.container)} | {j for i in inp if hasattr(i, '__iter__') for j in temp_func(i)}
    temp_func_dict = lambda inp: {id(inp._first_container.container)} | {j for key in inp if hasattr(inp[key], '__iter__') for j in temp_func(inp[key])}
    A = DbTuple(([1], 2, 3, datetime.datetime(2024, 10, 4)), _use_db = True)
    A += ((4,),)
    if len(temp_func(A)) > 1:
        print('9.1 error:')
        print(A, type(A), temp_func(A))
        print(id(A), id(A._first_container.container), id(A[0]._first_container.container))
        print(id(A._first_container), id(A[0]._first_container))

    B = DbList([([1], 2, 3, datetime.datetime(2024, 10, 4))], _use_db=True)
    B[0] += ((4,),)
    if len(temp_func(B)) > 1:
        print('9.2 error:')
        print(B, type(B), temp_func(B))
        print(id(B), id(B._first_container.container), id(B[0]._first_container.container), id(B[0][0]._first_container.container))
        print(id(B._first_container), id(B[0]._first_container), id(B[0][0]._first_container))

    B = cheaker.create_db_class([[1, (2,(3,),[4],datetime.datetime(2024, 10, 4)), {5, (6,(7,))}, {(8, 3), 5}], (9,(10,),[11])])
    if B != [[1, (2,(3,),[4],datetime.datetime(2024, 10, 4)), {5, (6,(7,))}, {(8, 3), 5}], (9,(10,),[11])]:
        print('9.3.a error:')
        print(B, type(B))
    B += [(12,)]
    B[0].append(13)
    B[-1] = [1, 2]
    B[0][1] += (4,)
    B[0][2] |= {(3, (1,))}
    B[0][2] -= {(3, (1,))}
    B[0][2] |= {(3, (2,))}
    B[0][2] &= {(3, (2,))}
    if len(temp_func(B)) > 1:
        print('9.3.b error:')
        print(B, type(B), temp_func(B))

    B = cheaker.create_db_class({(1, 2): [3, 4], 5: {6, (7,)}, 8: (9, {10:11})})
    if B != {(1, 2): [3, 4], 5: {6, (7,)}, 8: (9, {10:11})} or type(B) is not DbDict:
        print('9.4.a error:')
        print(B, type(B))
    if len(temp_func_dict(B)) > 1:
        print('9.4.b error:')
        print(B, type(B), temp_func_dict(B))
    B[9] = [(3, 5), {1, 0}, {3: 5}, [2]]
    B |= {8: [1, (5, 8)]}
    B |= {9: [3, 7, (3, 5)]}
    if len(temp_func_dict(B)) > 1:
        print('9.4.c error:')
        print(B, type(B), temp_func_dict(B))


    print(10, 'cheack datetime')
    A = DbDatetime(2024, 11, 4, _use_db=True)
    if A != datetime.datetime(2024, 11, 4) or type(A) is not DbDatetime:
        print('10.1.1 error:')
        print(A, type(A))
    A = cheaker.create_db_class(datetime.datetime(2024, 11, 4))
    if A != datetime.datetime(2024, 11, 4) or type(A) is not DbDatetime:
        print('10.1.2 error:')
        print(A, type(A))
    A = DbClass.loads(A.dumps())
    if A != datetime.datetime(2024, 11, 4) or type(A) is not DbDatetime:
        print('10.1.3 error:')
        print(A, type(A))
    B = DbList([A], _use_db=True)
    B = DbClass.loads(B.dumps())
    if B[0] != datetime.datetime(2024, 11, 4) or type(B[0]) is not DbDatetime:
        print('10.1.4 error:')
        print(A, type(A))
    A = DbTimedelta(microseconds=10, _use_db=True)
    if A != datetime.timedelta(microseconds=10) or type(A) is not DbTimedelta:
        print('10.2.1 error:')
        print(A, type(A))
    A = DbClass.loads(A.dumps())
    if A != datetime.timedelta(microseconds=10) or type(A) is not DbTimedelta:
        print('10.2.2 error:')
        print(A, type(A))
    A = DbTimedelta(seconds=10**6, _use_db=True)
    if A != datetime.timedelta(seconds=10**6) or type(A) is not DbTimedelta:
        print('10.2.3 error:')
        print(A, type(A))
    A = DbClass.loads(A.dumps())
    if A != datetime.timedelta(seconds=10**6) or type(A) is not DbTimedelta:
        print('10.2.4 error:')
        print(A, type(A))
    B = DbDatetime(2024, 11, 4, _use_db=True)
    B -= A
    if B != datetime.datetime(2024, 10, 23, 10, 13, 20) or type(B) is not DbDatetime:
        print('10.3.1 error:')
        print(B, type(B))
    A = DbDate(2024, 11, 10, _use_db=True)
    if A != datetime.date(2024, 11, 10) or type(A) is not DbDate:
        print('10.4.1 error:')
        print(A, type(A))
    A = DbClass.loads(A.dumps())
    if A != datetime.date(2024, 11, 10) or type(A) is not DbDate:
        print('10.4.2 error:')
        print(A, type(A))
    A = DbTime(11, 15, 10, _use_db=True)
    if A != datetime.time(11, 15, 10) or type(A) is not DbTime:
        print('10.5.1 error:')
        print(A, type(A))
    A = DbClass.loads(A.dumps())
    if A != datetime.time(11, 15, 10) or type(A) is not DbTime:
        print('10.5.2 error:')
        print(A, type(A))
    print(11, 'time test')
    def test(cls, args):
        import time
        n = 3*10**4
        print(f'test {cls}')
        start = time.time()
        for i in range(n):
            A = cls(args, _use_db = True)
        end = time.time()
        print(f'create: {n/(end - start)} op/sec {(end-start)} in {n} op')
        start = time.time()
        for i in range(n):
            data = A.dumps()
        end = time.time()
        print(f'dumps: {n/(end - start)} op/sec {(end-start)} in {n} op')
        start = time.time()
        for i in range(n):
            A = cls.loads(data)
        end = time.time()
        print(f'loads: {n/(end - start)} op/sec {(end-start)} in {n} op')
    #test(DbDict, {0: [[1, 2], [3, 4], [5, 6]], 1: {1, ((2,), (3,))}, 2: {1: {2: (3, ), 4: (5,)}, 6: {7: (8,)}}})
    test(DbList, [[[1, 2], [3, 4], [5, 6]], {1, ((2,), (3,))}, {1: {2: (3, ), 4: (5,)}, 6: {7: (8,)}}])


