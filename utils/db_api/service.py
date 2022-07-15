from dataclasses import dataclass

from utils.db_api.category import Category


@dataclass
class Service:
    id: int
    code: str
    name: str
    show: bool
    guide_url: str
    order: int

    def __post_init__(self):
        self.show = self.show == 1

    def get_categories(self, show_only: bool = False) -> list[Category]:
        from loader import db

        sql = 'SELECT * FROM Categories WHERE service_id = ?'
        if show_only:
            sql += ' AND show = 1'
        sql += ' ORDER BY "order"'

        categories = []
        for category in db.execute(sql, parameters=(self.id,), fetchall=True):
            categories.append(Category(*category))
        return categories

    def get_category_count(self, show_only: bool = False) -> int:
        from loader import db

        sql = 'SELECT COUNT(*) FROM Categories WHERE service_id = ?'
        if show_only:
            sql += ' AND show = 1'

        return db.execute(sql, parameters=(self.id,), fetchone=True)[0]

    def increase_order(self) -> None:
        from loader import db, Database

        db.increase_order(Database.TableNames.services, self.id)

    def decrease_order(self) -> None:
        from loader import db, Database

        db.decrease_order(Database.TableNames.services, self.id)

    def set_name(self, value: str) -> None:
        self.name = value
        self._update('name', value)

    def set_guide_url(self, value: str) -> None:
        self.guide_url = value
        self._update('guide', value)

    def set_code(self, value: str) -> None:
        self.code = value
        self._update('code', value)

    def set_show(self, value: bool) -> None:
        self.show = value
        self._update('show', value)

    def delete(self) -> None:
        from loader import db, Database

        db.move_up(Database.TableNames.services, self.id)
        sql = "DELETE FROM Services WHERE id = ?"
        db.execute(sql, parameters=(self.id,), commit=True)

        del self

    def _update(self, parameter, value) -> None:
        from loader import db

        sql = f"UPDATE Services SET {parameter} = ? WHERE id = ?"
        db.execute(sql, parameters=(value, self.id), commit=True)