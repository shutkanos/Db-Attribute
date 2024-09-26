from dataclasses import dataclass, field
from typing import ClassVar
import sys

import db_atribute
from db_atribute import dbDecorator, Db_Atribute, db_field

@dbDecorator
@dataclass
class User(Db_Atribute):
    other_dict_information: dict = field(default_factory=lambda:{})
    name: str = db_field(default='NotSet')
    age: int = db_field(default=-1)
    ban: bool = db_field(default=False)
    other_int_information: int = 100
    list_of_books: list = db_field(default_factory=lambda:[])
    sittings: dict = db_field(default_factory=lambda:{})

@dbDecorator
@dataclass
class User2(Db_Atribute):
    other_dict_information: dict = field(default_factory=lambda:{})
    name: str = 'NotSet'
    age: int = -1
    ban: bool = False
    other_int_information: int = 100
    list_of_books: list = field(default_factory=lambda:[])
    sittings: dict = field(default_factory=lambda:{})
    _db_Atribute__list_db_atributes: ClassVar[list] = ['name', 'age', 'ban', 'list_of_books', 'sittings']

#a = User(10, name='shutka', age=748924, ban=False, list_of_books=['Hello world!', 'name of hiro'], sittings={'user': {'language': 'ru'}, 'other': {'other1', 'other2'}})
a = User(10)
print(a)
print(a.__dict__)

"""print(sys.getsizeof(a))
print(sys.getsizeof(a.__dict__))
print(sum(sys.getsizeof(i) for i in a.__dict__.keys()))
print(sum(sys.getsizeof(i) for i in a.__dict__.values()))"""