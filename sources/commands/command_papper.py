"""
Newspapper engine
"""

from datetime import datetime, timedelta

from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdPapper(DwgbCmdCustom):
    """ Команда проверки баланса """

    # Создание таблицы
    __QUERY_PAPPER_CREATE = "CREATE TABLE IF NOT EXISTS dwgb_papper (" + "uid serial primary key, name VARCHAR (50) NOT NULL, data VARCHAR (150) NOT NULL, date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);" + "CREATE UNIQUE INDEX IF NOT EXISTS name_idx ON dwgb_papper (name);"

    # Запрос объявлений
    __QUERY_PAPPER_GET = "SELECT name, data FROM dwgb_papper where date > current_date - interval '7 days'"

    # Добавление объявления
    __QUERY_PAPPER_ADD = "INSERT INTO dwgb_papper (name, data) values(%(name)s, %(data)s) ON CONFLICT (name) DO UPDATE SET data = %(data)s"

    # Удаление объявления
    __QUERY_PAPPER_DEL = "DELETE FROM dwgb_papper WHERE name=%(name)s"

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        # Доска
        self.database.exec(self.__QUERY_PAPPER_CREATE, {})
        self.date = self.boardTime()
        self.boards = {}
        # События
        self.regBoardDel = self.getRegex(r"^газета удалить")
        self.regBoardAdd = self.getRegex(r"^газета (.+)")
        self.regBoardGet = self.getRegex(r"^(?:\[.+?\] )?газета")
        # Загрузим
        for tmp_item in self.database.queryall(self.__QUERY_PAPPER_GET, {}):
            self.boards[tmp_item["name"]] = tmp_item["data"]

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        tmp_match = self.regBoardDel.match(message.text)
        if tmp_match:
            return self.doBoardDel(message, tmp_match)
        tmp_match = self.regBoardAdd.match(message.text)
        if tmp_match:
            return self.doBoardAdd(message, tmp_match)
        tmp_match = self.regBoardGet.match(message.text)
        if tmp_match or (self.boards and (datetime.today() > self.date)):
            return self.doBoardGet(message, tmp_match) and tmp_match
        return False

    def boardTime(self):
        """ Time to auto showing """
        return datetime.today() + timedelta(hours=3)

    def boardName(self, message: DwgbMessage):
        """ Papper owner """
        return "💬[id%s|%s]" % (message.user, message.name.split()[0])

    def doBoardAdd(self, message: DwgbMessage, _match: {}):
        """ Добавление объявления """
        tmp_name = self.boardName(message)
        tmp_text = (_match[1][:100]).replace("\n", " ")
        self.boards[tmp_name] = tmp_text
        self.database.exec(self.__QUERY_PAPPER_ADD, {"name": tmp_name, "data": tmp_text})
        self.transport.writeChannel("Объявление записано", message, True)
        return True

    def doBoardDel(self, message: DwgbMessage, _match: {}):
        """ Удаление объявления """
        tmp_name = self.boardName(message)
        if tmp_name in self.boards:
            self.boards.pop(tmp_name)
            self.database.exec(self.__QUERY_PAPPER_DEL, {"name": tmp_name})
            self.transport.writeChannel("Объявление удалено", message, True)
        else:
            self.transport.writeChannel("Ваших объявлений нет", message, True)
        return True

    def doBoardGet(self, message: DwgbMessage, _match: {}):
        """ Показ доски """
        self.date = self.boardTime()
        tmp_board = ""
        for tmp_user, tmp_data in self.boards.items():
            tmp_board += "%s: %s\n" % (tmp_user, tmp_data)
        if tmp_board:
            self.transport.writeChannel("📜Объявления:\n%s" % tmp_board, message, False, 720)
        else:
            self.transport.writeChannel("📜Объявлений пока нет", message, False)
        return True
