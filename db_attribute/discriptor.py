from dataclasses import MISSING

import db_attribute.db_types as db_types
import db_attribute.db_class as db_class
import db_attribute.db_work as db_work

class Comparison:
    def __init__(self, cls, attr):
        self.cls = cls
        self.attr = attr

    def _found(self, data, operator):
        temp = self.cls._db_attribute__dbworkobj.found_ids_by_value(class_name=self.cls.__name__, attribute_name=self.attr, data=data, _cls_dbattribute=self.cls, operator=operator)
        if temp['status_code'] != 200: return set()
        return temp['data']

    def __gt__(self, other):
        return self._found(other, '>')
    def __ge__(self, other):
        return self._found(other, '>=')
    def __lt__(self, other):
        return self._found(other, '<')
    def __le__(self, other):
        return self._found(other, '<=')
    def __eq__(self, other):
        return self._found(other, '=')
    def __ne__(self, other):
        return self._found(other, '!=')
    def _like(self, other):
        return self._found(other, 'Like')
    def __repr__(self):
        return f'{self.cls.__name__}.{self.attr}'

class DbAttributeDiscriptor:
    def __init__(self, owner=None, name:str=None):
        self.public_name = name
        self.private_name = name if name is None else '_' + name
        self.cls = owner
        self.field = None if self.cls is None else self.cls.__dataclass_fields__[name]

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = '_' + name
        self.cls = owner
        self.field = self.cls.__dataclass_fields__[name]

    def __get__(self, this, objtype=None):
        if this is None:
            return Comparison(self.cls, self.public_name)
        if self.private_name in object.__getattribute__(this, '__dict__'):
            return object.__getattribute__(this, self.private_name)
        return self.get_attr_from_db(this)

    def __set__(self, this, value):
        if value is db_types.NotSet:
            return
        if self.private_name in object.__getattribute__(this, '__dict__'):
            object.__setattr__(this, self.private_name, value)
            return
        self.dump_attr_to_db(this, value)

    def get_default_value(self):
        if self.field is db_types.NotSet or (self.field.default is MISSING and self.field.default_factory is MISSING): return db_types.NotSet
        if self.field.default is not MISSING: return self.field.default
        return self.field.default_factory()

    def dump_attr_to_db(self, this, value, cheak_exists_value=True, update_value=False):
        attribute_type = self.cls.__annotations__[self.public_name]
        obj = db_class.cheaker.create_db_class(value, attribute_type=attribute_type, _obj_dbattribute=this)
        if db_work.get_table_name(self.cls.__name__, self.public_name) not in self.cls._db_attribute__dbworkobj.active_tables:
            self.cls._db_attribute__dbworkobj.create_attribute_table(class_name=self.cls.__name__, attribute_name=self.public_name, attribute_type=attribute_type)
            cheak_exists_value = False
        ID = object.__getattribute__(this, 'id')
        self.cls._db_attribute__dbworkobj.add_attribute_value(class_name=self.cls.__name__, attribute_name=self.public_name, ID=ID, data=obj, attribute_type=attribute_type)

    def get_attr_from_db(self, this):
        ID = object.__getattribute__(this, 'id')
        temp_data = object.__getattribute__(self.cls, '_db_attribute__dbworkobj').get_attribute_value(class_name=self.cls.__name__, attribute_name=self.public_name, ID=ID, _obj_dbattribute=this)
        if temp_data['status_code'] == 302: #table is not create
            object.__getattribute__(self.cls, '_db_attribute__dbworkobj').create_attribute_table(class_name=self.cls.__name__, attribute_name=self.public_name, _cls_dbattribute=self.cls)
            temp_data['status_code'] = 304
        if temp_data['status_code'] == 304: #attr is not found
            value = self.get_default_value()
            self.__set__(this, value)
            return value
        if temp_data['status_code'] != 200:
            return None
        return temp_data['data']

    def dump_attr(self, this, cheak_exists=True):
        if cheak_exists and (not hasattr(this, self.private_name)):
            return
        self.dump_attr_to_db(this, getattr(this, self.private_name))

    def container_update(self, this, data=None):
        ID = object.__getattribute__(this, 'id')
        self.cls._db_attribute__dbworkobj.add_attribute_value(class_name=self.cls.__name__, attribute_name=self.public_name, ID=ID, data=data, _cls_dbattribute=self.cls)


