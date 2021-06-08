"""
Gold transfering
"""

from .command_custom import DwgbCmdCustom, DwgbCmdConst
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage, DwgbTransfer


class DwgbCmdTransferGold(DwgbCmdCustom):
    """ Учет получения золота """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regGold = self.getRegex(r"^🌕\[id(\d+)\|(.+?)], получено (\d+) золота от игрока \[id(\d+)\|(.+?)]")
        self.regShard = self.getRegex(r"^💎\[id(\d+)\|(.+?)], получено (\d+) осколков сердца от игрока \[id(\d+)\|(.+?)]")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        # Проверка прав
        if message.user != self._DW_BOT_ID:
            return False
        # Проверка золота
        tmp_data = self.regGold.match(message.text)
        if tmp_data:
            return self.usegold(message, tmp_data)
        # Проверка осколков
        tmp_data = self.regShard.match(message.text)
        if tmp_data:
            return self.useshards(message, tmp_data)
        # Передача не для склада
        return False

    def send(self, message: DwgbMessage, name: str, count: int):
        """ Возвращение сообщения о балансе """
        self.transport.writeChannel("%s, Ваш баланс: 🌕%s" % (name, count), message, False)
        return True

    def gettransfer(self, data: dict):
        """ Разбор параметров передачи """
        tmp_transfer = DwgbTransfer()
        tmp_transfer.sourceId = int(data[1])
        tmp_transfer.sourceName = data[2]
        tmp_transfer.count = int(data[3])
        tmp_transfer.targetId = int(data[4])
        tmp_transfer.targetName = data[5]
        # Вернем
        return tmp_transfer

    def usegold(self, message: DwgbMessage, data: dict):
        """ Передача осколков """
        tmp_transfer = self.gettransfer(data)
        # Фиксация передачи на склад
        if tmp_transfer.sourceId == self.transport.getOwnerId():
            return self.goldin(message, tmp_transfer)
        # Фиксация передачи со склада
        if tmp_transfer.targetId == self.transport.getOwnerId():
            return self.goldout(message, tmp_transfer)

    def useshards(self, message: DwgbMessage, data: dict):
        """ Передача золота """
        tmp_transfer = self.gettransfer(data)
        # Фиксация передачи на склад
        if tmp_transfer.sourceId == self.transport.getOwnerId():
            return self.shardsin(message, tmp_transfer)
        # Фиксация передачи со склада
        if tmp_transfer.targetId == self.transport.getOwnerId():
            return self.shardsout(message, tmp_transfer)

    def goldin(self, message: DwgbMessage, transfer: DwgbTransfer):
        """ Учет передачи золота на склад """
        # Увеличим баланс отправителя
        self.setStorage(transfer.targetId, self._ITEM_GOLD, transfer.count)
        # Увеличим баланс склада
        self.setStorage(0, self._ITEM_GOLD, transfer.count)
        # Уведомим
        return self.send(message, self.getAccountTag(transfer.targetId, transfer.targetName), self.getStorageItem(transfer.targetId, self._ITEM_GOLD))

    def goldout(self, message: DwgbMessage, transfer: DwgbTransfer):
        """ Учет передачи золота со склада """
        # Уменьшим баланс отправителя
        self.setStorage(transfer.sourceId, self._ITEM_GOLD, -self.getCostFixed(transfer.count))
        # Уменьшим баланс склада
        self.setStorage(0, self._ITEM_GOLD, -self.getCostFixed(transfer.count))
        # Уведомим
        return self.send(message, self.getAccountTag(transfer.sourceId, transfer.sourceName), self.getStorageItem(transfer.sourceId, self._ITEM_GOLD))

    def shardsin(self, message: DwgbMessage, transfer: DwgbTransfer):
        """ Учет передачи осколков на склад """
        # Увеличим баланс отправителя
        self.setStorage(transfer.targetId, self._ITEM_GOLD, transfer.count * self.getCostIn(DwgbCmdConst.STORE_DATA[self._ITEM_SHARDS].cost) // 100)
        # Увеличим баланс склада
        self.setStorage(0, self._ITEM_SHARDS, transfer.count)
        # Уведомим
        return self.send(message, self.getAccountTag(transfer.targetId, transfer.targetName), self.getStorageItem(transfer.targetId, self._ITEM_GOLD))

    def shardsout(self, message: DwgbMessage, transfer: DwgbTransfer):
        """ Учет передачи осколков со склада """
        # Уменьшим баланс отправителя
        self.setStorage(transfer.sourceId, self._ITEM_GOLD, -transfer.count * self.getCostOut(DwgbCmdConst.STORE_DATA[self._ITEM_SHARDS].cost) // 100)
        # Уменьшим баланс склада
        self.setStorage(0, self._ITEM_SHARDS, -self.getCostFixed(transfer.count, 0.95))
        # Уведомим
        return self.send(message, self.getAccountTag(transfer.sourceId, transfer.sourceName), self.getStorageItem(transfer.sourceId, self._ITEM_GOLD))
