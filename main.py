import db_atribute
import dataclasses

@dataclasses.dataclass(kw_only=True)
class User(db_atribute.Db_Atribute):
    name: str
    _list_db_atributes: list = dataclasses.field(default_factory=lambda: ['name'])

a = User(id=10, name='hello')
print(a)