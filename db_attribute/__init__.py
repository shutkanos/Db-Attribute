import dataclasses
from typing import ClassVar
from dataclasses import MISSING

import db_attribute.db_class as db_class
import db_attribute.db_work as db_work
import db_attribute.db_types as db_types

__all__ = ['dbDecorator', 'db_field', 'DbAttribute', 'db_work', 'db_class', 'connector', 'db_types']
__version__ = '1.2'

def dbDecorator(cls=None, /, _db_attribute__dbworkobj=None):
    def wrap(cls):
        if (('_db_attribute__dbworkobj' not in cls.__dict__) or cls._db_attribute__dbworkobj is None) and _db_attribute__dbworkobj is None:
            raise Exception('set _db_attribute__dbworkobj in class (_db_attribute__dbworkobj: ClassVar[list] = *dbwork obj*) or give dbwork obj to dbDecorator')

        db_types.dict_classes.add(cls)

        if not _db_attribute__dbworkobj is None:
            cls._db_attribute__dbworkobj = _db_attribute__dbworkobj

        _Fields = getattr(cls, '__dataclass_fields__')

        if '_db_attribute__list_db_attributes' not in cls.__dict__:
            cls._db_attribute__list_db_attributes = set()
        cls._db_attribute__list_db_attributes = set(cls._db_attribute__list_db_attributes | {i for i in cls.__annotations__ if isinstance(_Fields[i], db_types.DbField)})

        fields_kw_only_init_db_attributes = [i for i in _Fields if _Fields[i].kw_only and _Fields[i].init and isinstance(_Fields[i], db_types.DbField)]
        fields_not_kw_only_init = [i for i in _Fields if (not _Fields[i].kw_only) and _Fields[i].init]
        fields_not_kw_only_init_db_attributes = [i for i in _Fields if isinstance(_Fields[i], db_types.DbField) and (not _Fields[i].kw_only) and _Fields[i].init]

        set_db_attributes = set(cls._db_attribute__list_db_attributes)
        set_fields_kw_only_init_db_attributes = set(fields_kw_only_init_db_attributes)
        set_fields_not_kw_only_init_db_attributes = set(fields_not_kw_only_init_db_attributes)

        db_sorted_atrs = fields_not_kw_only_init.copy()
        if 'id' not in db_sorted_atrs:
            db_sorted_atrs = ['id'] + db_sorted_atrs

        dict_db_sorted_atrs = {db_sorted_atrs[i]: i for i in range(len(db_sorted_atrs)) if db_sorted_atrs[i] in set_db_attributes}

        def new_init(self, *args, _without_init=False, **kwargs):
            if 'id' in kwargs:
                ID = kwargs['id']
            elif args:
                ID = args[0]
            else:
                IDs = cls.db_attribute_found_ids(**kwargs)
                if not IDs:
                    raise Exception(f'no object with these attributes was found {kwargs}')
                if len(IDs) > 1:
                    raise Exception(f'more than one object with these attributes was found {kwargs}')
                object.__setattr__(self, 'id', next(iter(IDs)))
                return
            if _without_init:
                object.__setattr__(self, 'id', ID)
                return
            db_args_not_set = set_fields_not_kw_only_init_db_attributes.copy() - set(kwargs)

            temp_data = set()
            for i in db_args_not_set:
                if i in dict_db_sorted_atrs and dict_db_sorted_atrs[i] < len(args):
                    temp_data.add(i)
            db_args_not_set -= temp_data

            kwargs |= {i: db_types.NotSet for i in db_args_not_set}
            kwargs |= {i: db_types.NotSet for i in set_fields_kw_only_init_db_attributes - set(kwargs)}
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
    return db_types.DbField(default, default_factory, init, repr, hash, compare, metadata, kw_only)

@dataclasses.dataclass
class DbAttribute:
    id: int
    _db_attribute__list_db_attributes: ClassVar[list] = []
    _db_attribute__dbworkobj: ClassVar[db_work.Db_work] = None

    def __setattr__(self, key, value):
        object.__getattribute__(self, '_db_attribute_set_attr')(key, value)

    def __getattribute__(self, item):
        return object.__getattribute__(self, '_db_attribute_get_attr')(item)

    @classmethod
    def _db_attribute_get_default_value(cls, fieldname):
        Field = getattr(cls, '__dataclass_fields__').get(fieldname, db_types.NotSet)
        if Field is db_types.NotSet or (Field.default is MISSING and Field.default_factory is MISSING): return db_types.NotSet
        if Field.default is not MISSING: return Field.default
        return Field.default_factory()

    def _db_attribute_set_attr(self, key, value):
        if value is db_types.NotSet:
            return
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        if (key in self_dict) or (key not in cls.__dict__['_db_attribute__list_db_attributes']):
            return object.__setattr__(self, key, value)
        self._db_attribute_dump_attr_to_db(key, value)

    def _db_attribute_dump_attr_to_db(self, key, value, cheak_exists_value=True, update_value=False):
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        attribute_type = cls.__annotations__[key]
        obj = db_class.cheaker.create_db_class(value, attribute_type=attribute_type, _obj_dbattribute=self)
        if db_work.get_table_name(cls.__name__, key) not in cls._db_attribute__dbworkobj.active_tables:
            cls._db_attribute__dbworkobj.create_attribute_table(class_name=cls.__name__, attribute_name=key, attribute_type=attribute_type)
            cheak_exists_value = False
        cls._db_attribute__dbworkobj.add_attribute_value(class_name=cls.__name__, attribute_name=key, ID=self_dict['id'], data=obj, attribute_type=attribute_type, cheak_exists_value=cheak_exists_value, update_value=update_value)

    def _db_attribute_get_attr(self, key):
        cls = object.__getattribute__(self, '__class__')
        self_dict = object.__getattribute__(self, '__dict__')
        if (key in self_dict) or (key not in cls.__dict__['_db_attribute__list_db_attributes']):
            return object.__getattribute__(self, key)
        temp_data = object.__getattribute__(cls, '_db_attribute__dbworkobj').get_attribute_value(class_name=cls.__name__, attribute_name=key, ID=self_dict['id'], _obj_dbattribute=self)
        if temp_data['status_code'] == 302:
            object.__getattribute__(cls, '_db_attribute__dbworkobj').create_attribute_table(class_name=cls.__name__, attribute_name=key, _cls_dbattribute=cls)
            temp_data['status_code'] = 304
        if temp_data['status_code'] == 304:
            value = cls._db_attribute_get_default_value(key)
            self._db_attribute_set_attr(key, value)
            #object.__getattribute__(self, '_db_attribute_dump_attr_to_db')(key, value, cheak_exists_value=False)
            return value
        if temp_data['status_code'] != 200:
            return None
        return temp_data['data']

    def _db_attribute_container_update(self, key, data=None):
        """
        call this functions, when any container attribute is updated, to update this attribute in db
        :param key: name attribute container which update
        :type key: str
        :param data: the attribute (DbDict, DbSet and others containers)
        """
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        if (key in self_dict) or (key not in cls.__dict__['_db_attribute__list_db_attributes']):
            return
        cls._db_attribute__dbworkobj.add_attribute_value(class_name=cls.__name__, attribute_name=key, ID=self_dict['id'], data=data, _cls_dbattribute=cls, cheak_exists_value=False, update_value=True)

    @classmethod
    def _db_attribute_found_ids_by_attribute(cls, attribute_name:str, attribute_value):
        tempdata = cls._db_attribute__dbworkobj.found_ids_by_value(class_name=cls.__name__, attribute_name=attribute_name, data=attribute_value, _cls_dbattribute=cls)
        if tempdata['status_code'] != 200:
            return []
        return tempdata['data']

    def db_attribute_dump(self):
        """
        use it func, if you need dump the data to db, with manual_dump_mode
        """
        self_dict = object.__getattribute__(self, '__dict__')
        for db_atr in object.__getattribute__(self, '_db_attribute__list_db_attributes') & set(self_dict):
            self._db_attribute_dump_attr_to_db(db_atr, self_dict[db_atr])

    def db_attribute_dump_attr(self, name_db_attribute):
        """
        this self.db_attribute_dump, but for one attribute
        """
        self_dict = object.__getattribute__(self, '__dict__')
        if name_db_attribute in self_dict and name_db_attribute in object.__getattribute__(self, '_db_attribute__list_db_attributes'):
            self._db_attribute_dump_attr_to_db(name_db_attribute, self_dict[name_db_attribute])

    def db_attribute_set_manual_dump_mode(self, atributes:set[str]=None):
        """
        auto_dump_mode: attributes don't save in self.__dict__, all changes automatic dump in db.
        manual_dump_mode: all attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_auto_dump_mode is called.
        function set undump_mode (dump_mode = False)
        :param atributes: which atributes save in __dict__, ex: atributes={'name', 'age'}
        """
        all_attributes = object.__getattribute__(self, '__class__').__dict__['_db_attribute__list_db_attributes']
        if atributes is None:
            atributes = all_attributes
        self_dict = object.__getattribute__(self, '__dict__')
        get_attr = object.__getattribute__(self, '_db_attribute_get_attr')
        for db_atr in (all_attributes if all_attributes is atributes else all_attributes & atributes):
            self_dict[db_atr] = get_attr(db_atr)

    def db_attribute_set_auto_dump_mode(self):
        """
        auto_dump_mode: attributes don't save in self.__dict__, all changes automatic dump in db.
        manual_dump_mode: all attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_auto_dump_mode is called.
        function set auto_dump_mode and call self.db_attribute_dump() for dump attributes
        """
        self.db_attribute_dump()
        self_dict = object.__getattribute__(self, '__dict__')
        for db_atr in object.__getattribute__(self, '_db_attribute__list_db_attributes') & set(self_dict):
            del self_dict[db_atr]

    @classmethod
    def db_attribute_found_ids(cls, **kwargs):
        """
        found ids objs with this values of attributes, ex:
        objs: User(id=1, name='Bob', age=3), User(id=2, name='Bob', age=2), User(id=3, name='Anna', age=2)
        User.db_attribute_found_ids_by_attributes(name='Bob') -> {1, 2}
        User.db_attribute_found_ids_by_attributes(age=2) -> {2, 3}
        User.db_attribute_found_ids_by_attributes(name='Bob', age=2) -> {2}
        :param kwargs: names and values of attributes (see doc.)
        :return: set of ids
        """
        if not kwargs: return []
        res = set(cls._db_attribute_found_ids_by_attribute(attribute_name=(temp:=next(iter(kwargs))), attribute_value=kwargs[temp]))
        for key in kwargs:
            res &= set(cls._db_attribute_found_ids_by_attribute(attribute_name=key, attribute_value=kwargs[key]))
        return res
