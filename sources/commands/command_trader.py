"""
Trader
"""
import json
from threading import Thread
from time import sleep

import requests
import urllib3

from .command_custom import DwgbCmdCustom, DwgbCmdConst
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdTrader(DwgbCmdCustom):
    """ Автоскупщик """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regAccept = self.getRegex(r"^⚖.+Вы успешно приобрели с аукциона предмет (\d+)\*(.+) - (\d+)")
        self.regScrolls = self.getRegex(r"^📜Вы получили 100 пустых страниц")
        self.buytimes = {}
        self.thread = Thread(target=self.threadbuy).start()

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        if self.scrolls(message):
            return True
        if self.trade(message):
            return True
        else:
            return False

    def threadbuy(self):
        """ Покупка """
        urllib3.disable_warnings()
        while True:
            try:
                # Запросим файл
                tmp_response = requests.get("https://empirehopes.space/export.txt", verify=False)
                if not tmp_response.ok:
                    print("Trade error: %s" % tmp_response.text)
                    sleep(120)
                    continue
                # Загрузим данные
                tmp_json = json.loads(tmp_response.content.decode("utf-8"))
                # Переберем все элементы
                for tmp_key, tmp_packet in tmp_json.items():
                    if not tmp_packet:
                        continue
                    tmp_time = tmp_packet[0]
                    tmp_name = tmp_packet[2]
                    for tmp_item in tmp_packet[1]:
                        tmp_count = tmp_item[0]
                        tmp_cost = tmp_item[1]
                        tmp_lot = tmp_item[2]
                        # С этого списка уже все купили
                        if tmp_key in self.buytimes and (self.buytimes[tmp_key] == tmp_time):
                            continue
                        # Определим нужно ли его скупать
                        if tmp_name not in DwgbCmdConst.STORE_DATA:
                            continue
                        # Вытащим
                        tmp_store = DwgbCmdConst.STORE_DATA[tmp_name]
                        if (tmp_store.count + tmp_count >= tmp_store.limit) or (tmp_count > DwgbCmdConst.STORE_FREE):
                            continue
                        # Цена
                        if tmp_store.trade < int(tmp_cost / tmp_count):
                            continue
                        # Купим
                        message = DwgbMessage()
                        message.channel = self._GAME_BOT_ID
                        self.transport.writeChannel("Купить лот %s" % tmp_lot, message, False)
                        self.buytimes[tmp_key] = tmp_time
                        sleep(15)
                sleep(60)
            except Exception as e:
                print(e)
                print(e.__traceback__)
                sleep(120)

    def trade(self, message: DwgbMessage):
        """ Учет покупки """
        # Проверим канал
        if message.channel != self._GAME_BOT_ID:
            return False
        # Проверим бота
        if message.user != self._GAME_BOT_ID:
            return False
        # Пробьем регулярку
        tmp_match = self.regAccept.search(message.text)
        if not tmp_match:
            return False
        # Учет покупки
        tmp_count = int(tmp_match[1])
        tmp_name = tmp_match[2].lower()
        tmp_cost = int(tmp_match[3])
        # Это мы не закупаем
        if tmp_name not in DwgbCmdConst.STORE_DATA:
            return True
        # Запишем в базу
        self.setStorage(0, self._ITEM_GOLD, -tmp_cost)
        self.setBookPages(DwgbCmdConst.STORE_DATA[tmp_name], tmp_count)
        # Успешно
        return True

    def scrolls(self, message: DwgbMessage):
        """ Покупка """
        # Проверим канал
        if message.channel != self._GAME_BOT_ID:
            return False
        # Проверим бота
        if message.user != self._GAME_BOT_ID:
            return False
        # Пробьем регулярку
        tmp_match = self.regScrolls.search(message.text)
        if not tmp_match:
            return False
        # Запишем в базу
        self.setStorage(0, self._ITEM_GOLD, -300)
        self.setBookPages(DwgbCmdConst.STORE_DATA[self._ITEM_PAGE], 100)
        # Успешно
        return True
