import dataclasses
from typing import ClassVar

import db_class
import db_work

@dataclasses.dataclass(kw_only=True)
class Db_Atribute:
    id: int
    _db_Atribute__list_db_atributes: ClassVar[list] = []

    def __setattr__(self, key, value):
        object.__getattribute__(self, '_db_atribute_set_attr')(key, value)

    def __getattribute__(self, item):
        return object.__getattribute__(self, '_db_atribute_get_attr')(item)

    def _db_atribute_set_attr(self, key, value):
        self_dict = object.__getattribute__(self, '__dict__') | object.__getattribute__(self, '__class__').__dict__
        if key == '_db_Atribute__list_db_atributes':
            object.__setattr__(self, key, value)
            if '_db_Atribute__deque_of_atributes' in self_dict:
                for temp_key, temp_value in self_dict['_db_Atribute__deque_of_atributes']:
                    self.__setattr__(temp_key, temp_value)
                del self_dict['_db_Atribute__deque_of_atributes']
            return
        if '_db_Atribute__list_db_atributes' not in self_dict:
            if '_db_Atribute__deque_of_atributes' not in self_dict:
                object.__setattr__(self, '_db_Atribute__deque_of_atributes', [])
            object.__getattribute__(self, '_db_Atribute__deque_of_atributes').append((key, value))
            return
        if key in self_dict['_db_Atribute__list_db_atributes']:
            obj = db_class.cheaker.create_one_db_class(value, _obj_dbatribute=self)
            #object.__setattr__(self, key, obj)
            cls_name = object.__getattribute__(self, '__class__').__name__
            if db_work.get_table_name(cls_name, key) not in db_work.db_work.active_tables:
                db_work.db_work.create_atribute_table(class_name=cls_name, atribute_name=key, atribute_type=type(obj))
            db_work.db_work.add_atribute_value(class_name=cls_name, atribute_name=key, ID=self_dict['id'], data=obj)
        else:
            object.__setattr__(self, key, value)

    def _db_atribute_get_attr(self, key):
        if key[0] == '_' or '_db_Atribute__list_db_atributes' not in (cls_dict := object.__getattribute__(self, '__class__').__dict__) or key not in cls_dict['_db_Atribute__list_db_atributes']:
            return object.__getattribute__(self, key)

        temp_data = db_work.db_work.get_atribute_value(class_name=self.__class__.__name__, atribute_name=key, ID=object.__getattribute__(self, 'id'))
        if temp_data['status_code'] != 200:
            return None
        #print(f'_db_atribute_get_attr {key} {temp_data["data"]}')
        return temp_data['data']

    def _db_atribute_container_update(self, key):
        """
        call this functions, when any container atribute is updated, to update this atribute in db
        :param key: atribute container which update
        :type key: str
        :return: None
        """
        pass

#a = Db_Atribute(id=10)

#print(a)