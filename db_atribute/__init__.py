import dataclasses
from typing import ClassVar
from dataclasses import MISSING

import db_atribute.db_class as db_class
import db_atribute.db_work as db_work
import db_atribute.dbtypes as dbtypes

__all__ = ['dbDecorator', 'db_field', 'DbAtribute', 'db_work', 'db_class', 'connector', 'dbtypes']
__version__ = '1.2'

def dbDecorator(cls=None, /, kw_only=False, _db_Atribute__dbworkobj=None):
    def wrap(cls):
        if (('_db_Atribute__dbworkobj' not in cls.__dict__) or cls._db_Atribute__dbworkobj is None) and _db_Atribute__dbworkobj is None:
            raise Exception('set _db_Atribute__dbworkobj in class (_db_Atribute__dbworkobj: ClassVar[list] = *dbwork obj*) or give dbwork obj to dbDecorator')
        if not _db_Atribute__dbworkobj is None:
            cls._db_Atribute__dbworkobj = _db_Atribute__dbworkobj
        dbworkobj = cls._db_Atribute__dbworkobj

        _Fields = getattr(cls, '__dataclass_fields__')

        if '_db_Atribute__list_db_atributes' not in cls.__dict__:
            cls._db_Atribute__list_db_atributes = set()
        cls._db_Atribute__list_db_atributes = set(cls._db_Atribute__list_db_atributes | {i for i in cls.__annotations__ if isinstance(_Fields[i], dbtypes.DbField)})

        #print(f'{_Fields=}')
        #print(f'{_Fields["_db_Atribute__list_db_atributes"]._field_type == dataclasses._FIELD_CLASSVAR}')

        fields_kw_only_init = [i for i in _Fields if _Fields[i].kw_only and _Fields[i].init]
        fields_kw_only_init_db_atributes = [i for i in _Fields if _Fields[i].kw_only and _Fields[i].init and isinstance(_Fields[i], dbtypes.DbField)]
        fields_not_kw_only_init = [i for i in _Fields if (not _Fields[i].kw_only) and _Fields[i].init]
        fields_not_kw_only_init_db_atributes = [i for i in _Fields if isinstance(_Fields[i], dbtypes.DbField) and (not _Fields[i].kw_only) and _Fields[i].init]
        #init_db_atributes = [i for i in _Fields if isinstance(_Fields[i], DbField) and _Fields[i].init]

        set_db_atributes = set(cls._db_Atribute__list_db_atributes)
        set_fields_kw_only_init_db_atributes = set(fields_kw_only_init_db_atributes)
        set_fields_not_kw_only_init_db_atributes = set(fields_not_kw_only_init_db_atributes)


        db_sorted_atrs = fields_not_kw_only_init.copy()#list(cls.__annotations__)
        if 'id' not in db_sorted_atrs:
            db_sorted_atrs = ['id'] + db_sorted_atrs

        """        print(f'{fields_kw_only_init=}')
        print(f'{fields_kw_only_init_db_atributes=}')
        print(f'{fields_not_kw_only_init=}')
        print(f'{fields_not_kw_only_init_db_atributes=}')
        print(f'{set_db_atributes=}')"""

        dict_db_sorted_atrs = {db_sorted_atrs[i]: i for i in range(len(db_sorted_atrs)) if db_sorted_atrs[i] in set_db_atributes}

        #print(f'{dict_db_sorted_atrs=}')

        def new_init(self, *args, _without_init=False, **kwargs):
            ID = -1
            if 'id' in kwargs:
                ID = kwargs['id']
            elif args:
                ID = args[0]
            if _without_init:
                object.__setattr__(self, 'id', ID)
                object.__setattr__(self, '_db_Atribute__dump_mode', True)
                return
            db_args_not_set = set_fields_not_kw_only_init_db_atributes.copy() - set(kwargs)

            temp_data = set()
            for i in db_args_not_set:
                if i in dict_db_sorted_atrs and dict_db_sorted_atrs[i] < len(args):
                    temp_data.add(i)
            db_args_not_set -= temp_data

            #temp_data = set()
            #for i in db_args_not_set:
            #    if (table_name := db_work.get_table_name(cls.__name__, i)) not in dbworkobj.active_tables or (not dbworkobj.get_values_by_id(table_name, ID)['data']):
            #        temp_data.add(i)
            #db_args_not_set -= temp_data

            kwargs |= {i: dbtypes.NotSet for i in db_args_not_set}
            kwargs |= {i: dbtypes.NotSet for i in set_fields_kw_only_init_db_atributes - set(kwargs)}
            self._db_Atribute__dump_mode = True
            return cls.__old_init__(self, *args, **kwargs)
        cls.__old_init__ = cls.__init__
        cls.__init__ = new_init
        return cls
    if cls is None:
        return wrap
    return wrap(cls)

def db_field(*, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None, kw_only=MISSING):
    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')
    return dbtypes.DbField(default, default_factory, init, repr, hash, compare, metadata, kw_only)

@dataclasses.dataclass
class DbAtribute:
    id: int
    _db_Atribute__dump_mode: bool = dataclasses.field(default=True, repr=False, init=False)
    _db_Atribute__list_db_atributes: ClassVar[list] = []
    _db_Atribute__dbworkobj: ClassVar[db_work.Db_work] = None

    def __setattr__(self, key, value):
        object.__getattribute__(self, '_db_atribute_set_attr')(key, value)

    def __getattribute__(self, item):
        return object.__getattribute__(self, '_db_atribute_get_attr')(item)

    @classmethod
    def _db_atribute_get_default_value(cls, fieldname):
        Field = getattr(cls, '__dataclass_fields__').get(fieldname, dbtypes.NotSet)
        if Field is dbtypes.NotSet or (Field.default is MISSING and Field.default_factory is MISSING): return dbtypes.NotSet
        if Field.default is not MISSING: return Field.default
        return Field.default_factory()

    def _db_atribute_set_attr(self, key, value):
        if value is dbtypes.NotSet:
            return
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        if (key not in cls.__dict__['_db_Atribute__list_db_atributes']) or ('_db_Atribute__dump_mode' not in self_dict) or (not self_dict['_db_Atribute__dump_mode']):
            return object.__setattr__(self, key, value)
        self._db_atribute_dump_attr_to_db(key, value)

    def _db_atribute_dump_attr_to_db(self, key, value, cheak_exists_value=True):
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        obj = db_class.cheaker.create_db_class(value, _obj_dbatribute=self)
        if db_work.get_table_name(cls.__name__, key) not in cls._db_Atribute__dbworkobj.active_tables:
            cls._db_Atribute__dbworkobj.create_atribute_table(class_name=cls.__name__, atribute_name=key, atribute_type=type(obj))
            cheak_exists_value = False
        cls._db_Atribute__dbworkobj.add_atribute_value(class_name=cls.__name__, atribute_name=key, ID=self_dict['id'], data=obj, _cls_dbatribute=cls, cheak_exists_value=cheak_exists_value)

    def _db_atribute_get_attr(self, key):
        cls = object.__getattribute__(self, '__class__')
        if (key not in cls.__dict__['_db_Atribute__list_db_atributes']) or ('_db_Atribute__dump_mode' not in (self_dict := object.__getattribute__(self, '__dict__'))) or (not self_dict['_db_Atribute__dump_mode']):
            return object.__getattribute__(self, key)
        temp_data = cls._db_Atribute__dbworkobj.get_atribute_value(class_name=cls.__name__, atribute_name=key, ID=self_dict['id'], _obj_dbatribute=self)
        if temp_data['status_code'] == 304:
            value = cls._db_atribute_get_default_value(key)
            object.__getattribute__(self, '_db_atribute_dump_attr_to_db')(key, value, cheak_exists_value=False)
            return value
        if temp_data['status_code'] != 200:
            return None
        return temp_data['data']

    def _db_atribute_container_update(self, key, data=None):
        """
        call this functions, when any container atribute is updated, to update this atribute in db
        :param key: name atribute container which update
        :type key: str
        :param data: the atribute (DbDict, DbSet and others containers)
        """
        self_dict = object.__getattribute__(self, '__dict__')
        if ('_db_Atribute__dump_mode' not in self_dict) or (not self_dict['_db_Atribute__dump_mode']):
            return
        cls = object.__getattribute__(self, '__class__')
        cls._db_Atribute__dbworkobj.add_atribute_value(class_name=cls.__name__, atribute_name=key, ID=self_dict['id'], data=data)

    @classmethod
    def _db_atribute_found_ids_by_atribute(cls, atribute_name:str, atribute_value):
        tempdata = cls._db_Atribute__dbworkobj.found_ids_by_value(class_name=cls.__name__, atribute_name=atribute_name, data=atribute_value, _cls_dbatribute=cls)
        if tempdata['status_code'] != 200:
            return []
        return tempdata['data']

    def db_atribute_dump(self):
        """
        use it func, if you need dump the data to db, with undump_mode (_db_Atribute__dump_mode = False)
        you don't can use this funnction, if it dump_mode (_db_Atribute__dump_mode = True)
        """
        self_dict = object.__getattribute__(self, '__dict__')
        if ('_db_Atribute__dump_mode' not in self_dict) or self_dict['_db_Atribute__dump_mode']: return
        for db_atr in object.__getattribute__(self, '__class__').__dict__['_db_Atribute__list_db_atributes']:
            self._db_atribute_dump_attr_to_db(db_atr, self_dict[db_atr])

    def db_atribute_dump_attr(self, name_db_attribute):
        """
        this self.db_atribute_dump, but for one attribute
        """
        self_dict = object.__getattribute__(self, '__dict__')
        if ('_db_Atribute__dump_mode' not in self_dict) or self_dict['_db_Atribute__dump_mode']: return
        self._db_atribute_dump_attr_to_db(name_db_attribute, self_dict[name_db_attribute])

    def db_atribute_set_undump_mode(self):
        """
        dump_mode: atributes don't save in self.__dict__, all changes automatic dump in db.
        undump_mode: all atributes save in self.__dict__, and won't dump in db until self.db_atribute_set_dump_mode is called.
        function set undump_mode (dump_mode = False)
        """
        self_dict = object.__getattribute__(self, '__dict__')
        if ('_db_Atribute__dump_mode' in self_dict) and (not self_dict['_db_Atribute__dump_mode']): return
        for db_atr in object.__getattribute__(self, '__class__').__dict__['_db_Atribute__list_db_atributes']:
            self_dict[db_atr] = self._db_atribute_get_attr(db_atr)
        self_dict['_db_Atribute__dump_mode'] = False

    def db_atribute_set_dump_mode(self):
        """
        dump_mode: atributes don't save in self.__dict__, all changes automatic dump in db.
        undump_mode: all atributes save in self.__dict__, and won't dump in db until self.db_atribute_set_dump_mode is called.
        function set dump_mode (dump_mode = True) and call self.db_atribute_dump() for dump all atributes
        """
        self_dict = object.__getattribute__(self, '__dict__')
        if ('_db_Atribute__dump_mode' not in self_dict) or self_dict['_db_Atribute__dump_mode']: return
        self.db_atribute_dump()
        self_dict['_db_Atribute__dump_mode'] = True
        for db_atr in object.__getattribute__(self, '__class__').__dict__['_db_Atribute__list_db_atributes']:
            del self_dict[db_atr]

    @classmethod
    def db_atribute_found_ids(cls, **kwargs):
        """
        found ids objs with this values of atributes, ex:
        objs: User(id=1, name='Bob', age=3), User(id=2, name='Bob', age=2), User(id=3, name='Anna', age=2)
        User.db_atribute_found_ids_by_atributes(name='Bob') -> {1, 2}
        User.db_atribute_found_ids_by_atributes(age=2) -> {2, 3}
        User.db_atribute_found_ids_by_atributes(name='Bob', age=2) -> {2}
        :param kwargs: names and values of atributes (see doc.)
        :return: set of ids
        """
        if not kwargs: return []
        res = set(cls._db_atribute_found_ids_by_atribute(atribute_name=(temp:=next(iter(kwargs))), atribute_value=kwargs[temp]))
        for key in kwargs:
            res &= set(cls._db_atribute_found_ids_by_atribute(atribute_name=key, atribute_value=kwargs[key]))
        return res
