import db_class
import dataclasses

@dataclasses.dataclass(kw_only=True)
class Db_Atribute:
    id: int
    _list_db_atributes: list = dataclasses.field(default_factory=lambda: [])

    def _db_atribute_set_attr(self, key, value):
        if key in self._list_db_atributes:
            super().__setattr__(key, db_container.cheaker.create_one_db_class(value, _obj_dbatribute=self))

    def _db_atribute_container_update(self, key):
        """
        call this functions, when any container atribute is updated, to update this atribute in db
        :param key: atribute container which update
        :type key: str
        :return: None
        """
        pass

    def __setattr__(self, key, value):
        self._db_atribute_set_attr(key, value)
