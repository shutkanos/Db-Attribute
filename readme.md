DbAttribute - Database Attribute
=========================

This module allows you to save attributes of objects not in RAM, but in a database. the closest analogue is <a href='https://github.com/sqlalchemy/sqlalchemy'>SQLAlchemy</a>. Unlike SQLAlchemy, this module maximizes automatism, allowing the developer to focus on other details without worrying about working with the database.

* [Supported types](#supported-types)
* [Install](#install)
* [How it used](#how-it-used)
    * [Create class](#create-class)
        * [Options](#options)
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

If developer needs other data types, he will need to write an adapter class.

# Install

Installation from source (requires git):

```
$ pip install git+https://github.com/shutkanos/Db-Attribute.git
```

# How it used

## Create class

For create any classes (Tables):

* Set metaclass `DbAttributeMetaclass`
* Inheritance the `DbAttribute` (optional, since it inherits automatically when using a metaclass)
* Set dbworkobj for connect to database
* Create any fields / Annotations / DbFields for database

```python
from db_attribute import DbAttribute, DbAttributeMetaclass, db_work, connector
from db_attribute.db_types import DbField

connect_obj = connector.Connection(host=*mysqlhost*, user=*user*, password=*password*, database=*databasename*)
db_work_obj = db_work.Db_work(connect_obj)

class User(DbAttribute, metaclass=DbAttributeMetaclass, __dbworkobj__=db_work_obj):
    name: str = DbField(default='NotSet') # Ok
    age: int = -1 # Ok
    ban = DbField(default=False) # Ok
    other_int_information = 100 # Need annotation or DbField
    list_of_books = DbField(default_factory=lambda: ['name of first book']) # Ok
    sittings: dict = DbField(default_factory=lambda: {}) # Ok
```

Each class object has its own `id`. It is inherited from DbAttribute and stored in __dict__

### Options

Options can be set in different ways:

```python
class User(DbAttribute, metaclass=DbAttributeMetaclass):
    __dbworkobj__ = db_work_obj
```
```python
class User(DbAttribute, metaclass=DbAttributeMetaclass):
    class Meta:
        __dbworkobj__ = db_work_obj
```
```python
class BaseMeta:
    __dbworkobj__ = dbworkobj
class User(DbAttribute, metaclass=DbAttributeMetaclass):
    class Meta(BaseMeta):
        pass
```

All options:

* `__dbworkobj__` - database work object,
* `__max_repr_recursion_limit__` - maximum recursion limit for `__repr__` of DbAttribute

## Work with obj

### Create new obj / add obj do db

For create obj use id and other fields,

```python
obj = User(id=3) # other field set to defaults value
print(obj) # User(id=3, name=*default value*)
```
```python
obj = User(name='Ben', id=3)
print(obj) # User(id=3, name='Ben')
```

### Found obj by id
If Developer need recreated obj, he can call DbAttribute cls with id.

```python
obj = User(name='Ben', age=10, id=3) #insert obj to db
print(obj) #User(id=3, name='Ben', age=10)

obj = User(id=3)
print(obj) #User(id=3, name='Ben', age=10)

obj = User('Anna', id=3)
print(obj) #User(id=3, name='Anna', age=10)

obj = User(age=15, id=3)
print(obj) #User(id=3, name='Anna', age=15)

obj = User(id=3)
print(obj) #User(id=3, name='Anna', age=15)
```

### Found obj by other attributes

```python
#create objs
obj = User(name='Bob', age=3, id=1)
obj = User(name='Bob', age=2, id=2)
obj = User(name='Anna', age=2, id=3)
#finds objs
print(User.get(User.name == 'Bob' and User.age == 3).id) #1
print(User.get(User.name == 'Anna').id) #3
print(User.get(User.name == 'Bob').id) #error, a lot of obj found
print(User.get(User.name == 'Other name').id) #error, no obj found
```

### Change attribute of obj

```python
obj = User(name='Bob', list_of_books=[], id=1)

print(obj) #User(id=1, name='Bob', list_of_books=[])

obj.name = 'Anna'
obj.list_of_books.append('Any name of book')

print(obj) #User(id=1, name='Anna', list_of_books=['Any name of book'])
print(obj.list_of_books[0]) #Any name of book
print(obj.name) #Anna
```

### Dump mode

If in any function you will work with obj, you can activate manual_dump_mode (auto_dump_mode is default),

* `auto_dump_mode`: attributes don't save in self.__dict__, all changes automatic dump in db.
* `manual_dump_mode`: attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_dump_mode is called. this helps to quickly perform operations on containers db attributes

DbAttribute.db_attribute_set_auto_dump_mode set auto_dump_mode and call dump

DbAttribute.db_attribute_set_manual_dump_mode set manual_dump_mode

```python
user = User(id=1, any_db_data1=531, any_db_data2='string')
print(user.__dict__)
# {'id': 1}
user.set_manual_dump_mode()
print(user.__dict__)
# {'id': 1, '_any_db_data1': 531, '_any_db_data2': 'string'}
```
Or set dump mod for individual attributes

```python
user = User(id=1, any_db_data1=531, any_db_data2='string')
print(user.__dict__)
# {'id': 1}
user.set_manual_dump_mode({'any_db_data1'})
print(user.__dict__)
# {'id': 1, '_any_db_data1': 531}
```

```python
user = User(id=1, list_of_books=[])
user.set_manual_dump_mode()
for i in range(10 ** 5):
    user.list_of_books.append(i)
user.set_auto_dump_mode()
```
If Developer need dump attributes to db with manual_dump_mode, you can use DbAttribute.db_attribute_dump

```python
user = User(id=1, list_of_books=[])
user.set_manual_dump_mode()
for i in range(10 ** 4):
    user.list_of_books.append(i)
user.dump()  # dump the list_of_books to db
for i in range(10 ** 4):
    user.list_of_books.append(i)
user.set_auto_dump_mode()
```

## Types

### Db attribute

Developer can set the Db attribute class as data type for another Db attribute class

```python
from db_attribute.db_types import TableType

class Class_A(DbAttribute, metaclass=DbAttributeMetaclass, __dbworkobj__=db_work_obj):
    obj_b: TableType('Class_B')

class Class_B(DbAttribute, metaclass=DbAttributeMetaclass, __dbworkobj__=db_work_obj):
    obj_a: Class_A
```
For create obj:
```python
obj_a = Class_A(id=15, name='Anna', obj_b=1)
obj_b = Class_B(id=1, name='Bob', obj_a=15)
print(obj_b.obj_a.name) #Anna
#or
obj_a = Class_A(id=15, name='Anna', obj_b=obj_b)
print(obj_a.obj_b.name) #Bob
```
For found obj:
```python
obj = Class_B(id=1, name='Bob')
obj = Class_A.get(Class_A.obj_a==obj)
print(obj.name) #Anna
obj = Class_A.get(Class_A.obj_a==1)
print(obj.name) #Anna
```

### Db classes
When collections are stored in memory, they converted to Db classes
```python
obj = User(1, list_of_books=[1, 2, 3])
print(type(obj.list_of_books)) #DbList
```
```python
obj = User(1, times=[datetime(2024, 1, 1)])
print(type(obj.times[0])) #DbDatetime
```
And when collections dumped to db, they converted to json
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

Db attribute support `tuple`, `list`, `dict`, other collections, but this types slow, because uses Db classes (see [speed test](#speed-test)).

To solve this problem, use a Json convertation

```python
from db_attribute.db_types import JsonType, DbField

class User(DbAttribute, metaclass=DbAttributeMetaclass, __dbworkobj__=db_work_obj):
    sittings: JsonType = DbField(default_factory=lambda: {})

obj = User(1, sittings={1: 2, 3: [4, 5]})
print(obj.sittings)  # {'1': 2, '3': [4, 5]}
print(type(obj.sittings))  # dict
```

* If Developer change obj with JsonType, this obj don't dump to db, you need set the new obj 
* The json support only `dict`, `list`, `str`, `int`, `float`, `True`, `False`, `None`

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
* mysql `insert` - 8500 op/sec<br>

## Get attr

Mysql `select` - 12500 op/sec

Type      | Operation/seconds | How much slower is it
----------|-------------------|---------------------------
int       | 11658 op/sec      | -6%
str       | 11971 op/sec      | -4%
tuple     | 9685 op/sec       | -22%
list      | 9630 op/sec       | -23%
dict      | 9545 op/sec       | -23%
JsonType  | 11937 op/sec      | -4%

## Set attr

Mysql `insert` - 8500 op/sec<br>

Type      | Operation/seconds | How much slower is it
----------|-------------------|---------------------------
int       | 8056 op/sec       | -5%
str       | 8173 op/sec       | -3%
tuple     | 6284 op/sec       | -26%
list      | 6043 op/sec       | -28%
dict      | 6354 op/sec       | -25%
JsonType  | 7297 op/sec       | -14%

# Data base

this module used mysql db (<a href="https://github.com/mysql/mysql-connector-python/blob/trunk/LICENSE.txt">Licanse</a>), and for use it, you need install <a href='https://www.mysql.com'>mysql</a>

