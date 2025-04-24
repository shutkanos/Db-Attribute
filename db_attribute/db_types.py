import collections

class _NotSetMetaClass(type):
    def __repr__(cls):
        return cls.__name__

class NotSet(metaclass=_NotSetMetaClass):
    pass

class MISSING(metaclass=_NotSetMetaClass):
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
        self.fabric = fabric
    def get_value(self):
        return self.fabric()
    def __call__(self):
        return self.fabric()
    def __repr__(self):
        return 'FACTORY'

class DbField:
    def __init__(self, default=MISSING, default_factory=MISSING, python_type=MISSING, mysql_type=MISSING, repr=True, init=True, **kwargs):
        """Attention! python_type takes precedence over the data type specified in the annotation"""
        self.default = default
        self.default_factory = MISSING if default_factory is MISSING else Factory(default_factory)
        self.python_type = python_type
        self.mysql_type = mysql_type
        self.repr = repr
        self.init = init
    def __repr__(self):
        return f'DbField({", ".join([f"{i} = {self.__dict__[i]}" for i in self.__dict__ if self.__dict__[i] is not MISSING])})'

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
    def __init__(self):
        self.data = dict()
        self.needdata = collections.defaultdict(set)

    def add(self, cls):
        self.data[cls.__name__] = cls
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

dict_classes = DictClasses()

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

