import collections, json
from typing import Callable, Any

import db_attribute

db_class = db_attribute.db_class

class _ReprMetaClass(type):
    def __repr__(cls):
        return cls.__name__

class NotSet(metaclass=_ReprMetaClass):
    pass

class MISSING(metaclass=_ReprMetaClass):
    pass

class Id:
    def __init__(self, Id: int, cls_name=None):
        self.Id = Id
        self.cls_name = cls_name
    def __repr__(self):
        return f'{self.cls_name}(id={self.Id})' if self.cls_name else f'Any(id={self.Id})'

class Ids:
    def __init__(self, Ids=None, cls_name=None):
        if Ids is None:
            Ids = []
        self.set_ids = set(Ids)
        self.list_ids = sorted(list(self.set_ids))
        self.cls_name = cls_name
        for i in range(len(self.list_ids)):
            if not isinstance(self.list_ids[i], Id):
                self.list_ids[i] = Id(self.list_ids[i], cls_name=cls_name)
        self.set_ids = set(self.list_ids)
    def __len__(self):
        return len(self.list_ids)
    def __bool__(self):
        return bool(self.list_ids)
    def __iter__(self):
        return iter(self.list_ids)
    def __repr__(self):
        return f'{self.cls_name if self.cls_name else "Ids"}({[i.Id for i in self.list_ids]})'

class JsonType:
    pass

class Factory:
    def __init__(self, fabric):
        self.fabric = fabric.fabric if isinstance(fabric, Factory) else fabric
    def get_value(self):
        return self.fabric()
    def __call__(self):
        return self.fabric()
    def __repr__(self):
        return 'FACTORY'

class DbField:
    def __init__(self, default:Any=MISSING, default_factory:Callable[[], Any]=MISSING, python_type:Any=MISSING, mysql_type:str=MISSING, repr:bool=True, init:bool=True, search_default:bool=True, **kwargs):
        """
        :param default: the default value of this Field (default takes precedence over the default_factory)
        :type default: Any
        :param default_factory: the default factory of this Field
        :type mysql_type: Callable[[], Any]
        :param python_type: python type of data, example: str, int (python_type takes precedence over the data type specified in the annotation)
        :type python_type: Any
        :param mysql_type: mysql type of data, example: 'varchar(50)', 'bigint'
        :type mysql_type: str
        :param repr: Include field in `__repr__()` output
        :type repr: bool
        :param init: Include field in constructor (`__init__()`)
        :type init: bool
        :param search_default: When True, applies default value during searches if record is missing in this field's table (Use this parameter if you understand what it is responsible for.)
        :type search_default: bool
        :param kwargs:
        """
        self.default = default
        self.default_factory = MISSING if default_factory is MISSING else Factory(default_factory)
        self.python_type = python_type
        self.mysql_type = mysql_type
        self.repr = repr
        self.init = init
        self.search_default = search_default


    def __repr__(self):
        return f'''DbField({", ".join([f"{i} = {self.__dict__[i]}" for i in self.__dict__ if self.__dict__[i] is not MISSING])})'''

    def get_default(self):
        if self.default is not MISSING:
            return self.default
        if self.default_factory is not MISSING:
            return self.default_factory.get_value()
        return MISSING

class TableType:
    def __init__(self, name_cls):
        self.name_cls = name_cls
    def __repr__(self):
        return f'temp type of {self.name_cls} class'

class TableObject:
    def __init__(self, name_cls, args=None, kwargs=None):
        self.name_cls = name_cls
        self.args = [] if args is None else args
        self.kwargs = dict() if kwargs is None else kwargs
    def __repr__(self):
        return f'temp type of {self.name_cls} class'

class DictClasses:
    """
    DictClasses is used to store DbAttribute classes.
    It replaces the TableType and TableObject classes, which use a string to define these classes.
    Created DbContainer for classes (for saved in DbList, DbDict and other).
    :argument data: main data store. Example: {'User': User, 'Book': Book}
    """
    def __init__(self):
        self.data = dict()
        self.needdata = collections.defaultdict(set)
        self.db_containers = dict()

    def add(self, cls):
        self.data[cls.__name__] = cls
        self.db_containers[cls.__name__] = _created_db_class(cls)
        for othercls in self.needdata.get(cls.__name__, []):
            self.replace(othercls)
        if cls.__name__ in self.needdata:
            del self.needdata[cls.__name__]
        self.replace(cls)

    def replace(self, cls):
        temp = cls.__db_fields__
        for nameattr in temp:
            if isinstance(temp[nameattr].python_type, TableType):
                if temp[nameattr].python_type.name_cls in self.data:
                    temp[nameattr].python_type = self.data[temp[nameattr].python_type.name_cls]
                else:
                    self.needdata[temp[nameattr].python_type.name_cls].add(cls)
            value = temp[nameattr].get_default()
            if isinstance(value, TableObject):
                if value.name_cls in self.data:
                    now_need_cls = self.data[value.name_cls]
                    now_need_args = value.args
                    now_need_kwargs = value.kwargs
                    temp[nameattr].default = MISSING
                    temp[nameattr].default_factory = Factory(lambda: now_need_cls(*now_need_args, **now_need_kwargs))
                else:
                    self.needdata[value.name_cls].add(cls)

def _created_db_class(cls):
    @db_class.DbClassDecorator(add_class_to_db_class_manager=False)
    class ContainerDbAttribute(db_class.DbClass, cls, need_DbAttributeMetaclass=False, __repr_class_name__=cls.__name__):
        def __init__(self, id: int = NotSet, *args, _use_db=False, _convert_arguments=True, _obj_dbattribute=None, _name_attribute=None, _first_container=None, **kwargs):
            super().__init__(*args, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container, _call_init=False, **kwargs)
            object.__setattr__(self, 'id', id)

        @classmethod
        def __convert_to_db__(cls, obj: db_attribute.DbAttribute, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
            if isinstance(obj, int):
                Id = obj
            else:
                Id = obj.id
            return cls(id=Id, _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

        def dumps(self, _return_json=True):
            if _return_json: return json.dumps({'t': f'ContainerDbAttribute_{cls.__name__}', 'i': self.id})
            return {'t': f'ContainerDbAttribute_{cls.__name__}', 'i': self.id}

        def copy(self):
            return cls(id=self.id)

        @classmethod
        def _loads(cls, tempdata: dict, *, _obj_dbattribute=None, _name_attribute=None, _first_container=None):
            return cls(id=tempdata['i'], _use_db=True, _obj_dbattribute=_obj_dbattribute, _name_attribute=_name_attribute, _first_container=_first_container)

    ContainerDbAttribute.__name__ = f'ContainerDbAttribute_{cls.__name__}'

    db_class.DbClassManager.add_db_class(cls, ContainerDbAttribute)
    return ContainerDbAttribute

def cheak_db_work_object(cls):
    if cls.__skip_dbworkobj__:
        raise Exception(f'For this operation, set the value of the __dbworkobj__ parameter of the {cls} class using the "register_dbworkobj" method')

if __name__ == "__main__":
    Field = DbField(default_factory=lambda:10)
    print(Field.get_default())
    """
    class A:
        b: DbAttributeType('B')
    print(A.__annotations__, f'{dict_classes.data=} {dict_classes.needdata=}')
    dict_classes.add(A)
    print(A.__annotations__, f'{dict_classes.data=} {dict_classes.needdata=}')
    class B:
        a: DbAttributeType('A')
    print(A.__annotations__, B.__annotations__, f'{dict_classes.data=} {dict_classes.needdata=}')
    dict_classes.add(B)
    print(A.__annotations__, B.__annotations__, f'{dict_classes.data=} {dict_classes.needdata=}')
    """

