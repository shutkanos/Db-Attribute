import dataclasses

class _NotSetMetaClass(type):
    @classmethod
    def __repr__(cls):
        return 'NotSet'

class NotSet(metaclass=_NotSetMetaClass):
    pass

class JsonType:
    pass

class DbField(dataclasses.Field):
    pass

class DbAttributeType:
    def __init__(self, name_cls):
        self.name_cls = name_cls
    def __repr__(self):
        return f'temp type of {self.name_cls} class'

class DictClasses:
    def __init__(self):
        self.data = dict()
        self.needdata = dict()

    def add(self, cls):
        self.data[cls.__name__] = cls
        for othercls in self.needdata.get(cls.__name__, []):
            for nameattr in othercls.__annotations__:
                if isinstance(othercls.__annotations__[nameattr], DbAttributeType) and othercls.__annotations__[nameattr].name_cls == cls.__name__:
                    othercls.__annotations__[nameattr] = cls
        if cls.__name__ in self.needdata:
            del self.needdata[cls.__name__]
        for nameattr in cls.__annotations__:
            if isinstance(cls.__annotations__[nameattr], DbAttributeType):
                temp = cls.__annotations__
                if temp[nameattr].name_cls in self.data:
                    temp[nameattr] = self.data[temp[nameattr].name_cls]
                else:
                    if temp[nameattr].name_cls not in self.needdata:
                        self.needdata[temp[nameattr].name_cls] = []
                    self.needdata[temp[nameattr].name_cls].append(cls)

dict_classes = DictClasses()

if __name__ == "__main__":
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

