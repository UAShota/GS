"""
Database entry
"""

import psycopg2
from psycopg2.extras import RealDictCursor


class DwgbDatabase(object):
    """ Движок базы данных """

    def __init__(self, dbtoken: str):
        """ Конструктор """
        self.connection = None
        self.cursor = None
        self.connect(dbtoken)

    def __del__(self):
        """ Деструктор """
        self.cursor.close()

    def connect(self, dbtoken: str):
        """ Соединение с базой """
        self.connection = psycopg2.connect(dbtoken, sslmode="require", cursor_factory=RealDictCursor)
        self.cursor = self.connection.cursor()

    def exec(self, sql: str, params: dict):
        """ Выполнение запроса """
        try:
            self.cursor.execute(sql, params)
        finally:
            self.connection.commit()

    def queryone(self, sql: str, params: dict):
        """ Возвращение одного параметра """
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def queryall(self, sql: str, params: dict):
        """ Возвращение всех параметров """
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()
