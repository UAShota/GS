"""
Chat buttons engine
"""

from .command_baf import DwgbCmdBaf
from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage
from ..vkapi import *


class DwgbCmdButtons(DwgbCmdCustom):
    """ Команда накладывания бафа """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.club = VkApi(token="912aae31dcf728d5084549ee55de9d04b4ca64ed7d7d92729cd09582d0e7508927c1961dd6ec299d80903")
        self.regButtonsFull = self.getRegex(r"^склад кнопки$")
        self.regButtonsBaf = self.getRegex(r"^склад миникнопки$")
        self.regBaf = self.getRegex(r"^(?:\[.+?\]|хочу) апо (\d+)$")
        self.regLinks = self.getRegex(r"^(?:\[.+?\]|хочу) (💬|ссылки)$")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        tmp_match = self.regBaf.match(message.text)
        if tmp_match:
            return self.showBaf(message, tmp_match)
        elif self.regLinks.match(message.text):
            return self.showLinks(message)
        elif self.regButtonsFull.match(message.text):
            return self.showButtonsFull(message)
        elif self.regButtonsBaf.match(message.text):
            return self.showButtonsBaf(message)
        # Ничего не найдено
        return False

    def send(self, message: DwgbMessage, text: str, keyboard: str):
        """ Отправка """
        tmp_params = {
            "chat_id": 7,
            "message": text,
            "random_id": 0,
            "keyboard": keyboard
        }
        self.transport.writeChannel("", message, False, -1, client=self.club, params=tmp_params)
        return True

    def showButtonsFull(self, message: DwgbMessage):
        """ Показ набора кнопок """
        return self.send(message, "Ойбай кнопки", '{"one_time":false,"buttons":[[{"action":{"type":"text","label":"🌕","payload":""},"color":"secondary"},{"action":{"type":"text","label":"🍄","payload":""},"color":"secondary"},{"action":{"type":"text","label":"📕","payload":""},"color":"secondary"},{"action":{"type":"text","label":"🛒","payload":""},"color":"secondary"}],[{"action":{"type":"text","label":"Апо 1","payload":""},"color":"secondary"},{"action":{"type":"text","label":"Апо 2","payload":""},"color":"secondary"},{"action":{"type":"text","label":"Апо 3","payload":""},"color":"secondary"},{"action":{"type":"text","label":"Апо 4","payload":""},"color":"secondary"}]]}')

    def showButtonsBaf(self, message: DwgbMessage):
        """ Показ набора кнопок """
        return self.send(message, "Ойбай кнопки", '{"one_time":false,"buttons":[[{"action":{"type":"text","label":"Апо 1","payload":""},"color":"secondary"},{"action":{"type":"text","label":"Апо 2","payload":""},"color":"secondary"},{"action":{"type":"text","label":"Апо 3","payload":""},"color":"secondary"},{"action":{"type":"text","label":"Апо 4","payload":""},"color":"secondary"}]]}')

    def showBaf(self, message: DwgbMessage, tmp_match):
        """ Показ кнопок бафа """
        return self.send(message, "апо %s 🌕%s" % (tmp_match[1], DwgbCmdBaf.BAF_COST), '{"buttons":[[{"action":{"type":"text","label":"Баф атаки","payload":""},"color":"positive"},{"action":{"type":"text","label":"Баф защиты","payload":""},"color":"positive"},{"action":{"type":"text","label":"Баф удачи","payload":""},"color":"positive"}],[{"action":{"type":"text","label":"Баф людей","payload":""},"color":"positive"},{"action":{"type":"text","label":"Баф гномик","payload":""},"color":"positive"},{"action":{"type":"text","label":"Баф демона","payload":""},"color":"positive"}],[{"action":{"type":"text","label":"Баф нежить","payload":""},"color":"positive"},{"action":{"type":"text","label":"Ссылки","payload":""},"color":"primary"},{"action":{"type":"text","label":"Газета","payload":""},"color":"primary"}]],"inline":true}')

    def showLinks(self, message: DwgbMessage):
        """ Показ ссылок """
        return self.send(message, "Аве!", '{"buttons":[[{"action":{"type":"open_link","link":"https://vk.com/@72923353-kolodec-dostigenie","label":"Достижения","payload":""}},{"action":{"type":"open_link","link":"https://vk.com/@shad_death-eventbook","label":"Страницы","payload":""}}],[{"action":{"type":"open_link","link":"https://vk.com/@465701449-ekspedicii-kolodca","label":"Экспедиции","payload":""}},{"action":{"type":"open_link","link":"https://vk.com/@shaden87-sobytiya","label":"События","payload":""}}],[{"action":{"type":"open_link","link":"https://vk.com/@shaden87-outwells","label":"Похождения","payload":""}},{"action":{"type":"open_link","link":"https://vk.com/app7055214_-182985865","label":"Рюкзак","payload":""}}]],"inline":true}')
