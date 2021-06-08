"""
Baf command
"""

from datetime import timedelta, datetime

from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdBaf(DwgbCmdCustom):
    """ Команда накладывания бафа """

    # Цена бафа
    BAF_COST = 300

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regApp = self.getRegex(r"^апо (\d+)")
        self.regGet = self.getRegex(r"^(?:\[.+?\]|хочу) баф (.+)")
        self.regSet = self.getRegex(r"^✨\[id(\d+)\|(.+?)], на Вас наложено благословение ")
        self.regCon = self.getRegex(r"^Благословение .+")
        self.avail = False
        self.apos = 0
        self.time = datetime.min

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        # Найден факт бафа
        tmp_match = self.regCon.match(message.text)
        if tmp_match:
            return self.useCon(message)
        # Найдено смена апостола
        tmp_match = self.regApp.match(message.text)
        if tmp_match:
            return self.useApp(message, tmp_match)
        # Найдена просьба бафа
        tmp_match = self.regGet.match(message.text)
        if tmp_match:
            return self.useBaf(message, tmp_match)
        # Найдено наложение бафа
        tmp_match = self.regSet.match(message.text)
        if tmp_match:
            return self.usePay(message, tmp_match)
        # Ничего не найдено
        return False

    def useCon(self, message: DwgbMessage):
        """ Был баф """
        self.apos = message.user
        return True

    def useApp(self, message: DwgbMessage, data: dict):
        """ Разрешение бафера """
        self.avail = data[1] == "1"
        # Adding to clear
        self.transport.clearQueue(message.id)
        # Not me
        if not self.avail:
            return True
        tmp_time = datetime.today()
        if tmp_time < self.time:
            tmp_time = (self.time - tmp_time).total_seconds()
            tmp_min = int(tmp_time / 60)
            tmp_sec = int(tmp_time % 60)
            tmp_time = "⌛"
            if tmp_min > 0:
                tmp_time += " %s мин." % tmp_min
            tmp_time += " %s сек." % tmp_sec
        else:
            tmp_time = "⌛ доступен (человек)"
        self.transport.writeChannel(tmp_time, message, True)
        # В любом случае операция успешна
        return True

    def useBaf(self, message: DwgbMessage, data: dict):
        """ Наложение бафа """
        if self.avail:
            self.transport.writeChannel("Благословение %s" % (data[1]), message, True)
        # В любом случае операция успешна
        return True

    def usePay(self, message: DwgbMessage, data: dict):
        """ Учет наложения бафа """
        # Игнор фальсификации
        if message.user != self._DW_BOT_ID:
            return False
        # Соберем параметры, самобаф игнорим
        tmp_id = int(data[1])
        if tmp_id == self.apos:
            return True
        # Уменьшим баланс за баф
        self.setStorage(tmp_id, self._ITEM_GOLD, -self.BAF_COST)
        # Сохраним время последнего бафа
        if self.avail:
            self.time = datetime.today() + timedelta(minutes=15)
        if self.apos != self.transport.getOwnerId():
            self.setStorage(self.apos, self._ITEM_GOLD, self.BAF_COST)
            self.transport.writeChannel("[id%s|Апостол], вы заработали 🌕%s" % (self.apos, self.BAF_COST), message, False)
        # Отправим сообщение
        self.transport.writeChannel("%s, Ваш баланс: 🌕%s" % (self.getAccountTag(tmp_id, data[2]), self.getStorageItem(tmp_id, self._ITEM_GOLD)), message, False)
        # Все хорошо
        return True
