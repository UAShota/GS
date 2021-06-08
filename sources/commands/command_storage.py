"""
Storage actions
"""
import random

from .command_custom import DwgbCmdCustom, DwgbCmdConst
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdStorage(DwgbCmdCustom):
    """ Отображение хранилища """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regView = self.getRegex(r"^(?:\[.+?\]|хочу) (склад|🍄|📕|📘|🛒)$")
        self.regBuy = self.getRegex(r"^(?:\[.+?\]|хочу) цены$")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        # Обзор
        tmp_data = self.regView.match(message.text)
        if tmp_data:
            return self.getView(message, tmp_data)
        # Недостача
        tmp_data = self.regBuy.match(message.text)
        if tmp_data:
            return self.getBuy(message)
        return False

    def getView(self, message: DwgbMessage, match: dict):
        """ Отображение склада """
        tmp_type = match[1]
        tmp_need_scrolls = False
        # Скидки
        if DwgbCmdConst.PERCENT_SELL <= 0.80:
            tmp_data = "💥 Черная пятница! Скидки %s%%! 💥\n" % int(DwgbCmdConst.PERCENT_SELL * 100)
        else:
            tmp_data = ""
        # Переберем хранилище
        for tmp_item, tmp_storage in DwgbCmdConst.STORE_DATA.items():
            if not tmp_storage.count and not tmp_storage.valueex:
                continue
            # Если нужен склад - не фильтруем
            if (tmp_type != "склад") and (tmp_type != "📦"):
                if tmp_type == "🍄":
                    if tmp_storage.icon != "🌳" and tmp_storage.icon != tmp_type:
                        continue
                elif tmp_type == "📕":
                    if tmp_storage.icon != "📕" and tmp_storage.icon != "📘":
                        continue
                elif tmp_type == "🛒":
                    if tmp_storage.icon == "🍄" or tmp_storage.icon == "📕" or tmp_storage.icon == "📘" or tmp_storage.icon == "🌳":
                        continue
            # Определим короткое имя
            if tmp_storage.short:
                tmp_short = "(" + tmp_storage.short + ")"
            else:
                tmp_short = ""
            # Дополним количество
            if tmp_storage.icon == "📕" or tmp_storage.icon == "📘":
                if tmp_storage.count > 0:
                    tmpCount = "%s+%s" % (tmp_storage.valueex, tmp_storage.count)
                else:
                    tmpCount = tmp_storage.valueex
            else:
                tmpCount = tmp_storage.count
            # Определим перелимит
            if tmp_storage.id != self._ITEM_GOLD and tmp_storage.count > tmp_storage.limit + 3:
                tmpLimit = " ❗"
            else:
                tmpLimit = ""
            # Свитки
            if tmp_storage.icon == "📜" and tmp_storage.count < 1000:
                tmp_need_scrolls = True
            # Без цены только аренда
            if tmp_storage.cost > 0:
                tmp_data += "%s%s: %s по %s %s %s\n" % (tmp_storage.icon, tmp_storage.id.capitalize(), tmpCount, self.getCostOut(tmp_storage.cost), tmp_short, tmpLimit)
            else:
                tmp_data += "%s%s: %s %s аренда %s\n" % (tmp_storage.icon, tmp_storage.id.capitalize(), tmpCount, tmp_short, tmpLimit)
        # Отправим
        self.transport.writeChannel("📦Заполненность: %s из %s\n" % (DwgbCmdConst.STORE_SIZE - DwgbCmdConst.STORE_FREE, DwgbCmdConst.STORE_SIZE) + tmp_data, message, False, 360)
        # Бонус
        if random.randint(1, 100) == 50:
            self.setBonus(message)
        # Свитки
        if tmp_need_scrolls:
            message.channel = self._GAME_BOT_ID
            self.transport.writeChannel("100 страниц (300 золота)", message, False)
        # Вернем
        return True

    def getBuy(self, message: DwgbMessage):
        """ Отображение закупок """
        tmp_data = "📦Продажа на склад %s%%, покупка - %s%%\n" % (DwgbCmdConst.PERCENT_BUY, DwgbCmdConst.PERCENT_SELL)
        # Переберем хранилище
        for tmpItem, tmp_storage in DwgbCmdConst.STORE_DATA.items():
            tmp_data += "%s%s: %s 🎚%s/%s/%s\n" % (tmp_storage.icon, tmp_storage.id.capitalize()[:15], tmp_storage.cost, tmp_storage.trade, tmp_storage.limit, tmp_storage.date.strftime("%m.%d"))
        # Отправим
        self.transport.writeChannel(tmp_data, message, False, 360)
        return True
