DbAtribute - Database Atribute
=========================

This module allows you to save attributes of objects not in RAM, but in a database. the closest analogue is <a href='https://github.com/sqlalchemy/sqlalchemy'>SQLAlchemy</a>. Unlike SQLAlchemy, this module maximizes automatism, allowing the developer to focus on other details without worrying about working with the database.

# Supported types

This module supported standart types: `int`, `float`, `str`, `bool`, `tuple`, `list`, `set`, `dict`.

if the developer needs other data types, he will need to write an adapter class.

# How it used

## Create class

for any class with DbAtribute you need

* Inheritance the `DbAtribute.DbAtribute`
* Use `@dataclasses.dataclass`
* Use `@DbAtribute.dbDecorator`
* create any field for database
* create `_db_Atribute__list_db_atributes: typing.ClassVar[list]` with database fields names.

with `_db_Atribute__list_db_atributes`

```python
from dataclasses import dataclass, field
from typing import ClassVar

from db_atribute import dbDecorator, DbAtribute, db_work, connector

connect_obj = connector.Connection(host=*mysqlhost*, user=*user*, password=*password*, database=*database name*)
db_work_obj = db_work.Db_work(connect_obj)


@dbDecorator(_db_Atribute__dbworkobj=db_work_obj)
@dataclass
class User(DbAtribute):
    other_dict_information: dict = field(default_factory=lambda: {})
    name: str = 'NotSet'
    age: int = -1
    ban: bool = False
    other_int_information: int = 100
    list_of_books: list = field(default_factory=lambda: [])
    sittings: dict = field(default_factory=lambda: {})
    _db_Atribute__list_db_atributes: ClassVar[list] = ['name', 'age', 'ban', 'list_of_books', 'sittings']
```

without `_db_Atribute__list_db_atributes` (automatic created)

```python
from dataclasses import dataclass, field

from db_atribute import dbDecorator, DbAtribute, db_field, db_work, connector

connect_obj = connector.Connection(host=*mysqlhost*, user=*user*, password=*password*, database=*database name*)
db_work_obj = db_work.Db_work(connect_obj)

@dbDecorator(_db_Atribute__dbworkobj=db_work_obj)
@dataclass
class User(DbAtribute):
    other_dict_information: dict = field(default_factory=lambda:{})
    name: str = db_field(default='NotSet')
    age: int = db_field(default=-1)
    ban: bool = db_field(default=False)
    other_int_information: int = 100
    list_of_books: list = db_field(default_factory=lambda:[])
    sittings: dict = db_field(default_factory=lambda:{})
```

with `id` (in other cases, id inheritance from DbAtribute.DbAtribute)

```python
@dbDecorator(_db_Atribute__dbworkobj=*db work obj*)
@dataclass
class User(DbAtribute):
    id: int
    #other code
```

you can set _db_Atribute_dbworkobj in class

```python
@dbDecorator
@dataclass
class User(DbAtribute):
    _db_Atribute_dbworkobj: ClassVar = ... #*db_work_obj*
    #other code
```

## Work with obj

### Create new obj / add obj do db

for create obj use id and other fields,

```python
obj = User(id=3) # other field set to defaults value
print(obj) # User(id=3, name=*default value*)
```
```python
obj = User(id=3, name='Ben')
print(obj) # User(id=3, name='Ben')
```

### Found obj by id
if you need recreated obj, you can call your cls with id.

```python
obj = User(3, name='Ben', age=10) #insert obj to db
print(obj) #User(id=3, name='Ben', age=10)

obj = User(3)
print(obj) #User(id=3, name='Ben', age=10)

obj = User(3, 'Anna')
print(obj) #User(id=3, name='Anna', age=10)

obj = User(id=3, age=15)
print(obj) #User(id=3, name='Anna', age=15)

obj = User(3)
print(obj) #User(id=3, name='Anna', age=15)
```

### Found obj by other atributes

use cls.db_atribute_found_ids(**atributes) for get all ids with values of this atributes

```python
obj = User(id=1, name='Bob', age=3),
obj = User(id=2, name='Bob', age=2),
obj = User(id=3, name='Anna', age=2)

print(User.db_atribute_found_ids(name='Bob')) #{1, 2}
print(User.db_atribute_found_ids(age=2)) #{2, 3}
print(User.db_atribute_found_ids(name='Bob', age=2)) #{2}
```

### Change atribute of obj

```python
obj = User(id=1, name='Bob', list_of_books=[])

print(obj) #User(id=1, name='Bob', list_of_books=[])

obj.name = 'Anna'
obj.sittings.append('Any name of book')

print(obj) #User(id=1, name='Anna', list_of_books=['Any name of book'])
print(obj.sittings[0]) #Any name of book
print(obj.name) #Anna
```

### Dump_mode

if in any function you will work with obj, you can activate undump_mode,

*dump_mode*: atributes don't save in self.__dict__, all changes automatic dump in db.

*undump_mode*: all atributes save in self.__dict__, and won't dump in db until self.db_atribute_set_dump_mode is called. this helps to quickly perform operations on containers db attributes

DbAtribute.db_atribute_set_dump_mode set dump_mode to True and call dump

DbAtribute.db_atribute_set_undump_mode set dump_mode to False

```python
@dbDecorator(_db_Atribute__dbworkobj=*db work obj*)
@dataclass
class User(DbAtribute):
    list_of_books: list = db_field(default_factory=lambda:[])

def update_list_of_books_for_this_user(id_user):
    user = User(id_user)
    user.db_atribute_set_undump_mode()
    for i in range(10**5):
        user.list_of_books.append(i)
    user.db_atribute_set_dump_mode()

update_list_of_books_for_this_user(1)
```

if you need dump attributes to db with undump_mode, you can use DbAtribute.db_atribute_dump

```python
@dbDecorator(_db_Atribute__dbworkobj=*db work obj*)
@dataclass
class User(DbAtribute):
    list_of_books: list = db_field(default_factory=lambda:[])

def update_list_of_books_for_this_user(id_user):
    user = User(id_user)
    user.db_atribute_set_undump_mode()
    for i in range(10**4):
        user.list_of_books.append(i)
    user.db_atribute_dump() #dump the list_of_books to db
    time.sleep(60)
    for i in range(10**4):
        user.list_of_books.append(i)
    user.db_atribute_set_dump_mode()

update_list_of_books_for_this_user(1)
```

# Data base

this module used mysql db, and for use it, you need install <a href='https://www.mysql.com'>mysql</a>

