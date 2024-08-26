import collections, time, json, copy

import UserSet

class DbContainer:
    _standart_class=object
    _obj_dbatribute=None
    data=None

    def __new__(cls, iterable=(), *args, _use_db = False, _obj_dbatribute=None, **kwargs):
        if not _use_db:
            obj = cls._standart_class.__new__(cls._standart_class)
            if cls._standart_class == dict:
                obj.__init__(iterable, **kwargs)
            else:
                obj.__init__(iterable)
            return obj
        #print(f'__new__ {cls=} {iterable=}')
        return super().__new__(cls)

    def __copy__(self, *args, **kwargs):
        obj = self.__class__.__new__(self.__class__, iterable=self.data.copy())
        if isinstance(obj, self._standart_class):
            return obj
        obj.__dict__.update(self.__dict__)
        obj.__dict__['data'] = self.data.copy()
        return obj

    __deepcopy__ = __copy__

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'data':
            self.update_data()

    def update_data(self):
        data = object.__getattribute__(self, 'data')

    def dumps(self):
        data1 = ", ".join([i.dumps() if cheaker.this_db_atribute_container_class(i) else json.dumps(i) for i in self.data])
        data2 = {str(key): value.__class__.__name__ for key, value in enumerate(self.data) if cheaker.this_db_atribute_container_class(value)}
        return f'{"{"}"data": [{data1}], "sittings": {str(data2)}{"}"}'

    def loads(self, s: str):
        temp_data = json.loads(s)
        pass

class DbDict(DbContainer, collections.UserDict):
    _standart_class=dict

    def __init__(self, iterable=(), *args, _use_db = False, _obj_dbatribute=None, **kwargs):
        self._obj_dbatribute = _obj_dbatribute
        if isinstance(iterable, self.__class__):
            self.__dict__['data'] = copy.deepcopy(iterable.data)
        else:
            data = dict(iterable, **kwargs)
            self.__dict__['data'] = data
            for i in data:
                if cheaker.this_container_class(data[i]):
                    self.__dict__['data'][i] = cheaker.create_one_db_class(data[i], _obj_dbatribute=_obj_dbatribute)

    def __setitem__(self, key, item):
        data = super().__setitem__(key, cheaker.create_one_db_class(item, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def __delitem__(self, key):
        data = super().__delitem__(key)
        self.update_data()
        return data

    def clear(self):
        data = super().clear()
        self.update_data()
        return data

    def update(self, __m, **kwargs):
        data = super().update(__m, **kwargs)
        self.update_data()
        return data

    def pop(self, __key):
        data = super().pop(__key)
        self.update_data()
        return data

    def popitem(self):
        data = super().popitem()
        self.update_data()
        return data

    def dumps(self):
        return f''

class DbList(DbContainer, collections.UserList):
    _standart_class=list

    def __init__(self, iterable=(), *args, _use_db = False, _obj_dbatribute=None, **kwargs):
        self._obj_dbatribute = _obj_dbatribute
        if isinstance(iterable, self.__class__):
            self.__dict__['data'] = copy.deepcopy(iterable.data)
        else:
            data = list(iterable)
            self.__dict__['data'] = data
            for i in range(len(data)):
                if cheaker.this_container_class(data[i]):
                    self.__dict__['data'][i] = cheaker.create_one_db_class(data[i], _obj_dbatribute=_obj_dbatribute)

    def __setitem__(self, i, item):
        data = super().__setitem__(i, cheaker.create_one_db_class(item, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def __delitem__(self, i):
        data = super().__delitem__(i)
        self.update_data()
        return data

    def append(self, item):
        data = super().append(cheaker.create_one_db_class(item, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def insert(self, i, item):
        data = super().insert(i, cheaker.create_one_db_class(item, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def pop(self, i=-1):
        data = super().pop(i)
        self.update_data()
        return data

    def remove(self, item):
        data = super().remove(cheaker.create_one_db_class(item, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def clear(self):
        data = super().clear()
        self.update_data()
        return data

    def reverse(self):
        data = super().reverse()
        self.update_data()
        return data

    def sort(self, *args, key=None, reverse=False):
        if args:
            raise TypeError('sort() takes no positional arguments')
        data = super().sort(key=key, reverse=reverse)
        self.update_data()
        return data

    def extend(self, other):
        data = super().extend(other)
        self.update_data()
        return data

class DbSet(DbContainer, UserSet.UserSet):
    _standart_class=set

    def __init__(self, iterable=(), *args, _use_db = False, _obj_dbatribute=None, **kwargs):
        self._obj_dbatribute = _obj_dbatribute
        if isinstance(iterable, self.__class__):
            self.__dict__['data'] = copy.deepcopy(iterable.data)
        else:
            self.__dict__['data'] = set(iterable)

    def add(self, __element):
        data = super().add(cheaker.create_one_db_class(__element, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def discard(self, __element):
        data = super().discard(cheaker.create_one_db_class(__element, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def update(self, *s):
        data = super().update(*cheaker.create_db_class(*s, _obj_dbatribute=self._obj_dbatribute))
        self.update_data()
        return data

    def difference_update(self, *s):
        data = super().difference_update(*s)
        self.update_data()
        return data

    def intersection_update(self, *s):
        data = super().intersection_update(*s)
        self.update_data()
        return data

    def symmetric_difference_update(self, __s):
        data = super().symmetric_difference_update(__s)
        self.update_data()
        return data

class Cheaker:
    def __init__(self, users_db_classes:dict = None):
        """
        :param users_db_classes: example: {datetime.datetime: DbDatetime}
        :type users_db_classes: dict
        """
        self.users_db_classes = users_db_classes
        if not users_db_classes:
            self.users_db_classes = dict()

    def set_users_db_classes(self, users_db_classes: dict):
        """
        :param users_db_classes: example: {datetime.datetime: DbDatetime}
        :type users_db_classes: dict
        """
        self.users_db_classes = users_db_classes
        if not users_db_classes:
            self.users_db_classes = dict()

    def create_db_class(self, *objs, _obj_dbatribute=None):
        """
        Use for create db_class from other classes. example: from list to DbList, but from int to int.
        :param objs: example: [123, '535', {8, 4, 6} #it's set , {1: 2} # it's dict]
        :param _obj_dbatribute:
        :return: example: [123, '535', {8, 4, 6} #it's DbSet , {1: 2} # it's DbDict]
        """
        return [self.create_one_db_class(objs[i], _obj_dbatribute=_obj_dbatribute) for i in range(len(objs))]

    def create_one_db_class(self, obj, _obj_dbatribute=None):
        if isinstance(obj, dict):
            return DbDict(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute)
        if isinstance(obj, list):
            return DbList(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute)
        if isinstance(obj, set):
            return DbSet(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute)
        for from_class, to_class in self.users_db_classes.items():
            if isinstance(obj, from_class):
                return to_class(obj, _use_db=True, _obj_dbatribute=_obj_dbatribute)
        return obj

    def this_container_class(self, obj, this_is_cls=False):
        if this_is_cls:
            return obj in [dict, list, set] or obj in self.users_db_classes
        return obj.__class__ in [dict, list, set] or obj.__class__ in self.users_db_classes

    def this_db_atribute_container_class(self, obj, this_is_cls=False):
        if this_is_cls:
            return obj in [DbDict, DbList, DbSet] or obj in self.users_db_classes.values()
        return obj.__class__ in [DbDict, DbList, DbSet] or obj.__class__ in self.users_db_classes.values()

cheaker = Cheaker()

def list_to_dict(obj):
    return {i: obj[i] for i in range(len(obj))}


if __name__ == "__main__":

    print(1)
    A = DbDict([[0, 1], [1, 4], [2, 3], [3, 2], [4, 4]], _use_db = True)
    B = DbList([1, 4, 3, 2, 4], _use_db = True)
    C = DbSet([1, 4, 3, 2, 4], _use_db = True)
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4} or B != [1, 4, 3, 2, 4] or C != {1, 2, 3, 4}:
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(2)
    a = A | {8: 5}
    b = B + [1]
    c = C - {3}
    if a != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or b != [1, 4, 3, 2, 4, 1] or c != {1, 2, 4}:
        print(a, type(a))
        print(b, type(b))
        print(c, type(c))

    print(3)
    A |= {8: 5}
    B += [1]
    C -= {3}
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or B != [1, 4, 3, 2, 4, 1] or C != {1, 2, 4}:
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(4)
    A = DbDict([[0, 1], [1, 4], [2, 3], [3, 2], [4, 4]], _use_db = True)
    B = DbList([1, 4, 3, 2, 4], _use_db = True)
    C = DbSet([1, 4, 3, 2, 4], _use_db = True)
    A.update({8:5})
    B.append(1)
    C.remove(3)
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or B != [1, 4, 3, 2, 4, 1] or C != {1, 2, 4}:
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(5)
    A = DbDict([[0, 1], [1, 4], [2, 3], [3, 2], [4, 4]], _use_db = True)
    B = DbList([1, 4, 3, 2, 4], _use_db = True)
    C = DbSet([1, 4, 3, 2, 4], _use_db = True)
    a = dict(A)
    b = list(B)
    c = set(C)
    a |= {8: 5}
    b += [1]
    c -= {3}
    if A != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4} or B != [1, 4, 3, 2, 4] or C != {1, 2, 3, 4} or a != {0: 1, 1: 4, 2: 3, 3: 2, 4: 4, 8: 5} or b != [1, 4, 3, 2, 4, 1] or c != {1, 2, 4} or a == A or b == B or c == C:
        print(a, type(a))
        print(b, type(b))
        print(c, type(c))
        print(A, type(A))
        print(B, type(B))
        print(C, type(C))

    print(6)
    A = DbDict([[0, [1, 4, {1}]], [1, {2}], [2, {5:6}], [3, 4]], _use_db = True)
    B = DbList([[1], [4], [3], {2:[5]}, {1, 3, 4}], _use_db = True)
    C = DbSet([(1, 4), (3, 2), 4], _use_db = True)
    A[0][0] = 3
    del A[0][1]
    A[0][1].add(2)
    print(A, type(A))
    print(B, type(B))
    print(C, type(C))

    #A = DbList([(1, 4), 2, 3, {4, 5, 6}], _use_db=True)
    #print(A.dumps(), type(A.dumps()))


