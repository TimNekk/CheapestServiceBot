import logging
import os
import sqlite3
import time
import uuid
from datetime import datetime, date
from enum import Enum
from shutil import copyfile, move
from typing import Optional

from utils.db_api.category import Category
from utils.db_api.number import Number
from utils.db_api.service import Service
from utils.db_api.user import User


class Database:
    def __init__(self, path_to_db='data/main.db'):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = tuple(), fetchone=False,
                fetchall=False, commit=False):

        connection = self.connection
        connection.set_trace_callback(self.log)
        cursor = connection.cursor()

        cursor.execute(sql, parameters)

        if commit:
            connection.commit()
        data = None
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()

        connection.close()

        return data

    @staticmethod
    def log(statement):
        logging.debug(statement)

    # -----------------------------------------------------------------
    # Users
    # -----------------------------------------------------------------

    def add_user(self, id: int, username: Optional[str], first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        sql = 'INSERT INTO Users(id, username, first_name, last_name) VALUES(?, ?, ?, ?)'
        self.execute(sql, parameters=(id, username, first_name, last_name), commit=True)
        return self.get_user(id)

    def get_user(self, id: int) -> Optional[User]:
        sql = 'SELECT * FROM Users WHERE id = ?'
        data = self.execute(sql, parameters=(id,), fetchone=True)
        return User(*data) if data else None

    def get_all_users(self, without_ban=False):
        sql = 'SELECT * FROM Users'

        if without_ban:
            sql += ' WHERE ban = 0'

        users = []
        for data in self.execute(sql, fetchall=True):
            users.append(User(*data))
        return users

    def get_users_count(self) -> int:
        sql = f"SELECT COUNT(*) FROM Users"
        return self.execute(sql, fetchone=True)[0]

    def get_users_count_by_date(self, utc_date: date) -> int:
        utc_date = utc_date.strftime('%Y-%m-%d')
        sql = f"SELECT COUNT(*) FROM Users WHERE DATETIME(join_datetime) > '{utc_date} 00:00:00' AND DATETIME(join_datetime) < '{utc_date} 23:59:59'"
        return self.execute(sql, fetchone=True)[0]

    # -----------------------------------------------------------------
    # Services
    # -----------------------------------------------------------------

    def add_service(self, name: str, code: str, guide: str, show: bool = True) -> Service:
        sql = 'INSERT INTO Services (name, code, guide, show, "order") VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX("order") + 1, 1) FROM Services))'
        self.execute(sql, parameters=(name, code, guide, show), commit=True)
        return self._get_service_by_name(name)

    def get_service(self, id: int) -> Optional[Service]:
        sql = 'SELECT * FROM Services WHERE id = ?'
        data = self.execute(sql, parameters=(id,), fetchone=True)
        return Service(*data) if data else None

    def _get_service_by_name(self, name: str) -> Optional[Service]:
        sql = 'SELECT * FROM Services WHERE name = ?'
        data = self.execute(sql, parameters=(name,), fetchone=True)
        return Service(*data) if data else None

    def get_all_services(self, show_only: bool = False) -> list[Service]:
        sql = 'SELECT * FROM Services'
        if show_only:
            sql += ' WHERE show = 1'
        sql += ' ORDER BY "order"'

        services = []
        for service in self.execute(sql, fetchall=True):
            services.append(Service(*service))
        return services

    def change_service_order(self, service_id: int, increase: bool):
        sql = f'UPDATE Services SET "order" = "order" + 1' \
              f' WHERE "order" = (SELECT "order" FROM Services WHERE id = ?) + {-1 if increase else 1}'
        self.execute(sql, parameters=(service_id,), commit=True)

        sql = f'UPDATE Services SET "order" = "order" + {-1 if increase else 1} WHERE id = ?'
        self.execute(sql, parameters=(service_id,), commit=True)

    # -----------------------------------------------------------------
    # Categories
    # -----------------------------------------------------------------

    def add_category(self, service_id: int, name: str, price: int, description: Optional[str] = None, show: bool = True) -> Category:
        sql = 'INSERT INTO Categories(service_id, name, price, show, description, "order") VALUES(?, ?, ?, ?, ?,' \
              ' (SELECT COALESCE(MAX("order") + 1, 1) FROM Categories WHERE service_id = ?))'
        self.execute(sql, parameters=(service_id, name, price, show, description, service_id), commit=True)
        return self.get_category(service_id)

    def get_category(self, id: int) -> Optional[Category]:
        sql = 'SELECT * FROM Categories WHERE id = ?'
        data = self.execute(sql, parameters=(id,), fetchone=True)
        return Category(*data) if data else None

    # -----------------------------------------------------------------
    # Numbers
    # -----------------------------------------------------------------

    def add_number(self, id: str, category_id: int, number: int) -> Number:
        sql = 'INSERT INTO Numbers(id, category_id, number) VALUES(?, ?, ?)'
        self.execute(sql, parameters=(id, category_id, number), commit=True)
        return self.get_number(id)

    def get_number(self, id: str) -> Optional[Number]:
        sql = 'SELECT * FROM Numbers WHERE id = ?'
        data = self.execute(sql, parameters=(id,), fetchone=True)
        return Number(*data) if data else None

    # -----------------------------------------------------------------
    # Moving
    # -----------------------------------------------------------------

    class TableNames(Enum):
        services = 'Services'
        categories = 'Categories'

    CATEGORIES_SQL_FILTER = ' AND service_id = (SELECT service_id FROM Categories WHERE id = ?)'

    def decrease_order(self, table_name: TableNames, id: int) -> None:
        sql = f'UPDATE {table_name.value}' \
              f' SET "order" = "order" - 1' \
              f' WHERE "order" = (SELECT "order" FROM {table_name.value} WHERE id = ?) + 1'

        if table_name == self.TableNames.categories:
            sql += self.CATEGORIES_SQL_FILTER
        self.execute(sql, parameters=(id,) + ((id,) if table_name == self.TableNames.categories else ()), commit=True)

        sql = f'UPDATE {table_name.value}' \
              f' SET "order" = CASE' \
              f' WHEN "order" =' \
              f' (SELECT MAX("order") +' \
              f' (CASE WHEN (SELECT COUNT(*) FROM {table_name.value} WHERE "order" = (SELECT "order" FROM {table_name.value} WHERE id = ?)) = 1' \
              f' THEN 0 ELSE 1 END) FROM {table_name.value})' \
              f' THEN "order"' \
              f' ELSE "order" + 1 END' \
              f' WHERE id = ?'

        if table_name == self.TableNames.categories:
            sql += self.CATEGORIES_SQL_FILTER
        self.execute(sql, parameters=(id, id) + ((id,) if table_name == self.TableNames.categories else ()), commit=True)

    def increase_order(self, table_name: TableNames, id: int) -> None:
        sql = f'UPDATE {table_name.value}' \
              f' SET "order" = CASE' \
              f' WHEN "order" = (SELECT MAX("order") FROM {table_name.value})' \
              f' THEN "order"' \
              f' ELSE "order" + 1 END' \
              f' WHERE "order" = (SELECT "order" FROM {table_name.value} WHERE id = ?) - 1'

        if table_name == self.TableNames.categories:
            sql += self.CATEGORIES_SQL_FILTER
        self.execute(sql, parameters=(id,) + ((id,) if table_name == self.TableNames.categories else ()), commit=True)

        sql = f'UPDATE {table_name.value}' \
              f' SET "order" = CASE' \
              f' WHEN "order" = 1' \
              f' THEN "order"' \
              f' ELSE "order" + -1 END' \
              f' WHERE id = ?'

        if table_name == self.TableNames.categories:
            sql += self.CATEGORIES_SQL_FILTER
        self.execute(sql, parameters=(id,) + ((id,) if table_name == self.TableNames.categories else ()), commit=True)

    def move_up(self, table_name: TableNames, id: int) -> None:
        sql = f'UPDATE {table_name.value}' \
              f' SET "order" = "order" - 1' \
              f' WHERE "order" >= (SELECT "order" FROM {table_name.value} WHERE id = ?)'

        if table_name == self.TableNames.categories:
            sql += ' AND service_id = (SELECT service_id FROM Categories WHERE id = ?)'
            self.execute(sql, parameters=(id, id), commit=True)
        else:
            self.execute(sql, parameters=(id,), commit=True)
