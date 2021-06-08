"""
Some converts
"""

from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdConvert(DwgbCmdCustom):
    """ Вычисление чистого значения передачи """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regFixedA = self.getRegex(r"^чистыми (\d+)$")
        self.regFixedB = self.getRegex(r"^чистыми о (\d+)$")
        self.regFloatA = self.getRegex(r"^грязными (\d+)$")
        self.regFloatB = self.getRegex(r"^грязными о (\d+)$")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        tmp_match = self.regFixedA.match(message.text)
        if tmp_match:
            self.transport.writeChannel("%s чистыми %s" % (tmp_match[1], self.getCostFixed(int(tmp_match[1]))), message, False)
            return True
        tmp_match = self.regFixedB.match(message.text)
        if tmp_match:
            self.transport.writeChannel("%s чистыми о %s" % (tmp_match[1], self.getCostFixed(int(tmp_match[1]), 0.95)), message, False)
            return True
        tmp_match = self.regFloatA.match(message.text)
        if tmp_match:
            self.transport.writeChannel("%s грязными %s" % (tmp_match[1], self.getCostFloat(int(tmp_match[1]))), message, False)
            return True
        tmp_match = self.regFloatB.match(message.text)
        if tmp_match:
            self.transport.writeChannel("%s грязными о %s" % (tmp_match[1], self.getCostFloat(int(tmp_match[1]), 0.95)), message, False)
            return True
        # Ничегошеньки
        return False
