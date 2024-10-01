import dataclasses
from typing import ClassVar
from dataclasses import MISSING

import db_atribute.db_class as db_class
import db_atribute.db_work as db_work

__all__ = ['dbDecorator', 'db_field', 'DbAtribute']

def dbDecorator(cls=None, /, kw_only=False, _db_Atribute__dbworkobj=None):
    def wrap(cls):
        if (('_db_Atribute__dbworkobj' not in cls.__dict__) or cls._db_Atribute__dbworkobj is None) and _db_Atribute__dbworkobj is None:
            raise Exception('set _db_Atribute__dbworkobj in class (_db_Atribute__dbworkobj: ClassVar[list] = *dbwork obj*) or give dbwork obj to dbDecorator')
        if not _db_Atribute__dbworkobj is None:
            cls._db_Atribute__dbworkobj = _db_Atribute__dbworkobj
        dbworkobj = cls._db_Atribute__dbworkobj
        if '_db_Atribute__list_db_atributes' not in cls.__dict__:
            cls._db_Atribute__list_db_atributes = []
        cls._db_Atribute__list_db_atributes = list(set(cls._db_Atribute__list_db_atributes + [i for i in cls.__annotations__ if isinstance(cls.__dataclass_fields__[i], DbField)]))

        set_db_atributes = set(cls._db_Atribute__list_db_atributes)
        if not kw_only:
            db_sorted_atrs = list(cls.__annotations__)
            if 'id' not in db_sorted_atrs:
                db_sorted_atrs = ['id'] + db_sorted_atrs
            dict_db_sorted_atrs = {db_sorted_atrs[i]: i for i in range(len(db_sorted_atrs)) if db_sorted_atrs[i] in set_db_atributes}

        def new_init(self, *args, **kwargs):
            db_args_not_set = set_db_atributes.copy() - set(kwargs)
            if not kw_only:
                temp_data = set()
                for i in db_args_not_set:
                    if i in dict_db_sorted_atrs and dict_db_sorted_atrs[i] < len(args):
                        temp_data.add(i)
                db_args_not_set -= temp_data
            ID = -1
            if 'id' in kwargs:
                ID = kwargs['id']
            elif len(args):
                ID = args[0]
            temp_data = set()
            for i in db_args_not_set:
                if (table_name:= db_work.get_table_name(cls.__name__, i)) not in dbworkobj.active_tables or (not dbworkobj.get_values_by_id(table_name, ID)['data']):
                    temp_data.add(i)
            db_args_not_set -= temp_data
            kwargs |= {i: NotSet for i in db_args_not_set}
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
    return DbField(default, default_factory, init, repr, hash, compare, metadata, kw_only)

class NotSet:
    pass

class DbField(dataclasses.Field):
    pass


@dataclasses.dataclass
class DbAtribute:
    id: int
    _db_Atribute__dump_mode: bool = True
    _db_Atribute__list_db_atributes: ClassVar[list] = []
    _db_Atribute__dbworkobj: ClassVar[db_work.Db_work] = None

    def __setattr__(self, key, value):
        object.__getattribute__(self, '_db_atribute_set_attr')(key, value)

    def __getattribute__(self, item):
        return object.__getattribute__(self, '_db_atribute_get_attr')(item)

    def _db_atribute_set_attr(self, key, value):
        if value is NotSet:
            return
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        if (key not in cls.__dict__['_db_Atribute__list_db_atributes']) or ('_db_Atribute__dump_mode' not in self_dict) or (not self_dict['_db_Atribute__dump_mode']):
            return object.__setattr__(self, key, value)
        self._db_atribute_dump_attr_to_db(key, value)

    def _db_atribute_dump_attr_to_db(self, key, value):
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        obj = db_class.cheaker.create_one_db_class(value, _obj_dbatribute=self)
        if db_work.get_table_name(cls.__name__, key) not in cls._db_Atribute__dbworkobj.active_tables:
            cls._db_Atribute__dbworkobj.create_atribute_table(class_name=cls.__name__, atribute_name=key, atribute_type=type(obj))
        cls._db_Atribute__dbworkobj.add_atribute_value(class_name=cls.__name__, atribute_name=key, ID=self_dict['id'], data=obj)

    def _db_atribute_get_attr(self, key):
        cls = object.__getattribute__(self, '__class__')
        if (key not in cls.__dict__['_db_Atribute__list_db_atributes']) or ('_db_Atribute__dump_mode' not in (self_dict := object.__getattribute__(self, '__dict__'))) or (not self_dict['_db_Atribute__dump_mode']):
            return object.__getattribute__(self, key)
        temp_data = cls._db_Atribute__dbworkobj.get_atribute_value(class_name=cls.__name__, atribute_name=key, ID=self_dict['id'], _obj_dbatribute=self)
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
        cls = object.__getattribute__(self, '__class__')
        self_dict = object.__getattribute__(self, '__dict__')
        if ('_db_Atribute__dump_mode' not in self_dict) or (not self_dict['_db_Atribute__dump_mode']):
            return
        cls._db_Atribute__dbworkobj.add_atribute_value(class_name=cls.__name__, atribute_name=key, ID=self_dict['id'], data=data)

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



