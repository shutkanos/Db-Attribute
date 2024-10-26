from typing import TypeVar
from collections.abc import MutableSet
from collections import deque

TypeUserSet = TypeVar('TypeUserSet', bound='UserSet')

class UserSet(MutableSet):
    def __init__(self, iterable=None):
        if iterable:
            if isinstance(iterable, UserSet):
                self.data = iterable.data.copy()
            else:
                self.data = set(iterable)
        else:
            self.data = set()

    def __contains__(self, __o, /):
        return self.data.__contains__(__o)

    def __iter__(self):
        return self.data.__iter__()

    def __len__(self):
        return self.data.__len__()

    def __repr__(self):
        return self.data.__repr__()

    def __sub__(self, __value, /):
        if isinstance(__value, UserSet):
            return self.__class__(self.data.__sub__(__value.data))
        return self.__class__(self.data.__sub__(__value))

    def __rsub__(self, __value, /):
        if isinstance(__value, UserSet):
            return self.__class__(__value.data.__sub__(self.data))
        return self.__class__(__value.__sub__(self.data))

    def __isub__(self, __value, /):
        if isinstance(__value, UserSet):
            self.data.__isub__(__value.data)
            return self
        self.data.__isub__(__value)
        return self

    def __or__(self, __value, /):
        if isinstance(__value, UserSet):
            return self.__class__(self.data.__or__(__value.data))
        return self.__class__(self.data.__or__(__value))

    __ror__ = __or__

    def __ior__(self, __value, /):
        if isinstance(__value, UserSet):
            self.data.__ior__(__value.data)
            return self
        self.data.__ior__(__value)
        return self

    def __copy__(self) -> TypeUserSet:
        return self.__class__(self.data)

    def add(self, __element, /):
        self.data.add(__element)

    def discard(self, __element, /):
        self.data.discard(__element)

    def update(self, *s):
        self.data.update(*s)

    def difference_update(self, *s):
        self.data.difference_update(*s)

    def intersection_update(self, *s):
        self.data.intersection_update(*s)

    def symmetric_difference_update(self, __s):
        self.data.symmetric_difference_update(__s)

    def isdisjoint(self, __s) -> bool:
        return self.data.isdisjoint(__s)

    def issubset(self, __s) -> bool:
        return self.data.issubset(__s)

    def issuperset(self, __s) -> bool:
        return self.data.issuperset(__s)

    def copy(self) -> TypeUserSet:
        return self.__class__(self.data.copy())

    def union(self, *s) -> TypeUserSet:
        return self.__class__(self.data.union(*s))

    def difference(self, *s) -> TypeUserSet:
        return self.__class__(self.data.difference(*s))

    def intersection(self, *s) -> TypeUserSet:
        return self.__class__(self.data.intersection(*s))

    def symmetric_difference(self, __s, /) -> TypeUserSet:
        return self.__class__(self.data.symmetric_difference(__s))

TypeUserTyple = TypeVar('TypeUserTyple', bound='UserTyple')

class UserTuple:
    def __init__(self, iterable=None):
        if iterable:
            if isinstance(iterable, UserTuple):
                self.data = iterable.data
            else:
                self.data = tuple(iterable)
        else:
            self.data = tuple()

    def __contains__(self, __key, /):
        return self.data.__contains__(__key)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    def __hash__(self):
        return hash(self.data)

    def __mul__(self, __value, /) -> TypeUserTyple:
        return self.__class__(self.data.__mul__(__value))

    __rmul__ = __mul__

    def __add__(self, __value, /) -> TypeUserTyple:
        if isinstance(__value, UserTuple):
            return self.__class__(self.data.__add__(__value.data))
        return self.__class__(self.data.__add__(__value))

    __radd__ = __add__

    def __class_getitem__(cls, __name, /):
        return tuple.__class_getitem__(__name)

    def __getitem__(self, __key, /):
        return self.data.__getitem__(__key)

    def __eq__(self, __value, /):
        if isinstance(__value, UserTuple):
            return self.data.__eq__(__value.data)
        return self.data.__eq__(__value)

    def __ge__(self, __value, /):
        if isinstance(__value, UserTuple):
            return self.data.__ge__(__value.data)
        return self.data.__ge__(__value)

    def __gt__(self, __value, /):
        if isinstance(__value, UserTuple):
            return self.data.__gt__(__value.data)
        return self.data.__gt__(__value)

    def __le__(self, __value, /):
        if isinstance(__value, UserTuple):
            return self.data.__le__(__value.data)
        return self.data.__le__(__value)

    def __lt__(self, __value, /):
        if isinstance(__value, UserTuple):
            return self.data.__lt__(__value.data)
        return self.data.__lt__(__value)

    def __ne__(self, __value, /):
        if isinstance(__value, UserTuple):
            return self.data.__ne__(__value.data)
        return self.data.__ne__(__value)

    def count(self, __value, /):
        return self.data.count(__value)

    def index(self, __value, /):
        return self.data.index(__value)

TypeUserDeque = TypeVar('TypeUserDeque', bound='UserDeque')

class UserDeque:
    def __init__(self, iterable=(), maxlen=None):
        if iterable:
            if isinstance(iterable, UserDeque):
                self.data = iterable.data
            else:
                self.data = deque(iterable, maxlen=maxlen)
        else:
            self.data = deque(maxlen=maxlen)

    @classmethod
    def __class_getitem__(cls, __item, /):
        return deque.__class_getitem__(__item)

    def __contains__(self, __key, /):
        return self.data.__contains__(__key)

    def __copy__(self):
        return self.__class__(self.data.__copy__())

    def __delitem__(self, __key, /):
        return self.data.__delitem__(__key)

    def __getitem__(self, __key, /):
        return self.data.__getitem__(__key)

    def __setitem__(self, __key, __value):
        return self.data.__setitem__(__key, __value)

    def __len__(self):
        return self.data.__len__()

    def __iter__(self):
        return self.data.__iter__()

    def __repr__(self):
        return self.data.__repr__()

    def __reversed__(self):
        return self.data.__reversed__()

    def __reduce__(self):
        return self.data.__reduce__()

    def __sizeof__(self):
        return self.data.__sizeof__()

    def __add__(self, __value, /) -> TypeUserTyple:
        if isinstance(__value, UserDeque):
            return self.__class__(self.data.__add__(__value.data))
        return self.__class__(self.data.__add__(__value))

    __radd__ = __add__

    def __iadd__(self, __value, /):
        if isinstance(__value, UserDeque):
            return self.data.__iadd__(__value.data)
        return self.data.__iadd__(__value)

    def __mul__(self, __value, /) -> TypeUserTyple:
        return self.__class__(self.data.__mul__(__value))

    __rmul__ = __mul__

    def __imul__(self, __value, /):
        return self.data.__imul__(__value)

    def __eq__(self, __value, /):
        if isinstance(__value, UserDeque):
            return self.data.__eq__(__value.data)
        return self.data.__eq__(__value)

    def __ge__(self, __value, /):
        if isinstance(__value, UserDeque):
            return self.data.__ge__(__value.data)
        return self.data.__ge__(__value)

    def __gt__(self, __value, /):
        if isinstance(__value, UserDeque):
            return self.data.__gt__(__value.data)
        return self.data.__gt__(__value)

    def __le__(self, __value, /):
        if isinstance(__value, UserDeque):
            return self.data.__le__(__value.data)
        return self.data.__le__(__value)

    def __lt__(self, __value, /):
        if isinstance(__value, UserDeque):
            return self.data.__lt__(__value.data)
        return self.data.__lt__(__value)

    def __ne__(self, __value, /):
        if isinstance(__value, UserDeque):
            return self.data.__ne__(__value.data)
        return self.data.__ne__(__value)

    def append(self, __x, /):
        return self.data.append(__x)

    def appendleft(self, __x, /):
        return self.data.appendleft(__x)

    def clear(self):
        return self.data.clear()

    def copy(self) -> TypeUserDeque:
        return self.__class__(self.data.copy())

    def count(self, __x, /):
        return self.data.count(__x)

    def extend(self, __iterable, /):
        return self.data.extend(__iterable)

    def extendleft(self, __iterable, /):
        return self.data.extendleft(__iterable)

    def index(self, __x, __start: int=0, __stop: int=..., /):
        return self.data.index(__x, __start, __stop)

    def insert(self, __i: int, __x, /):
        return self.data.insert(__i, __x)

    def pop(self):
        return self.data.pop()

    def popleft(self):
        return self.data.popleft()

    def remove(self, __value, /):
        return self.data.remove(__value)

    def reverse(self):
        return self.data.reverse()

    def rotate(self, __n: int=1, /):
        return self.data.rotate(__n)

    maxlen = property(lambda self: object(), lambda self, v: None, lambda self: None)

    __hash__ = None

def test_UserTyple():
    print(1)
    otuple = (1, 2, 3, 3)
    utuple = UserTuple(otuple)
    if otuple != utuple:
        print(otuple, type(otuple))
        print(utuple, type(utuple))
    print(2)
    if otuple * 2 != utuple * 2 or 2 * otuple != 2 * utuple:
        print(otuple * 2, type(otuple))
        print(utuple * 2, type(utuple))
        print(2 * otuple, type(otuple))
        print(2 * utuple, type(utuple))
    print(3)
    if len((x:=set((otuple+otuple, otuple+utuple, utuple+otuple, utuple+utuple)))) != 1:
        print(x)
        print(otuple + otuple)
        print(otuple + utuple)
        print(utuple + otuple)
        print(utuple + utuple)
    print(4)
    if list(otuple) != list(utuple):
        print(list(otuple))
        print(list(utuple))
    print(5)
    otuple += (1, 2)
    utuple += (1, 2)
    otuple *= 2
    utuple *= 2
    if otuple != utuple:
        print(otuple, type(otuple))
        print(utuple, type(utuple))

def test_UserDeque():
    print(1)
    Odeque = deque([1, 2, 3, 4])
    Udeque = UserDeque(Odeque)
    if Odeque != Udeque:
        print(Odeque, type(Odeque))
        print(Udeque, type(Udeque))

if __name__ == '__main__':
    test_UserDeque()

