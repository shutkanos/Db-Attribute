import db_atribute
from dataclasses import  dataclass, field
from typing import ClassVar
import sys

def dbDecorator(cls=None, /, *, arg1=True, arg2=False):
    def wrap(cls):
        #print(cls, arg1, arg2)
        #print(cls.__dict__)
        #print(cls.__anotations__)
        #print(cls.__init__)
        def new_init(*args, **kwargs):
            print(f'{kwargs=}')
            return cls.__old_init__(*args, **kwargs)
        cls.__old_init__ = cls.__init__
        cls.__init__ = new_init
        return cls
    if cls is None:
        return wrap
    return wrap(cls)

@dbDecorator
@dataclass(kw_only=True)
class User(db_atribute.Db_Atribute):
    name: str
    age: int
    ban: bool
    list_of_books: list
    sittings: dict
    _db_Atribute__list_db_atributes: ClassVar[list] = ['name', 'age', 'ban', 'list_of_books', 'sittings']

a = User(id=10, name='shutkanos', age=748924, ban=False, list_of_books=['Hello world!', 'name of hiro'], sittings={'user': {'language': 'ru'}, 'other': {'other1', 'other2'}})
#a = User(id=10)
print(a)
print(a.__dict__)
#print(a.__class__._db_Atribute__list_db_atributes)

"""print(sys.getsizeof(a))
print(sys.getsizeof(a.__dict__))
print(sum(sys.getsizeof(i) for i in a.__dict__.keys()))
print(sum(sys.getsizeof(i) for i in a.__dict__.values()))"""