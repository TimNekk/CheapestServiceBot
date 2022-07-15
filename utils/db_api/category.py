from dataclasses import dataclass
from typing import Optional

from utils.db_api.number import Number


@dataclass
class Category:
    id: int
    service_id: int
    name: str
    price: int
    show: bool
    description: Optional[str]
    order: int

    def __post_init__(self):
        self.show = self.show == 1
        self.description = self.description.replace('\\n', '\n') if self.description else None

    def get_numbers(self, not_busy: bool = True) -> list[Number]:
        from loader import db

        sql = 'SELECT * FROM Numbers WHERE category_id = ?'
        if not_busy:
            sql += ' AND busy = 0'

        numbers = []
        for number in db.execute(sql, parameters=(self.id,), fetchall=True):
            numbers.append(Number(*number))
        return numbers

    def get_number_count(self, not_busy: bool = True) -> int:
        from loader import db

        sql = 'SELECT COUNT(*) FROM Numbers WHERE category_id = ?'
        if not_busy:
            sql += ' AND busy = 0'

        return db.execute(sql, parameters=(self.id,), fetchone=True)[0]

    @property
    def service(self) -> 'Service':
        from loader import db
        return db.get_service(self.service_id)

    def increase_order(self) -> None:
        from loader import db, Database

        db.increase_order(Database.TableNames.categories, self.id)

    def decrease_order(self) -> None:
        from loader import db, Database

        db.decrease_order(Database.TableNames.categories, self.id)

    def set_name(self, value: str) -> None:
        self.name = value
        self._update('name', value)

    def set_price(self, value: int) -> None:
        self.price = value
        self._update('price', value)

    def set_description(self, value: str) -> None:
        self.description = value
        self._update('description', value)

    def set_show(self, value: bool) -> None:
        self.show = value
        self._update('show', value)

    def delete(self) -> None:
        from loader import db, Database

        db.move_up(Database.TableNames.categories, self.id)
        sql = "DELETE FROM Categories WHERE id = ?"
        db.execute(sql, parameters=(self.id,), commit=True)

        del self

    def _update(self, parameter, value) -> None:
        from loader import db

        sql = f"UPDATE Categories SET {parameter} = ? WHERE id = ?"
        db.execute(sql, parameters=(value, self.id), commit=True)