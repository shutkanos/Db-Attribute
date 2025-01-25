import dataclasses
from typing import ClassVar
from dataclasses import MISSING

import db_attribute.db_class as db_class
import db_attribute.db_work as db_work
import db_attribute.db_types as db_types
import db_attribute.connector as connector
import db_attribute.discriptor as discriptor

__all__ = ['dbDecorator', 'db_field', 'DbAttribute', 'db_work', 'db_class', 'connector', 'db_types']
__version__ = '1.3.1'

def dbDecorator(cls=None, /, dbworkobj=None):
    def wrap(cls):
        if dbworkobj is None:
            raise Exception('set _db_attribute__dbworkobj in class (_db_attribute__dbworkobj: ClassVar[list] = *dbwork obj*) or give dbwork obj to dbDecorator')

        db_types.dict_classes.add(cls)

        cls._db_attribute__dbworkobj = dbworkobj

        _Fields = getattr(cls, '__dataclass_fields__')

        for attr_name in _Fields:
            if isinstance(_Fields[attr_name], db_types.DbField):
                setattr(cls, attr_name, discriptor.DbAttributeDiscriptor(cls, attr_name))

        for i in cls.__mro__:
            if hasattr(i, '__annotations__'):
                cls.__annotations__.update(i.__annotations__)

        #if '_db_attribute__list_db_attributes' not in cls.__dict__:
        #    cls._db_attribute__list_db_attributes = set()
        cls._db_attribute__list_db_attributes = set(_Fields) - {'id'}

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
            if not (kwargs or args):
                raise Exception('need args or kwargs for create obj')
            if 'id' in kwargs:
                ID = kwargs['id']
            elif args and isinstance(args[0], int):
                ID = args[0]
            else:
                IDs = cls.found(**kwargs) if kwargs else args[0]
                for i in args:
                    IDs &= i
                if not IDs:
                    raise Exception('no object with these attributes was found')
                if len(IDs) > 1:
                    raise Exception('more than one object with these attributes was found')
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

    def _db_attribute_container_update(self, key, data=None):
        """
        call this functions, when any container attribute is updated, to update this attribute in db
        :param key: name attribute container which update
        :type key: str
        :param data: the attribute (DbDict, DbSet and others containers)
        """
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        if ('_'+key in self_dict) or (key not in cls.__dict__['_db_attribute__list_db_attributes']):
            return
        cls.__dict__[key].container_update(self, data)

    @classmethod
    def _db_attribute_found_ids_by_attribute(cls, attribute_name:str, attribute_value):
        tempdata = cls._db_attribute__dbworkobj.found_ids_by_value(class_name=cls.__name__, attribute_name=attribute_name, data=attribute_value, _cls_dbattribute=cls)
        if tempdata['status_code'] != 200:
            return set()
        return tempdata['data']

    def dump(self, attributes:set[str]=None):
        """
        use it func, if you need dump the data to db, with manual_dump_mode
        """
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        all_attributes = object.__getattribute__(self, '_db_attribute__list_db_attributes')
        for db_attr in all_attributes if attributes is None else all_attributes & attributes:
            if '_'+db_attr in self_dict:
                cls.__dict__[db_attr].dump_attr(self)

    def set_manual_dump_mode(self, attributes:set[str]=None):
        """
        auto_dump_mode: attributes don't save in self.__dict__, all changes automatic dump in db.
        manual_dump_mode: all attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_auto_dump_mode is called.
        function set undump_mode (dump_mode = False)
        :param attributes: for which attributes will set the mode, ex: atributes={'name', 'age'}
        """
        all_attributes = object.__getattribute__(self, '_db_attribute__list_db_attributes')
        self_dict = object.__getattribute__(self, '__dict__')
        for db_attr in (all_attributes if attributes is None else all_attributes & attributes):
            self_dict['_'+db_attr] = getattr(self, db_attr)

    def set_auto_dump_mode(self, attributes:set[str]=None):
        """
        auto_dump_mode: attributes don't save in self.__dict__, all changes automatic dump in db.
        manual_dump_mode: all attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_auto_dump_mode is called.
        function set auto_dump_mode and call self.db_attribute_dump() for dump attributes
        :param attributes: for which attributes will set the mode, ex: atributes={'name', 'age'}
        """
        self.dump(attributes=attributes)
        self_dict = object.__getattribute__(self, '__dict__')
        all_attributes = object.__getattribute__(self, '_db_attribute__list_db_attributes')
        for db_attr in all_attributes if attributes is None else all_attributes & attributes:
            if '_'+db_attr in self_dict:
                del self_dict['_'+db_attr]

    def delete(self, attributes:set[str]=None):
        """
        Delete this id from db
        :param attributes: attributes to be deleted
        :return:
        """
        all_attributes = object.__getattribute__(self, '_db_attribute__list_db_attributes')
        for db_attr in all_attributes if attributes is None else all_attributes & attributes:
            delattr(self, db_attr)

    @classmethod
    def delete_objs(cls, IDs: set[int] | int, attributes:set[str]=None):
        all_attributes = object.__getattribute__(cls, '_db_attribute__list_db_attributes')
        attributes = all_attributes if attributes is None else attributes & all_attributes
        IDs = {IDs} if isinstance(IDs, int) else IDs
        dbworkobj = cls._db_attribute__dbworkobj
        clsname = cls.__name__
        for ID in IDs:
            for db_attr in attributes:
                dbworkobj.del_attribute_value(class_name=clsname, attribute_name=db_attr, ID=ID)

    @classmethod
    def found(cls, **kwargs):
        """
        this function not used, use 'cls.attr == value'
        found ids objs with this values of attributes, ex:
        objs: User(id=1, name='Bob', age=3), User(id=2, name='Bob', age=2), User(id=3, name='Anna', age=2)
        User.db_attribute_found_ids_by_attributes(name='Bob') -> {1, 2}
        User.db_attribute_found_ids_by_attributes(age=2) -> {2, 3}
        User.db_attribute_found_ids_by_attributes(name='Bob', age=2) -> {2}
        :param kwargs: names and values of attributes (see doc.)
        :return: set of ids
        """
        if not kwargs: return set()
        res = cls._db_attribute_found_ids_by_attribute(attribute_name=(temp:=next(iter(kwargs))), attribute_value=kwargs[temp])
        for key in kwargs:
            res &= cls._db_attribute_found_ids_by_attribute(attribute_name=key, attribute_value=kwargs[key])
        return res


