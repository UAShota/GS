"""
Messenger message struct
"""


class DwgbMessage(object):
    """ Структура описания сообщения """

    #: Номер
    id = 0

    #: Канал
    channel = 0

    #: Код отправителя
    user = 0

    #: Имя отправителя
    name = ""

    #: Текст
    text = ""
