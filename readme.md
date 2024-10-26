DbAtribute - Database Atribute
=========================

This module allows you to save attributes of objects not in RAM, but in a database. the closest analogue is SQLAlchemy. Unlike SQLAlchemy, this module maximizes automatism, allowing the developer to focus on other details without worrying about working with the database.

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

### Example 1

with `_db_Atribute__list_db_atributes`

```python
from dataclasses import dataclass, field
from typing import ClassVar

from db_atribute import dbDecorator, DbAtribute, db_work, connector

from _db_info import host, user, password, database

connect_obj = connector.Connection(host=host, user=user, password=password, database=database)
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

### Example 2

without `_db_Atribute__list_db_atributes` (automatic created)

```python
from dataclasses import dataclass, field

from db_atribute import dbDecorator, DbAtribute, db_field, db_work, connector

from _db_info import host, user, password, database

connect_obj = connector.Connection(host=host, user=user, password=password, database=database)
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

### Example 3

with `id` (in other cases, id inheritance from DbAtribute.DbAtribute)

```python
from dataclasses import dataclass
from db_atribute import dbDecorator, DbAtribute

#craete db_work_obj

@dbDecorator(_db_Atribute__dbworkobj=...) #... is db_work_obj
@dataclass
class User(DbAtribute):
    id: int
    #other code
```

### Example 4

you can set _db_Atribute_dbworkobj in class

```python
from dataclasses import dataclass
from typing import ClassVar
from db_atribute import dbDecorator, DbAtribute

#craete db_work_obj

@dbDecorator
@dataclass
class User(DbAtribute):
    _db_Atribute_dbworkobj: ClassVar = ... #*db_work_obj*
    #other code
```

## Work with obj

for create obj use id and other fields,

### Found obj by id
if you need recreated obj, you can call your cls with id.

```python
obj = User(id=3)
print(obj) #User(id=3, name='name_of_obj3', age='age_of_obj3')

obj = User(3)
print(obj) #User(id=3, name='name_of_obj3', age='age_of_obj3')

obj = User(3, name='new_name_of_obj3')
print(obj) #User(id=3, name='new_name_of_obj3', age='age_of_obj3')

obj = User(id=3, age='new_age_of_obj3')
print(obj) #User(id=3, name='new_name_of_obj3', age='new_age_of_obj3')

obj = User(3)
print(obj) #User(id=3, name='new_name_of_obj3', age='new_age_of_obj3')
```

### Found obj by other atributes

```python
obj = User(id=1, name='Bob', age=3),
obj = User(id=2, name='Bob', age=2),
obj = User(id=3, name='Anna', age=2)

print(User.db_atribute_found_ids(name='Bob')) #{1, 2}
print(User.db_atribute_found_ids(age=2)) #{2, 3}
print(User.db_atribute_found_ids(name='Bob', age=2)) #{2}
```

### Dump_mode

if in any function you will work with obj, you can activate undump_mode,

*dump_mode*: atributes don't save in self.__dict__, all changes automatic dump in db.

*undump_mode*: all atributes save in self.__dict__, and won't dump in db until self.db_atribute_set_dump_mode is called. this helps to quickly perform operations on containers db attributes

DbAtribute.db_atribute_set_dump_mode set dump_mode to True and call dump

DbAtribute.db_atribute_set_undump_mode set dump_mode to False

```python
from dataclasses import dataclass, field

from db_atribute import db_work
from db_atribute import dbDecorator, DbAtribute, db_field, connector

from _db_info import host, user, password, database

connect_obj = connector.Connection(host=host, user=user, password=password, database=database)
db_work_obj = db_work.Db_work(connect_obj)

@dbDecorator(_db_Atribute__dbworkobj=db_work_obj)
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
from dataclasses import dataclass, field
import time

from db_atribute import db_work
from db_atribute import dbDecorator, DbAtribute, db_field, connector

from _db_info import host, user, password, database

connect_obj = connector.Connection(host=host, user=user, password=password, database=database)
db_work_obj = db_work.Db_work(connect_obj)

@dbDecorator(_db_Atribute__dbworkobj=db_work_obj)
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

this module used mysql db, and for use it, you need install mysql from https://www.mysql.com/downloads

