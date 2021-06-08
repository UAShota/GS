"""
Displaying the balance
"""

from .command_custom import DwgbCmdConst, DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdBalance(DwgbCmdCustom):
    """ Команда проверки баланса """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regGet = self.getRegex(r"^(?:\[.+?\]|хочу) (🌕|баланс)$")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        if not self.regGet.match(message.text):
            return False
        tmpHave = self.getStorageItem(message.user, self._ITEM_GOLD)
        self.transport.writeChannel("%s, баланс 🌕%d 📦%d/%d" % (self.getAccountTag(message.user, message.name), tmpHave, DwgbCmdConst.STORE_SIZE - DwgbCmdConst.STORE_FREE, DwgbCmdConst.STORE_SIZE), message, False, 180)
        return True
