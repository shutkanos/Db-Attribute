from typing import ClassVar, get_origin

import db_attribute.db_class as db_class
import db_attribute.db_work as db_work
import db_attribute.db_types as db_types
import db_attribute.connector as connector
import db_attribute.discriptor as discriptor

__all__ = ['DbAttribute', 'DbAttributeMetaclass', 'db_work', 'db_class', 'discriptor', 'connector', 'db_types']
__version__ = '2.1'

class DbAttributeMetaclass(type):
    dict_classes = db_types.DictClasses()
    def __new__(cls, name, bases, namespace, **kwargs):
        def cheak_class_in_bases(bases, Class):
            for i in bases:
                if Class in i.__mro__:
                    return True
            return False

        if not cheak_class_in_bases(bases, DbAttribute):
            bases = (DbAttribute,) + bases

        new_cls = super().__new__(cls, name, bases, namespace)

        params_for_metaclass = {'need_add_this_class_to_dict_classes': True, 'need_DbAttributeMetaclass': True}
        options = {'__dbworkobj__': db_types.NotSet, '__max_repr_recursion_limit__': 10, '__repr_class_name__': db_types.NotSet}

        __annotations__ = {}
        __dict__ = {}
        __db_fields__ = {}
        __meta_options__ = {}

        for i in new_cls.__mro__[::-1]:
            __db_fields__ |= getattr(i, '__db_fields__', {})
            __dict__ |= getattr(i, '__dict__', {})
            __annotations__ |= getattr(i, '__annotations__', {})
            Meta = getattr(i, 'Meta', None)
            if Meta is not None:
                for i in Meta.__mro__[::-1]:
                    __meta_options__ |= getattr(i, '__dict__', {})

        for i in __dict__:
            if i in options:
                options[i] = __dict__[i]
            if i in params_for_metaclass:
                params_for_metaclass[i] = kwargs[i]

        for i in __meta_options__:
            if i in options:
                options[i] = __meta_options__[i]
            if i in params_for_metaclass:
                params_for_metaclass[i] = kwargs[i]

        for i in kwargs:
            if i in options:
                options[i] = kwargs[i]
            if i in params_for_metaclass:
                params_for_metaclass[i] = kwargs[i]

        if not params_for_metaclass['need_DbAttributeMetaclass']:
            return new_cls

        new_cls.__repr_class_name__ = name

        for i in options:
            if options[i] is not db_types.NotSet:
                setattr(new_cls, i, options[i])

        if getattr(new_cls, '__dbworkobj__', None) is None:
            raise Exception(f'The "{new_cls.__name__}" class dosn\'t have "__dbworkobj__" parameter: set "__dbworkobj__" or "Meta", see documentation')

        attr_names = list(__annotations__.keys())
        set_attr_names = set(attr_names)
        for i in __dict__:
            if isinstance(__dict__[i], db_types.DbField) and i not in set_attr_names:
                attr_names.append(i)
                set_attr_names.add(i)

        for attr_name in attr_names:
            if attr_name == 'id': continue
            attr_value = __dict__.get(attr_name, db_types.MISSING)
            attr_type = __annotations__.get(attr_name, db_types.MISSING)

            if get_origin(attr_type) is ClassVar:
                continue

            if isinstance(attr_value, db_types.DbField):
                db_field = attr_value
            elif isinstance(attr_value, db_types.Factory):
                db_field = db_types.DbField(default_factory=attr_value)
            else:
                db_field = db_types.DbField(default=attr_value)

            if attr_type is not db_types.MISSING and db_field.python_type is db_types.MISSING:
                db_field.python_type = attr_type
            if db_field.python_type is db_types.MISSING:
                if db_field.default is not db_types.MISSING:
                    db_field.python_type = type(db_field.default)
                elif db_field.default_factory is not db_types.MISSING: #the idea: is to add a parameter for metaclass so as not to call default_factory to determine the type of the variable.
                    db_field.python_type = type(db_field.default_factory.get_value())
            if db_field.python_type is db_types.MISSING:
                raise f'the type for {attr_name} of {name} is not set (add python_type for DbField or set type in annotations or set default for DbField or set default_factory for DbField)'

            __db_fields__[attr_name] = db_field

        __cls_dict__ = getattr(new_cls, '__dict__')
        setattr(new_cls, '__db_fields__', __db_fields__)

        for attr_name in __cls_dict__['__db_fields__']:
            setattr(new_cls, attr_name, discriptor.DbAttributeDiscriptor(new_cls, attr_name))

        cls.dict_classes.replace(new_cls)

        required_params = []
        optional_params = []

        for field_name, field_value in __db_fields__.items():
            is_required = False
            if isinstance(field_value, db_types.DbField):
                default = field_value.get_default()
                if default is db_types.MISSING:
                    is_required = True
            else:
                if field_value is db_types.MISSING:
                    is_required = True

            if is_required:
                required_params.append(field_name)
            else:
                optional_params.append(f"{field_name}=db_types.NotSet")

        params = required_params + optional_params
        params_str = ', '.join(params)

        init_code = (
            f"def __init__(self, {params_str}, id:int=db_types.NotSet, _dont_add_id:bool = False):\n"
            "    now_locals = locals()\n"
            "    used_keys = now_locals\n"
            "    for i in ['self', 'id', '_dont_add_id']:\n"
            "        used_keys.pop(i)\n"
            "    if not self.__dbworkobj__.cheak_exists_id_table(self.__class__.__name__):\n"
            "        self.__dbworkobj__.create_id_table(self.__class__.__name__)\n"
            "    if isinstance(id, db_types.Id):\n"
            "        id = id.Id\n"
            "    if id is db_types.NotSet:\n"
            "        id = self.__dbworkobj__.get_new_id(self.__class__.__name__)['data']\n"
            "    elif not (_dont_add_id and len([i for i in used_keys if used_keys[i] is not db_types.NotSet]) == 0):\n"
            "        self.__dbworkobj__.add_id(self.__class__.__name__, id)\n"
            "    setattr(self, 'id', id)\n"
            "    for name in __db_fields__:\n"
            "        value = used_keys[name]\n"
            "        if value is db_types.NotSet:\n"
            "            continue\n"
            "        if isinstance(value, db_types.Factory):\n"
            "            setattr(self, name, value.get_value())\n"
            "        else:\n"
            "            setattr(self, name, value)\n"
        )

        exec_globals = {
            'db_types': db_types,
            '__db_fields__': __db_fields__
        }
        exec(init_code, exec_globals)
        init_method = exec_globals['__init__']

        new_cls.__init__ = init_method
        if params_for_metaclass['need_add_this_class_to_dict_classes']:
            cls.dict_classes.add(new_cls)

        if not new_cls.__dbworkobj__.cheak_exists_id_table(new_cls.__name__):
            new_cls.__dbworkobj__.create_id_table(new_cls.__name__)

        return new_cls

    def __iter__(self):
        return (self.get(id=i) for i in self.get_all_ids())


class DbAttribute:
    id: int
    __dbworkobj__: ClassVar[db_work.Db_work] = None
    __max_repr_recursion_limit__: ClassVar[int] = 10
    __repr_class_name__: ClassVar[str] = db_types.NotSet

    def __init__(self, *args, ID=None, **kwargs):
        raise 'Need set metaclass=DbAttributeMetaclass'
    def __repr__(self):
        return self.__get_repr__(set())
    def __get_repr__(self, Objs: set, now: int=0):
        if now > self.__max_repr_recursion_limit__ or (self.id, self.__repr_class_name__) in Objs:
            return f'{self.__repr_class_name__}(id={self.id}, ...)'
        Objs.add((self.id, self.__repr_class_name__))
        return f'''{self.__repr_class_name__}(id={self.id}, {", ".join([f"{i}={obj.__get_repr__(Objs, now+1) if hasattr(obj:=getattr(self, i), '__get_repr__') else f'{repr(getattr(self, i))}'}" for i in self.__db_fields__])})'''

    def _db_attribute_container_update(self, key, data=None):
        """
        call this functions, when any container attribute is updated, to update this attribute in db
        :param key: name attribute container which update
        :type key: str
        :param data: the attribute (DbDict, DbSet and others containers)
        """
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        if ('_'+key in self_dict) or (key not in cls.__dict__['__db_fields__']):
            return
        cls.__dict__[key].container_update(self, data)

    @classmethod
    def _db_attribute_found_ids_by_attribute(cls, attribute_name:str, attribute_value):
        tempdata = cls.__dbworkobj__.found_ids_by_value(class_name=cls.__name__, attribute_name=attribute_name, data=attribute_value, _cls_dbattribute=cls)
        if tempdata['status_code'] != 200:
            return set()
        return tempdata['data']

    @classmethod
    def get(cls, id):
        """
        return the one object with this id or None, if it's obj is not found
        if the 'get' method finds multiple search results, it selects the smallest id.
        if the 'get' method does not find any search results, it returns None.
        :param id:
        :type id: int | db_types.Id | discriptor.Condition
        :return: obj | None
        """
        if isinstance(id, discriptor.Condition):
            Ids = id.found()
            if not Ids:
                return None
            id = Ids.list_ids[0]
        if isinstance(id, db_types.Id):
            id = id.Id
        if isinstance(id, int) or isinstance(id, db_types.Id):
            obj = cls.__new__(cls)
            obj.id = id
            return obj
        return None

    @classmethod
    def get_all_ids(cls):
        temp = cls.__dbworkobj__.get_all_ids(cls.__name__)
        if temp['status_code'] != 200:
            return db_types.Ids()
        return db_types.Ids(temp['data'])

    def dump(self, attributes:set[str]=None):
        """
        Use it func, if you need dump the data to db, with manual_dump_mode
        """
        self_dict = object.__getattribute__(self, '__dict__')
        cls = object.__getattribute__(self, '__class__')
        all_attributes = object.__getattribute__(self, '__db_fields__')
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
        all_attributes = object.__getattribute__(self, '__db_fields__')
        self_dict = object.__getattribute__(self, '__dict__')
        for db_attr in (all_attributes if attributes is None else all_attributes.keys() & attributes):
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
        all_attributes = object.__getattribute__(self, '__db_fields__')
        for db_attr in all_attributes if attributes is None else all_attributes & attributes:
            if '_'+db_attr in self_dict:
                del self_dict['_'+db_attr]

    def delete(self, attributes:set[str]=None):
        """
        Delete this id from db
        :param attributes: attributes to be deleted, ex: obj.delete({'name', 'age'})
        :return:
        """
        all_attributes = object.__getattribute__(self, '__db_fields__')
        for db_attr in all_attributes if attributes is None else all_attributes & attributes:
            delattr(self, db_attr)

    @classmethod
    def delete_objs(cls, IDs: set[int] | int, attributes:set[str]=None):
        all_attributes = object.__getattribute__(cls, '__db_fields__')
        attributes = all_attributes if attributes is None else attributes & all_attributes
        IDs = {IDs} if isinstance(IDs, int) else IDs
        dbworkobj = cls.__dbworkobj__
        clsname = cls.__name__
        for ID in IDs:
            for db_attr in attributes:
                dbworkobj.del_attribute_value(class_name=clsname, attribute_name=db_attr, ID=ID)

    @classmethod
    def found(cls, **kwargs):
        """
        WARNING: This function has lost its relevance and is not supported. Use '(cls.attr == value).found()' or 'cls.get(cls.attr == value)'

        found ids objs with this values of attributes, ex:
        objs: User(id=1, name='Bob', age=3), User(id=2, name='Bob', age=2), User(id=3, name='Anna', age=2)
        User.found(name='Bob') -> {1, 2}
        User.found(age=2) -> {2, 3}
        User.found(name='Bob', age=2) -> {2}
        :param kwargs: names and values of attributes (see doc.)
        :return: set of ids
        """
        if not kwargs: return set()
        res = cls._db_attribute_found_ids_by_attribute(attribute_name=(temp:=next(iter(kwargs))), attribute_value=kwargs[temp])
        for key in kwargs:
            res &= cls._db_attribute_found_ids_by_attribute(attribute_name=key, attribute_value=kwargs[key])
        return res
