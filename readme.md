DbAttribute - Database Attribute
=========================

This module allows you to save attributes of objects not in RAM, but in a database. the closest analogue is <a href='https://github.com/sqlalchemy/sqlalchemy'>SQLAlchemy</a>. Unlike SQLAlchemy, this module maximizes automatism, allowing the developer to focus on other details without worrying about working with the database.

# Supported types

This module supported standart types: `int`, `float`, `str`, `bool`, `None`, `tuple`, `list`, `set`, `dict`, `datetime`.

if the developer needs other data types, he will need to write an adapter class.

# How it used

## Create class

for any class with DbAttribute you need

* Inheritance the `DbAttribute.DbAttribute`
* Use `@dataclasses.dataclass`
* Use `@DbAttribute.dbDecorator`
* create any field for database
* create `_db_attribute__list_db_attributes: typing.ClassVar[set]` with database fields names.

with `_db_attribute__list_db_attributes`

```python
from dataclasses import dataclass, field
from typing import ClassVar

from db_attribute import dbDecorator, DbAttribute, db_work, connector

connect_obj = connector.Connection(host=*mysqlhost*, user=*user*, password=*password*, database=*databasename*)
db_work_obj = db_work.Db_work(connect_obj)


@dbDecorator(_db_attribute__dbworkobj=db_work_obj)
@dataclass
class User(DbAttribute):
    other_dict_information: dict = field(default_factory=lambda: {})
    name: str = 'NotSet'
    age: int = -1
    ban: bool = False
    other_int_information: int = 100
    list_of_books: list = field(default_factory=lambda: [])
    sittings: dict = field(default_factory=lambda: {})
    _db_attribute__list_db_attributes: ClassVar[set] = {'name', 'age', 'ban', 'list_of_books', 'sittings'}
```

without `_db_attribute__list_db_attributes` (automatic created)

```python
from dataclasses import dataclass, field

from db_attribute import dbDecorator, DbAttribute, db_field, db_work, connector

connect_obj = connector.Connection(host=*mysqlhost*, user=*user*, password=*password*, database=*databasename*)
db_work_obj = db_work.Db_work(connect_obj)


@dbDecorator(_db_attribute__dbworkobj=db_work_obj)
@dataclass
class User(DbAttribute):
    other_dict_information: dict = field(default_factory=lambda: {})
    name: str = db_field(default='NotSet')
    age: int = db_field(default=-1)
    ban: bool = db_field(default=False)
    other_int_information: int = 100
    list_of_books: list = db_field(default_factory=lambda: [])
    sittings: dict = db_field(default_factory=lambda: {})
```

with `id` (in other cases, id inheritance from DbAttribute.DbAttribute)

```python
@dbDecorator(_db_attribute__dbworkobj=*db work obj*)
@dataclass
class User(DbAttribute):
    id: int
    #other code
```

you can set _db_attribute__dbworkobj in class

```python
@dbDecorator
@dataclass
class User(DbAttribute):
    _db_attribute__dbworkobj: ClassVar = ... #*db work obj*
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

### Found obj by other attributes

use cls.db_attribute_found_ids(**attributes) for get all ids with values of this attributes

```python
obj = User(id=1, name='Bob', age=3),
obj = User(id=2, name='Bob', age=2),
obj = User(id=3, name='Anna', age=2)

print(User.db_attribute_found_ids(name='Bob')) #{1, 2}
print(User.db_attribute_found_ids(age=2)) #{2, 3}
print(User.db_attribute_found_ids(name='Bob', age=2)) #{2}
```

### Change attribute of obj

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

*dump_mode*: attributes don't save in self.__dict__, all changes automatic dump in db.

*undump_mode*: all attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_dump_mode is called. this helps to quickly perform operations on containers db attributes

DbAttribute.db_attribute_set_dump_mode set dump_mode to True and call dump

DbAttribute.db_attribute_set_undump_mode set dump_mode to False

```python
user = User(id=1, any_db_data1=531, any_db_data2='string')
print(user.__dict__)
#{'id': 1, '_db_Attribute__dump_mode': True}
user.db_attribute_set_undump_mode()
print(user.__dict__)
#{'id': 1, 'any_db_data1': 531, 'any_db_data2': 'string', '_db_Attribute__dump_mode': True}
```

```python
user = User(id=1, list_of_books=[])
user.db_attribute_set_undump_mode()
for i in range(10**5):
    user.list_of_books.append(i)
user.db_attribute_set_dump_mode()
```

if you need dump attributes to db with undump_mode, you can use DbAttribute.db_attribute_dump

```python
user = User(id=1, list_of_books=[])
user.db_attribute_set_undump_mode()
for i in range(10**4):
    user.list_of_books.append(i)
user.db_attribute_dump() #dump the list_of_books to db
for i in range(10**4):
    user.list_of_books.append(i)
user.db_attribute_set_dump_mode()
```

## Types
### Db classes
when collections are stored in memory, they converted to Db classes
```python
obj = User(1, list_of_books=[1, 2, 3])
print(type(obj.list_of_books)) #DbList
```
```python
obj = User(1, times=[datetime(2024, 1, 1)])
print(type(obj.times[0])) #DbDatetime
```
and when collections dumped to db, they converted to json
```python
obj = User(1, list_of_books=[1, 2, 3])
print(obj.list_of_books.dumps()) #{"t": "DbList", "d": [1, 2, 3]}
```
```python
obj = User(1, times=[datetime(2024, 1, 1), datetime(2027, 7, 7)])
print(obj.list_of_books.dumps())
#{"t": "DbList", "d": [{"t": "DbDatetime", "d": "2024-01-01T00:00:00"}, {"t": "DbDatetime", "d": "2027-07-07T00:00:00"}]}
```

### Json type

db attribute support `tuple`, `list`, `dict`, other collections, but this types slow, because uses Db classes (see [speed test](#speed-test)).

to solve this problem, use a Json convertation

```python
from db_attribute.dbtypes import JsonType

@dbDecorator(_db_attribute__dbworkobj=*db work obj*)
@dataclass
class User(DbAttribute):
    sittings: JsonType = db_field()

obj = User(1, sittings={1: 2, 3: [4, 5]})
print(obj.sittings)  # {'1': 2, '3': [4, 5]}
print(type(obj.sittings))  # dict
```
but:
1) if you change obj with JsonType, this obj don't dump to db, you need set the new obj
2) the json support only `dict`, `list`, `str`, `int`, `float`, `True`, `False`, `None`

```python
obj = User(1, sittings={1: 2, 3: [4, 5]})
del obj.sittings['3'] # not changed
obj.sittings['1'] = 3 # not changed
obj.sittings |= {4: 5} # not changed
print(obj.sittings) #{'1': 2, '3': [4, 5]}
obj.sittings = {1: 3} # changed
print(obj.sittings) #{'1': 3}
```

# Speed Test

`op/sec` - `operation/second`

mysql `select` - `12500` op/sec </br>
db_attribute `get_attr`:

`int`:      11658 op/sec -6%<br>
`str`:      11971 op/sec -4%<br>
`tuple`:    9685 op/sec -22%<br>
`list`:     9161 op/sec -26%<br>
`dict`:     9311 op/sec -25%<br>
`JsonType`: 11937 op/sec -4%<br>

mysql `insert/update` - `4500` op/sec<br>
db_attribute `set_attr`:

`int`:      4552 op/sec +0%<br>
`str`:      4341 op/sec -3% <br>
`tuple`:    3419 op/sec -24%<br>
`list`:     3271 op/sec -27%<br>
`dict`:     3332 op/sec -25%<br>
`JsonType`: 4165 op/sec -7%<br>

# Data base

this module used mysql db, and for use it, you need install <a href='https://www.mysql.com'>mysql</a>

