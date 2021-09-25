"""
Trader
"""

from .command_custom import DwgbCmdCustom, DwgbCmdConst
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdTrader(DwgbCmdCustom):
    """ Автоскупщик """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regAccept = self.getRegex(r"^⚖.+Вы успешно приобрели с аукциона предмет (\d+)\*(.+) - (\d+)")
        self.regScrolls = self.getRegex(r"^📜Вы получили 100 пустых страниц")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        if self.scrolls(message):
            return True
        if self.trade(message):
            return True
        else:
            return False

    def trade(self, message: DwgbMessage):
        """ Учет покупки """
        # Проверим канал
        if message.channel != self._GAME_BOT_ID:
            return False
        # Проверим бота
        if message.user != self._GAME_BOT_ID:
            return False
        # Пробьем регулярку
        tmp_match = self.regAccept.search(message.text)
        if not tmp_match:
            return False
        # Учет покупки
        tmp_count = int(tmp_match[1])
        tmp_name = tmp_match[2].lower()
        tmp_cost = int(tmp_match[3])
        # Это мы не закупаем
        if tmp_name not in DwgbCmdConst.STORE_DATA:
            return True
        # Запишем в базу
        self.setStorage(0, self._ITEM_GOLD, -tmp_cost)
        self.setBookPages(DwgbCmdConst.STORE_DATA[tmp_name], tmp_count)
        # Успешно
        return True

    def scrolls(self, message: DwgbMessage):
        """ Покупка """
        # Проверим канал
        if message.channel != self._GAME_BOT_ID:
            return False
        # Проверим бота
        if message.user != self._GAME_BOT_ID:
            return False
        # Пробьем регулярку
        tmp_match = self.regScrolls.search(message.text)
        if not tmp_match:
            return False
        # Запишем в базу
        self.setStorage(0, self._ITEM_GOLD, -300)
        self.setBookPages(DwgbCmdConst.STORE_DATA[self._ITEM_PAGE], 100)
        # Успешно
        return True
