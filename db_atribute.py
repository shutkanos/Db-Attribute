import dataclasses
from typing import ClassVar
from dataclasses import MISSING

import db_class
import db_work
from db_work import db_work_obg as dwo

def dbDecorator(cls=None, /, kw_only=False):
    def wrap(cls):
        if '_db_Atribute__list_db_atributes' not in cls.__dict__:
            cls._db_Atribute__list_db_atributes = [i for i in cls.__annotations__ if isinstance(cls.__dataclass_fields__[i], DbField)]

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
                if (table_name:=db_work.get_table_name(cls.__name__, i)) not in dwo.active_tables or (not dwo.get_values_by_id(table_name, ID)['data']):
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

dataclasses.field

def db_field(*, default=MISSING, default_factory=MISSING, init=True, repr=True, hash=None, compare=True, metadata=None, kw_only=MISSING):
    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')
    return DbField(default, default_factory, init, repr, hash, compare, metadata, kw_only)

class NotSet:
    pass

class DbField(dataclasses.Field):
    pass


@dataclasses.dataclass
class Db_Atribute:
    id: int
    _db_Atribute__list_db_atributes: ClassVar[list] = []

    def __setattr__(self, key, value):
        object.__getattribute__(self, '_db_atribute_set_attr')(key, value)

    def __getattribute__(self, item):
        return object.__getattribute__(self, '_db_atribute_get_attr')(item)

    def _db_atribute_set_attr(self, key, value):
        if value is NotSet:
            return
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        if key in cls.__dict__['_db_Atribute__list_db_atributes']:
            obj = db_class.cheaker.create_one_db_class(value, _obj_dbatribute=self)
            cls_name = cls.__name__
            if db_work.get_table_name(cls_name, key) not in dwo.active_tables:
                dwo.create_atribute_table(class_name=cls_name, atribute_name=key, atribute_type=type(obj))
            dwo.add_atribute_value(class_name=cls_name, atribute_name=key, ID=self_dict['id'], data=obj)
        else:
            object.__setattr__(self, key, value)

    def _db_atribute_get_attr(self, key):
        if key[0] == '_' or '_db_Atribute__list_db_atributes' not in (cls_dict := object.__getattribute__(self, '__class__').__dict__) or key not in cls_dict['_db_Atribute__list_db_atributes']:
            return object.__getattribute__(self, key)

        temp_data = dwo.get_atribute_value(class_name=self.__class__.__name__, atribute_name=key, ID=object.__getattribute__(self, 'id'))
        if temp_data['status_code'] != 200:
            return None
        #print(f'_db_atribute_get_attr {key} {temp_data["data"]}')
        return temp_data['data']

    def _db_atribute_container_update(self, key):
        """
        call this functions, when any container atribute is updated, to update this atribute in db
        :param key: atribute container which update
        :type key: str
        :return: None
        """
        pass

#a = Db_Atribute(id=10)

#print(a)