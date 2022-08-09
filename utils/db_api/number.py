from dataclasses import dataclass


@dataclass
class Number:
    id: str
    category_id: int
    phone_number: int
    busy: bool

    def __post_init__(self):
        self.busy = self.busy == 1

    @property
    def category(self) -> 'Category':
        from loader import db
        return db.get_category(self.category_id)

    def prolong(self) -> 'Number':
        raise NotImplementedError

    def set_number(self, value: int) -> None:
        self._update('number', value)
        self.phone_number = value

    def set_id(self, value: str) -> None:
        self._update('id', value)
        self.id = value

    def set_busy(self, value: bool) -> None:
        self._update('busy', 1 if value else 0)
        self.busy = value

    def delete(self) -> None:
        from loader import db

        sql = 'DELETE FROM Numbers WHERE id = ?'
        db.execute(sql, parameters=(self.id,), commit=True)

        del self

    def _update(self, parameter, value) -> None:
        from loader import db

        sql = f"UPDATE Numbers SET {parameter} = ? WHERE id = ?"
        db.execute(sql, parameters=(value, self.id), commit=True)