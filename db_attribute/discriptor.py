import db_attribute.db_types as db_types
import db_attribute.db_class as db_class
import db_attribute.db_work as db_work
import db_attribute.connector as connector
import db_attribute

class ConditionCore:
    def __gt__(self, other):
        return Condition(self.cls, self, other, '>')
    def __ge__(self, other):
        return Condition(self.cls, self, other, '>=')
    def __lt__(self, other):
        return Condition(self.cls, self, other, '<')
    def __le__(self, other):
        return Condition(self.cls, self, other, '<=')
    def __eq__(self, other):
        return Condition(self.cls, self, other, '=')
    def __ne__(self, other):
        return Condition(self.cls, self, other, '!=')
    #def _like(self, other):
    #    return Condition(self.cls, self, other, 'Like')
    def __add__(self, other):
        return Condition(self.cls, self, other, '+', lambda a, b: a + b)
    def __mul__(self, other):
        return Condition(self.cls, self, other, '*', lambda a, b: a * b)
    def __sub__(self, other):
        return Condition(self.cls, self, other, '-', lambda a, b: a - b)
    def __truediv__(self, other):
        return Condition(self.cls, self, other, '/', lambda a, b: a / b)
    def __mod__(self, other):
        return Condition(self.cls, self, other, '%', lambda a, b: a % b)
    def __lshift__(self, other):
        return Condition(self.cls, self, other, '<<', lambda a, b: a << b)
    def __rshift__(self, other):
        return Condition(self.cls, self, other, '>>', lambda a, b: a >> b)
    def __and__(self, other):
        return Condition(self.cls, self, other, 'and', lambda a, b: a & b)
    def __or__(self, other):
        return Condition(self.cls, self, other, 'or', lambda a, b: a | b)
    def __xor__(self, other):
        return Condition(self.cls, self, other, '^', lambda a, b: a ^ b)


class AttributeObj(ConditionCore):
    def __init__(self, cls, attr):
        self.cls = cls
        self.attr = attr

    def _get_condition_repr(self):
        field = self.cls.__db_fields__[self.attr]
        default = field.get_default()
        python_type = field.python_type
        table_name = db_work.get_table_name(self.cls.__name__, self.attr)
        sql_name = self.cls.__dbworkobj__.connobj.sql_name
        scr_table_name = db_work.screening(table_name, sql_name)
        scr_data = db_work.screening('data', sql_name)
        if default is db_types.NotSet or default is db_types.MISSING:
            return f'{scr_table_name}.{scr_data}'
        temp = db_work.convert_attribute_value_to_mysql_value(default, python_type)
        if temp['status_code'] != 200:
            raise Exception(connector.status_cod[temp['status_code']])
        sql_default = temp["data"]
        return f'COALESCE({scr_table_name}.{scr_data}, {sql_default})'

    def __repr__(self):
        return f'{self.cls.__name__}.{self.attr}'


class Condition(ConditionCore):
    def __init__(self, cls, left, right, operator:str, lambda_operator=None):
        self.cls = cls
        self.left = left
        self.right = right
        self.operator = operator
        if lambda_operator:
            self.lambda_operator = lambda_operator

    def found(self):
        temp = self.cls.__dbworkobj__.found_ids_by_condition(class_name=self.cls.__name__, condition=self._get_condition_repr())
        if temp['status_code'] != 200:
            return db_types.Ids()
        return db_types.Ids(temp['data'])

    def get_value(self, ID):
        left = self.left.get_value(ID) if isinstance(self.left, ConditionCore) else self.left
        right = self.right.get_value(ID) if isinstance(self.right, ConditionCore) else self.right
        return self.lambda_operator(left, right)

    def _get_condition_repr(self):
        temp = db_work.convert_attribute_value_to_mysql_value(self.left, type(self.left))
        left = temp['data']
        temp = db_work.convert_attribute_value_to_mysql_value(self.right, type(self.right))
        right = temp['data']
        return f'({left} {self.operator} {right})'

    def __repr__(self):
        return f'({self.left} {self.operator} {self.right})'


class DbAttributeDiscriptor:
    def __init__(self, owner=None, name:str=None):
        self.public_name = name
        self.private_name = name if name is None else '_' + name
        self.cls = owner
        self.field = None if self.cls is None else self.cls.__db_fields__[name]

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = '_' + name
        self.cls = owner
        self.field = self.cls.__db_fields__[name]

    def __get__(self, this, objtype=None):
        if this is None:
            return AttributeObj(self.cls, self.public_name)
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

    def __delete__(self, this):
        if self.private_name in object.__getattribute__(this, '__dict__'):
            object.__delattr__(this, self.private_name)
        self.del_attr_from_db(this)

    def __repr__(self):
        return f'{self.cls}.{self.public_name}'

    def get_default_value(self):
        if self.field is db_types.NotSet or (self.field.default is db_types.MISSING and self.field.default_factory is db_types.MISSING): return db_types.NotSet
        return self.field.get_default()

    def dump_attr_to_db(self, this, value, cheak_exists_value=True, update_value=False):
        attribute_type = self.cls.__db_fields__[self.public_name].python_type
        obj = db_class.cheaker.create_db_class(value, attribute_type=attribute_type, _obj_dbattribute=this)
        if db_work.get_table_name(self.cls.__name__, self.public_name) not in self.cls.__dbworkobj__.tables:
            self.cls.__dbworkobj__.create_attribute_table(class_name=self.cls.__name__, attribute_name=self.public_name, attribute_type=attribute_type)
            cheak_exists_value = False
        ID = object.__getattribute__(this, 'id')
        self.cls.__dbworkobj__.add_attribute_value(class_name=self.cls.__name__, attribute_name=self.public_name, ID=ID, data=obj, attribute_type=attribute_type)

    def get_attr_from_db(self, this):
        ID = object.__getattribute__(this, 'id')
        temp_data = object.__getattribute__(self.cls, '__dbworkobj__').get_attribute_value(class_name=self.cls.__name__, attribute_name=self.public_name, ID=ID, _obj_dbattribute=this)
        if temp_data['status_code'] == 302: #table is not create
            object.__getattribute__(self.cls, '__dbworkobj__').create_attribute_table(class_name=self.cls.__name__, attribute_name=self.public_name, _cls_dbattribute=self.cls)
            temp_data['status_code'] = 304
        if temp_data['status_code'] == 304: #attr is not found
            value = self.get_default_value()
            if value is db_types.NotSet:
                raise Exception(connector.status_cod[305]['eng'])
            self.__set__(this, value)
            return value
        if temp_data['status_code'] != 200:
            return None
        return temp_data['data']

    def dump_attr(self, this, cheak_exists=True):
        if cheak_exists and (not hasattr(this, self.private_name)):
            return
        self.dump_attr_to_db(this, getattr(this, self.private_name))

    def del_attr_from_db(self, this):
        ID = object.__getattribute__(this, 'id')
        return object.__getattribute__(self.cls, '__dbworkobj__').del_attribute_value(class_name=self.cls.__name__, attribute_name=self.public_name, ID=ID)

    def container_update(self, this, data=None):
        ID = object.__getattribute__(this, 'id')
        self.cls.__dbworkobj__.add_attribute_value(class_name=self.cls.__name__, attribute_name=self.public_name, ID=ID, data=data, _cls_dbattribute=self.cls)
