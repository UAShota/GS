"""
Transfer record
"""

from .class_message import DwgbMessage
from .class_storage import DwgbStorage


class DwgbTransfer(object):
    """ Структура описания передачи предмета или золота """

    #: Исходное сообщение
    message: DwgbMessage = None

    #: Номер отправителя
    sourceId = ""

    #: Имя отправителя
    sourceName = ""

    #: Номер получателя
    targetId = ""

    #: Имя получателя
    targetName = ""

    #: Имя ресурса в сообщении
    type = ""

    #: Количество ресурсов
    count = 0

    #: Объект ресурса, если такой описан в базе
    item: DwgbStorage = None
