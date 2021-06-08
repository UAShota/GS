"""
Some converts
"""
import json
import random
import traceback
from urllib import parse

import requests

from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdFlooder(DwgbCmdCustom):
    """ Вычисление чистого значения передачи """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regMsg = self.getRegex(r"(\[.+?\])?(марго|маргоша|маша)?(.+)")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        if message.user == self.transport.getOwnerId():
            return True
        if message.user == self._DW_BOT_ID:
            return True
        # Проверим что нужно написать ответ
        tmp_match = self.regMsg.match(message.text)
        if not tmp_match:
            return True
        if tmp_match[1]:
            return True
        # Подготовим запрос
        tmp_data = "query=" + parse.quote('{"ask":"%s","userid":"dwgb","key":""}' % tmp_match[3])
        try:
            tmp_response = requests.post("https://aiproject.ru/api/", tmp_data, headers=self.apiHeaders(len(tmp_data), host="aiproject.ru"))
        except Exception as e:
            print("Chat failed %s %s" % (e, traceback.format_exc().replace("\n", " ")))
            return True
        if not tmp_response.ok:
            return True
        # Разберем пакет
        tmp_json = json.loads(tmp_response.content.decode("utf-8"))
        if tmp_json["status"] != 1:
            return True
        # Напишем в чатик ответ
        if not tmp_match[2]:
            return True
        tmp_text = "🐝"
        if tmp_json["aiml"]:
            tmp_text += tmp_json["aiml"]
        if tmp_json["url"]:
            tmp_text += "\n%s" % tmp_json["url"]
        # Отправим
        return self.transport.writeChannel(tmp_text, message, False, -1)
