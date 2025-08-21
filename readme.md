DbAttribute - Database Attribute
=========================

DbAttribute is an ORM library designed to simplify database interactions. Core capabilities:

* Automatic state synchronization
Object attribute changes are automatically tracked and persisted to the database without requiring explicit commit calls.
<br><br>
* Direct object manipulation
Supports both value assignment (obj.attr = value) and in-place modification of container types:

```python
obj.books.append("New Book")
obj.settings["theme"] = "dark"
```

* Expressive query syntax
Filtering uses Python operators with natural syntax:

```python
# Find users older than 18 named John
User.get((User.age > 18) & (User.name == "John"))

# Get all users named Bob
[user for user in User if user.name == "Bob"]
```
The library provides tools for declarative model definition, relationship management, and database operation optimization through configurable synchronization modes.

# Table of contents

* [Table of contents](#table-of-contents)
* [Supported types](#supported-types)
* [Install](#install)
* [How to use it](#how-to-use-it)
    * [Create class](#create-class)
        * [Options](#options)
    * [Work with obj](#work-with-obj)
        * [Create new object](#create-new-object)
        * [Finding objects](#finding-objects)
        * [Iterations](#iterations)
        * [Change attribute of obj](#change-attribute-of-obj)
        * [Dump mode](#dump-mode)
    * [Types](#types)
        * [Db attribute](#db-attribute)
        * [Db classes](#db-classes)
        * [Custom Db Classes](#custom-db-classes) 
        * [Json type](#json-type)
* [Speed Test](#speed-test)
    * [Get attr](#get-attr)
    * [Set attr](#set-attr)
* [Data base](#data-base)

# Supported types

This module supports standard types: `int`, `float`, `str`, `bool`, `None`, `tuple`, `list`, `set`, `dict`, `datetime`.

If a developer needs other data types, they will need to write an adapter class.

# Install

The package can be obtained from PyPI and installed in a single step:

```
pip install db_attribute
```

It can also be obtained from source (requires git):

```
pip install git+https://github.com/shutkanos/Db-Attribute.git
```

# How to use it

## Create class

To create any class (Table):

* Set metaclass `DbAttributeMetaclass`
* Inheritance the `DbAttribute` (optional, since it inherits automatically when using a metaclass)
* Set dbworkobj for connect to database
* Define fields using annotations or DbField for database columns

```python
from db_attribute import DbAttribute, DbAttributeMetaclass, db_work, connector
from db_attribute.db_types import DbField

connect_obj = connector.Connection(host=*mysqlhost*, user=*user*, password=*password*, database=*databasename*)
db_work_obj = db_work.Db_work(connect_obj)

class User(DbAttribute, metaclass=DbAttributeMetaclass, __dbworkobj__=db_work_obj):
    name: str = DbField(default='NotSet') # Ok
    age: int = -1 # Ok
    ban = DbField(default=False) # Ok
    other_int_information = 100 # Need annotation or DbField - not error, but not saved
    list_of_books = DbField(default_factory=lambda: ['name of first book']) # Ok
    settings: dict = DbField(default_factory=dict) # Ok
```

Each instance has a unique `id` identifier. It is inherited from DbAttribute and stored in `__dict__`

### Options

Options can be set in different ways:

```python
class User(DbAttribute, metaclass=DbAttributeMetaclass, __dbworkobj__ = db_work_obj):
    pass
```
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
class Class_A(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
class Class_B(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
```

All options:

* `__dbworkobj__` - database work object (required parameter),
* `__max_repr_recursion_limit__` - maximum recursion limit for `__repr__` of DbAttribute
* `__repr_class_name__` - sets the name of this class when using the method `__repr__` of DbAttribute

## Work with obj

### Create new object

To create an object, use an id (optional) and other fields (optional),

```python
obj = User(id=3) # other field set to defaults value
print(obj) # User(id=3, name=*default value*)
```
```python
obj = User(name='Ben', id=3)
print(obj) # User(id=3, name='Ben')
```
```python
obj = User(name='Alica')
print(obj) # User(id=4, name='Alica')
obj = User(name='Alica')
print(obj) # User(id=5, name='Alica')
```

If a developer needs to recreate an object, he can call DbAttribute cls with id.

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

### Finding objects

If a developer needs to find an object, they can use the 'get' method.

The `get()` method returns:
- Single object if found
- Object with smallest ID if multiple matches exist
- `None` if no matches found

```python
#create objs
obj = User(name='Bob', age=2, id=1)
obj = User(name='Bob', age=3, id=2)
obj = User(name='Anna', age=2, id=3)
#finds objs
print(User.get((User.age == 3) & (User.name == 'Bob'))) #User(id=2, name='Bob', age=3)
print(User.get(User.name == 'Anna'))                    #User(id=3, name='Anna', age=2)
print(User.get(User.name == 'Bob'))                     #User(id=1, name='Bob', age=2)
print(User.get(User.name == 'Other name'))              #None
```

To check the correctness of writing a logical expression, you can:

```python
print(User.name == 'Anna')                      #(User.name = 'Anna')
print((User.age == 3) & (User.name == 'Bob'))   #((User.age = 3) and (User.name = 'Bob'))
```

Use '&' and '|' instead of the 'and' and 'or' operators. The 'and' and 'or' operators are not supported

### Iterations

If a developer needs to iterate through all the elements of a class, they can use standard Python tools.

```python
print(list(User))
#[User(id=1, name='Bob', age=3), User(id=2, name='Bob', age=2), User(id=3, name='Anna', age=2)]

print([i for i in User if i.age < 3])
#[User(id=2, name='Bob', age=2), User(id=3, name='Anna', age=2)]

for i in User:
    print(i)
#User(id=1, name='Bob', age=3)
#User(id=2, name='Bob', age=2)
#User(id=3, name='Anna', age=2)
```
⚠️ Iterations loads all objects - not recommended for large tables

### Change attribute of obj

```python
obj = User(name='Bob', list_of_books=[], id=1)

print(obj) #User(id=1, name='Bob', list_of_books=[])

obj.name = 'Anna'
obj.list_of_books.append('Any name of book')

print(obj) #User(id=1, name='Anna', list_of_books=['Any name of book'])
```

### Dump mode

If in any function you will work with obj, you can activate manual_dump_mode (auto_dump_mode is the default),

* `auto_dump_mode`: attributes don't save in self.__dict__, all changes automatic dump in db.
* `manual_dump_mode`: attributes save in self.__dict__, and won't dump in db until self.db_attribute_set_dump_mode is called. this helps to quickly perform operations on containers db attributes

DbAttribute.set_auto_dump_mode set auto_dump_mode and call dump

DbAttribute.set_manual_dump_mode set manual_dump_mode

```python
user = User(id=1, any_db_data1=531, any_db_data2='string')
print(user.__dict__)
# {'id': 1}
user.set_manual_dump_mode()
print(user.__dict__)
# {'id': 1, '_any_db_data1': 531, '_any_db_data2': 'string'}
```
Or set dump mode for individual attributes

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
If a developer needs to dump attributes to db with manual_dump_mode, you can use DbAttribute.db_attribute_dump

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

A developer can set the Db attribute class as data type for another Db attribute class

```python
from db_attribute.db_types import TableType

class Class_A(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
    obj_b: TableType('Class_B')

class Class_B(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
    obj_a: Class_A
```
To create an object:
```python
obj_a = Class_A(id=15, name='Anna', obj_b=1)
obj_b = Class_B(id=1, name='Bob', obj_a=15)
print(obj_b) #Class_B(id=1, name='Bob', obj_a=Class_A(id=15, name='Anna', obj_b=Class_B(id=1, ...)))
#or
obj_a = Class_A(id=15, name='Anna', obj_b=obj_b)
print(obj_a) #Class_A(id=15, name='Anna', obj_b=Class_B(id=1, name='Bob', obj_a=Class_A(id=15, ...)))
```
For found obj:
```python
Class_A(id=15, name='Anna', obj_b=1)
obj = Class_B(id=1, name='Bob', obj_a=15)
obj = Class_A.get(Class_A.obj_b == obj)
print(obj) #Class_A(id=15, name='Anna', obj_b=Class_B(id=1, name='Bob', obj_a=Class_A(id=15, ...)))
#And Found with use id of obj:
obj = Class_A.get(Class_A.obj_b == 1)
print(obj) #Class_A(id=15, name='Anna', obj_b=Class_B(id=1, name='Bob', obj_a=Class_A(id=15, ...)))
```
One-to-Many relationship:
```python
from db_attribute.db_types import DbField

class Author(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
    name: str = ""
    books: list = DbField(default_factory=list)

class Book(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
    title: str = ""
    author: Author

author = Author(name="George Orwell")
book = Book(title="1984", author=author)
author.books.append(book)

print(author) #Author(id=1, name='George Orwell', books=[Book(id=1, title='1984', author=Author(id=1, ...))])
print(book) #Book(id=1, title='1984', author=Author(id=1, name='George Orwell', books=[Book(id=1, ...)]))
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

### Custom Db Classes

And to create a custom 'Db class', you need to
* Create regular class
* Inherit from DbClass (DbClass - first. It is important) and your regular class for custom Db class
* Set a Decorator with or without the necessary parameters
* Set at least the `__convert_to_db__` module, according to the documentation
* add additional modules.

```python
from db_attribute import db_class

# for exemple you have your class:

class UserDataClass:
    def __init__(self, value = None):
        self.value = value
    def __repr__(self):
        return f'UserDataClass(value={self.value})'

@db_class.DbClassDecorator
class DbUserDataClass(db_class.DbClass, UserDataClass):
    def __init__(self, value=None, **kwargs):
        # This is not a mandatory method
        super().__init__(_call_init=False, **kwargs) # But this call is mandatory
        self.__dict__['value'] = value
        # Here we set the value of a variable using __dict__.
        # This is not necessary, but it speeds up the work with the class.

    @classmethod
    def __convert_to_db__(cls, obj: UserDataClass, **kwargs):
        """Methode for convert obj to dbclass - need @classmethod and kwargs"""
        # This is a mandatory method
        # Call with _user_db=True
        # Example:
        # print(type(DbUserDataClass(value=10)))                #UserDataClass
        # print(type(DbUserDataClass(value=10, _use_db=True)))  #DbUserDataClass
        return cls(_use_db=True, value=obj.value, **kwargs)

    def __convert_from_db__(self):
        """Reverse convert"""
        # This is not a mandatory method.
        return self._standart_class(value=self.value)
```

For example:

```python
class User(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
    data: UserDataClass

user = User(id=1, data=UserDataClass(10))
print(user.data) # UserDataClass(value=10)
user.data.value = 5
print(user.data) # UserDataClass(value=5)
```

### Json type

DbAttribute supports `tuple`, `list`, `dict`, other collections, but these types are slow, because uses Db classes (see [speed test](#speed-test)).

To solve this problem, use a Json convertation

```python
from db_attribute.db_types import JsonType, DbField

class User(DbAttribute, metaclass=DbAttributeMetaclass):
    Meta = BaseMeta
    settings: JsonType = DbField(default_factory=lambda: {})

obj = User(1, settings={1: 2, 3: [4, 5]})
print(obj.settings)  # {'1': 2, '3': [4, 5]}
print(type(obj.settings))  # dict
```

* If Developer change obj with JsonType, this obj don't dump to db, you need set the new obj 
* JsonType only supports: `dict`, `list`, `str`, `int`, `float`, `bool`, `None`

```python
obj = User(1, settings={1: 2, 3: [4, 5]})
del obj.settings['3'] # not changed
obj.settings['1'] = 3 # not changed
obj.settings |= {4: 5} # not changed
print(obj.settings) #{'1': 2, '3': [4, 5]}
obj.settings = {1: 3} # changed
print(obj.settings) #{'1': 3}
```

# Speed Test

The execution speed may vary from computer to computer, so you need to focus on the specified number of operations per second of a regular mysql

* mysql `select` - 12500 op/sec
* mysql `insert` - 8500 op/sec<br>

## Get attr

Mysql `select` - 12500 op/sec

Type      | Operation/seconds | Performance impact
----------|-------------------|---------------------------
int       | 11658 op/sec      | -6%
str       | 11971 op/sec      | -4%
tuple     | 9685 op/sec       | -22%
list      | 9630 op/sec       | -23%
dict      | 9545 op/sec       | -23%
JsonType  | 11937 op/sec      | -4%

## Set attr

Mysql `insert` - 8500 op/sec<br>

Type      | Operation/seconds | Performance impact
----------|-------------------|---------------------------
int       | 8056 op/sec       | -5%
str       | 8173 op/sec       | -3%
tuple     | 6284 op/sec       | -26%
list      | 6043 op/sec       | -28%
dict      | 6354 op/sec       | -25%
JsonType  | 7297 op/sec       | -14%

# Data base

This module uses MySQL db (<a href="https://github.com/mysql/mysql-connector-python/blob/trunk/LICENSE.txt">License</a>), and for use it, you need install <a href='https://www.mysql.com'>mysql</a>

