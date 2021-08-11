"""
Item transfering
"""
import random

from .command_custom import DwgbCmdCustom, DwgbCmdConst
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage, DwgbTransfer, DwgbStorage


class DwgbCmdTransferItem(DwgbCmdCustom):
    """ Учет получения предмета """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regGet = self.getRegex(r"^👝\[id(\d+)\|(.+?)], получено: .(?:(\d+).+?)?(.+?) от игрока \[id(\d+)\|(.+?)]")
        self.loot = u"🛡"

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        # Проверка прав
        if message.user != self._DW_BOT_ID:
            return False
        # Проверка регулярки
        tmp_data = self.regGet.match(message.text)
        if not tmp_data:
            return False
        # Начнем сбор
        tmp_transfer = DwgbTransfer()
        tmp_transfer.message = message
        tmp_transfer.sourceId = int(tmp_data[1])
        tmp_transfer.sourceName = tmp_data[2]
        tmp_transfer.type = tmp_data[4].lower()
        # Если количество не указано = значит 1 штука
        if tmp_data[3]:
            tmp_transfer.count = int(tmp_data[3])
        else:
            tmp_transfer.count = 1
        tmp_transfer.targetId = int(tmp_data[5])
        tmp_transfer.targetName = tmp_data[6]
        tmp_transfer.item = self.getStorage(tmp_transfer.type)
        # Передача на склад
        if tmp_transfer.sourceId == self.transport.getOwnerId():
            if (not tmp_transfer.item) or (tmp_transfer.item.cost == 0):
                return self.incomingFree(tmp_transfer)
            else:
                return self.incomingPaid(tmp_transfer)
        # Передача со склада
        if tmp_transfer.targetId == self.transport.getOwnerId():
            if (not tmp_transfer.item) or (tmp_transfer.item.cost == 0):
                return self.outDoorFree(tmp_transfer)
            else:
                return self.outDoorPaid(tmp_transfer)
        # Ничегошеньки
        return False

    def incomingFree(self, transfer: DwgbTransfer):
        """ Передача на склад предмета без цены """
        # Увеличим в базе количество предметов
        self.setStorage(0, transfer.type, transfer.count)
        # Уведомим
        self.transport.writeChannel("%s, %s %s взято на хранение" % (self.getAccountTag(transfer.targetId, transfer.targetName), transfer.count, transfer.type), transfer.message, False)
        return True

    def incomingPaid(self, transfer: DwgbTransfer):
        """ Передача на склад предмета с ценой """
        self.setBookPages(transfer.item, transfer.count)
        # Увеличим в базе баланс
        tmp_cost = self.getCostIn(transfer.item.cost) * transfer.count
        self.setStorage(transfer.targetId, self._ITEM_GOLD, tmp_cost)
        # Уведомим
        self.transport.writeChannel("%s, %s %s принято за 🌕%s. Ваш баланс 🌕%s 📦%d/%d" % (self.getAccountTag(transfer.targetId, transfer.targetName), transfer.count, transfer.item.id, tmp_cost, self.getStorageItem(transfer.targetId, self._ITEM_GOLD), DwgbCmdConst.STORE_SIZE - DwgbCmdConst.STORE_FREE, DwgbCmdConst.STORE_SIZE), transfer.message, False)
        # Проверим на необходимость продажи
        if transfer.item.icon != self.loot:
            return True
        tmp_item: DwgbStorage = DwgbCmdConst.STORE_DATA[transfer.item.id]
        if not tmp_item.code:
            return True
        # Продадим излишки
        for tmp_i in range(1, tmp_item.count):
            if self.apiSell(tmp_item.code, 1):
                self.setStorage(0, tmp_item.id, -1)
                self.setStorage(0, self._ITEM_GOLD, tmp_item.cost)
        return True

    def outDoorFree(self, transfer: DwgbTransfer):
        """ Передача со склада предмета без цены """
        # Уменьшим в базе
        self.setStorage(0, transfer.type, -transfer.count)
        # Уведомим
        self.transport.writeChannel("%s, %s %s взято в аренду" % (self.getAccountTag(transfer.sourceId, transfer.sourceName), transfer.count, transfer.type), transfer.message, False)
        return True

    def outDoorPaid(self, transfer: DwgbTransfer):
        """ Передача со склада предмета с ценой """
        # Уменьшим в базе
        self.setStorage(0, transfer.item.id, -transfer.count)
        # Определим цену
        tmp_cost = self.getCostOut(transfer.item.cost) * transfer.count
        # Просчитаем бонус
        tmp_discount = random.randint(1, 100)
        if tmp_discount > 10:
            tmp_discount = 0
        # Учет бонуса
        if tmp_discount:
            tmp_cost -= int(tmp_cost / 100 * tmp_discount)
            tmp_text = "👝Критическая продажа! Стоимость уменьшена на %s%%! 🍀" % tmp_discount
        else:
            tmp_text = ""
        # Уменьшим в базе
        self.setStorage(transfer.sourceId, self._ITEM_GOLD, -tmp_cost)
        # Уведомим
        self.transport.writeChannel("%s, за %s оплачено 🌕%s. Ваш баланс: 🌕%s 📦%d/%d %s" % (self.getAccountTag(transfer.sourceId, transfer.sourceName), transfer.item.id, tmp_cost, self.getStorageItem(transfer.sourceId, self._ITEM_GOLD), DwgbCmdConst.STORE_SIZE - DwgbCmdConst.STORE_FREE, DwgbCmdConst.STORE_SIZE, tmp_text), transfer.message, False)
        return True
