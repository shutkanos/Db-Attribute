DbAttribute - Database Attribute
=========================

This module allows you to save attributes of objects not in RAM, but in a database. the closest analogue is <a href='https://github.com/sqlalchemy/sqlalchemy'>SQLAlchemy</a>. Unlike SQLAlchemy, this module maximizes automatism, allowing the developer to focus on other details without worrying about working with the database.

* [Supported types](#supported-types)
* [How it used](#how-it-used)
    * [Create class](#create-class)
    * [Work with obj](#work-with-obj)
        * [Create new obj / add obj do db](#create-new-obj--add-obj-do-db)
        * [Found obj by id](#found-obj-by-id)
        * [Found obj by other attributes](#found-obj-by-other-attributes)
        * [Change attribute of obj](#change-attribute-of-obj)
        * [Dump mode](#dump-mode)
    * [Types](#types)
        * [Db attribute](#db-attribute)
        * [Db classes](#db-classes)
        * [Json type](#json-type)
* [Speed Test](#speed-test)
  * [Get attr](#get-attr)
  * [Set attr](#set-attr)
* [Data base](#data-base)

# Supported types

This module supported standart types: `int`, `float`, `str`, `bool`, `None`, `tuple`, `list`, `set`, `dict`, `datetime`.

if the developer needs other data types, he will need to write an adapter class.

# How it used

## Create class

for any class with DbAttribute you need

* Inheritance the `DbAttribute.DbAttribute`
* Use `@dataclasses.dataclass`
* Use `@DbAttribute.dbDecorator`
* create any fields and db_fields for database

```python
from dataclasses import dataclass, field

from db_attribute import dbDecorator, DbAttribute, db_field, db_work, connector

connect_obj = connector.Connection(host=*mysqlhost*, user=*user*, password=*password*, database=*databasename*)
db_work_obj = db_work.Db_work(connect_obj)

@dbDecorator(_db_attribute__dbworkobj=db_work_obj)
@dataclass
class User(DbAttribute):
    other_dict_information: dict = field(default_factory=lambda: {}) #not save in db, only in RAM
    name: str = db_field(default='NotSet')
    age: int = db_field(default=-1)
    ban: bool = db_field(default=False)
    other_int_information: int = 100 #not save in db, only in RAM
    list_of_books: list = db_field(default_factory=lambda: ['name of first book'])
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

```python
obj = User(id=1, name='Bob', age=3)
obj = User(id=2, name='Bob', age=2)
obj = User(id=3, name='Anna', age=2)

print(User(name='Bob', age=3).id) #1
print(User(name='Anna').id) #3
print(User(name='Bob').id) #error, a lot of obj found
print(User(name='Other name').id) #error, no obj found
```
or
```python
obj = User(id=1, name='Camel', age=1)
obj = User(id=2, name='Bob', age=2)
obj = User(id=3, name='Anna', age=3)

print(User(User.age == 2)) #User(id=2, name='Bob', age=2)
print(User(User.age < 2)) #User(id=1, name='Camel', age=1)
print(User(User.name < 'Bob')) #User(id=3, name='Anna', age=3)
print(User(User.name._like('A%'))) #User(id=3, name='Anna', age=3)

print(User.age > 1) #{2, 3}
print(User.name > 'A') #{1, 2, 3}
print(User.name > 'Anna') #{1, 2}

print(User.name._like('%a%')) #{1, 3}, see Like in sql
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

### Dump mode

if in any function you will work with obj, you can activate manual_dump_mode (auto_dump_mode is default),

`auto_dump_mode`: attributes don't save in self.__dict__, all changes automatic dump in db.

`manual_dump_mode`: attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_dump_mode is called. this helps to quickly perform operations on containers db attributes

DbAttribute.db_attribute_set_auto_dump_mode set auto_dump_mode and call dump

DbAttribute.db_attribute_set_manual_dump_mode set manual_dump_mode

```python
user = User(id=1, any_db_data1=531, any_db_data2='string')
print(user.__dict__)
# {'id': 1}
user.db_attribute_set_manual_dump_mode()
print(user.__dict__)
# {'id': 1, '_any_db_data1': 531, '_any_db_data2': 'string'}
```
or set dump mod for individual attributes

```python
user = User(id=1, any_db_data1=531, any_db_data2='string')
print(user.__dict__)
# {'id': 1}
user.db_attribute_set_manual_dump_mode({'any_db_data1'})
print(user.__dict__)
# {'id': 1, '_any_db_data1': 531}
```

```python
user = User(id=1, list_of_books=[])
user.db_attribute_set_manual_dump_mode()
for i in range(10 ** 5):
    user.list_of_books.append(i)
user.db_attribute_set_auto_dump_mode()
```

if you need dump attributes to db with manual_dump_mode, you can use DbAttribute.db_attribute_dump

```python
user = User(id=1, list_of_books=[])
user.db_attribute_set_manual_dump_mode()
for i in range(10 ** 4):
    user.list_of_books.append(i)
user.db_attribute_dump()  # dump the list_of_books to db
for i in range(10 ** 4):
    user.list_of_books.append(i)
user.db_attribute_set_auto_dump_mode()
```

## Types

### Db attribute

you can set the Db attribute class as data type for another Db attribute class

```python
from db_attribute.db_types import DbAttributeType

*decorators*
class Class_A(DbAttribute):
    obj_b: DbAttributeType('Class_B')

*decorators*
class Class_B(DbAttribute):
    obj_a: Class_A
```
for create obj:
```python
obj = Class_A(id=15, name='Anna', obj_b=1)
obj = Class_B(id=1, name='Bob', obj_a=15)
print(obj.obj_a.name) #Anna
#or
obj = Class_A(id=15, name='Anna', obj_b=obj)
print(obj.obj_b.name) #Bob
```
for found obj:
```python
obj = Class_B(id=1, name='Bob')
obj = Class_A(obj_a=obj)
print(obj.name) #Anna
obj = Class_A(obj_a=1)
print(obj.name) #Anna
```

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
from db_attribute.db_types import JsonType

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

The execution speed may vary from computer to computer, so you need to focus on the specified number of operations per second of a regular mysql

* mysql `select` - 12500 op/sec
* mysql `insert/update` - 4500 op/sec<br>

## Get attr

mysql `select` - 12500 op/sec

Type      | Operation/seconds | How much slower is it
----------|-------------------|---------------------------
int       | 11658 op/sec      | -6%
str       | 11971 op/sec      | -4%
tuple     | 9685 op/sec       | -22%
list      | 9630 op/sec       | -23%
dict      | 9545 op/sec       | -23%
JsonType  | 11937 op/sec      | -4%

## Set attr

other name: update attr<br>
mysql `insert/update` - 4500 op/sec<br>

Type      | Operation/seconds | How much slower is it
----------|-------------------|---------------------------
int       | 4221 op/sec       | -6%
str       | 4341 op/sec       | -3%
tuple     | 3678 op/sec       | -18%
list      | 3571 op/sec       | -20%
dict      | 3506 op/sec       | -22%
JsonType  | 4165 op/sec       | -7%

# Data base

this module used mysql db, and for use it, you need install <a href='https://www.mysql.com'>mysql</a>

