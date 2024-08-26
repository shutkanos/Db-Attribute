from typing import TypeVar
from collections.abc import MutableSet

T_user_set = TypeVar('T_user_set', bound='UserSet')

class UserSet(MutableSet):
    def __init__(self, iterable=None):
        if iterable:
            if isinstance(iterable, UserSet):
                self.data = iterable.data.copy()
            else:
                self.data = set(iterable)
        else:
            self.data = set()

    def __contains__(self, value):
        return value in self.data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    def __sub__(self, other):
        if isinstance(other, UserSet):
            return self.__class__(self.data - other.data)
        return self.__class__(self.data - other)

    def __rsub__(self, other):
        if isinstance(other, UserSet):
            return self.__class__(other.data - self.data)
        return self.__class__(other - self.data)

    def __isub__(self, other):
        self.data -= other
        return self

    def __or__(self, other):
        if isinstance(other, UserSet):
            return self.__class__(self.data | other.data)
        return self.__class__(self.data | other)

    __ror__ = __or__

    def __ior__(self, other):
        self.data |= other
        return self

    def __copy__(self) -> T_user_set:
        print('__copy__')
        return self.__class__(self.data)

    def add(self, __element):
        self.data.add(__element)

    def discard(self, __element):
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

    def copy(self) -> T_user_set:
        return self.__class__(self.data.copy())

    def union(self, *s) -> T_user_set:
        return self.__class__(self.data.union(*s))

    def difference(self, *s) -> T_user_set:
        return self.__class__(self.data.difference(*s))

    def intersection(self, *s) -> T_user_set:
        return self.__class__(self.data.intersection(*s))

    def symmetric_difference(self, __s) -> T_user_set:
        return self.__class__(self.data.symmetric_difference(__s))