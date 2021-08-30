"""
Changing storage values
"""
import json
import math
import re
import traceback
from datetime import datetime, timedelta

import requests
from matplotlib import pyplot as plt

from .command_custom import DwgbCmdConst, DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage, DwgbStorage


class DwgbCmdAdminStorage(DwgbCmdCustom):
    """ Администрирование хранилища """

    # Имя файла плоттера
    __PLOT_IMAGE = "./storagecost.png"

    #: Добавление элемента склада
    __QUERY_STORAGE_ADD = "INSERT INTO dwgb_storages (owner, item) VALUES (%(owner)s, %(item)s) ON CONFLICT DO NOTHING"

    #: Настройка элемента склада
    __QUERY_STORAGE_SET = "UPDATE dwgb_storages SET {0} WHERE owner=%(owner)s AND item=%(item)s"

    #: Удаление позиции
    __QUERY_STORAGE_DEL = "DELETE FROM dwgb_storages WHERE owner=%(owner)s AND item=%(item)s"

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.date = datetime.min
        self.regItem = self.getRegex(r"(?:^склад (\d+)?\s*предмет ([\(\)\w|\s]+))")
        self.regDelete = self.getRegex(r"^склад (\d+)?\s*удалить (\D+)")
        self.regItems = self.getRegex(r"(?: -(\S+) (\S+))")
        self.regPercent = self.getRegex(r"^склад процент (\d+) (\d+)")
        self.regReload = self.getRegex(r"^склад обновить")
        self.regInfo = self.getRegex(r"^склад цену(.+)?")
        self.regSave = self.getRegex(r"^(хорошо|\d+)")
        self.regBag = self.getRegex(r"^золота - \d+\.")
        self.regInventory = self.getRegex(r"^(.+?) - (\d+)\.$")
        self.message = None

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        if datetime.today() > self.date:
            self.setcostchange(message)
        # Самопроверка инвентаря
        if (message.user == self._GAME_BOT_ID) and (self.regBag.match(message.text)):
            return self.rebag(message)
        # Auth
        if (message.user != 384297286) and (message.user != 66313242) and (message.user != 38752464):
            return False
        # Сохранение цены
        tmp_match = self.regSave.match(message.text)
        if tmp_match:
            return self.save(tmp_match, message)
        # Удаление позиции
        tmp_match = self.regDelete.match(message.text)
        if tmp_match:
            return self.delete(tmp_match, message)
        # Просмотр просрочки
        tmp_match = self.regInfo.match(message.text)
        if tmp_match:
            return self.getInfo(tmp_match, message)
        # Перезагрузка склада
        tmp_match = self.regReload.match(message.text)
        if tmp_match:
            return self.reloadStorages(message)
        # Установка скидки
        tmp_match = self.regPercent.match(message.text)
        if tmp_match:
            return self.percent(tmp_match, message)
        # Проверка наличия предмета для обновления
        tmp_match = self.regItem.match(message.text)
        if tmp_match is None:
            return False
        # Поиск всех параметров
        tmp_raw = self.regItems.findall(message.text)
        if tmp_raw is None:
            return True
        # Проверим владельца
        tmp_owner = tmp_match[1]
        if tmp_owner is None:
            tmp_owner = self.transport.getOwnerId()
        # Определим имя предмета
        tmp_name = tmp_match[2].strip().lower()
        tmp_params = []
        # Переберем все поля
        for tmp_row in tmp_raw:
            self.read(tmp_row, tmp_params)
        # Проверим
        if not tmp_params:
            return True
        # Запишем
        tmp_value = ",".join(tmp_params)
        self.database.exec(self.__QUERY_STORAGE_ADD, {"owner": tmp_owner, "item": tmp_name})
        self.database.exec(self.__QUERY_STORAGE_SET.format(tmp_value), {"owner": tmp_owner, "item": tmp_name})
        # Перезагрузим
        self.reloadStorages()
        # Ответим
        self.transport.writeChannel("Сохранено", message, True)
        return True

    def read(self, data: list, params: list):
        """ Чтение параметров """
        tmp_field = data[0]
        tmp_value = data[1]
        # Лимит предметов
        if tmp_field == "лим":
            params.append("maxlimit=%s" % int(tmp_value))
        elif tmp_field == "цена":
            params.append("cost=%s" % int(tmp_value))
            params.append("date=now()")
        elif tmp_field == "кол":
            params.append("value=%s" % int(tmp_value))
        elif tmp_field == "сток":
            params.append("trade=%s" % int(tmp_value))
        elif tmp_field == "доп":
            params.append("valueex=%s" % int(tmp_value))
        elif tmp_field == "код":
            params.append("code=%s" % int(tmp_value))
        elif tmp_field == "иконка":
            params.append("icon='%s'" % tmp_value)
        elif tmp_field == "тег":
            params.append("short='%s'" % tmp_value)
        return True

    def save(self, match: list, message: DwgbMessage):
        """ Сохранение прошлой цены """
        if not DwgbCmdConst.ITEM:
            return False
        # Определим тип
        if str(match[1]).lower() == "хорошо":
            tmp_cost = str(DwgbCmdConst.ITEM.average)
        else:
            tmp_cost = str(match[1])
        self.setcostdb(tmp_cost)
        # Ответим
        self.transport.writeChannel("Сохранено %s" % tmp_cost, message, True)
        # Вернем
        return True

    def percent(self, match: list, message: DwgbMessage):
        """ Установка процента """
        DwgbCmdConst.PERCENT_BUY = int(match[1]) / 100
        DwgbCmdConst.PERCENT_SELL = int(match[2]) / 100
        # Ответим
        self.transport.writeChannel("Установлено скупка %s%% продажа %s%% " % (int(match[1]), int(match[2])), message, True)
        return True

    def delete(self, match: list, message: DwgbMessage):
        """ Удаление позиции """
        tmpOwner = match[1]
        if tmpOwner is None:
            tmpOwner = self.transport.getOwnerId()
        # Удалим
        self.database.exec(self.__QUERY_STORAGE_DEL, {"owner": tmpOwner, "item": match[2].strip().lower()})
        # Перезагрузим
        self.reloadStorages()
        # Ответим
        self.transport.writeChannel("Удалено %s для %s" % (match[2], tmpOwner), message, True)
        return True

    def getInfo(self, match: list, message: DwgbMessage):
        """ Отображение цен """
        DwgbCmdConst.ITEM = None
        if match[1]:
            tmp_item = str(match[1]).lower().strip()
            for tmpItem, tmp_storage in DwgbCmdConst.STORE_DATA.items():
                if (tmp_item == tmpItem) or (tmp_item == tmp_storage.short):
                    DwgbCmdConst.ITEM = tmp_storage
                    break
        else:
            self.setcostlast()
        # Нет совпадения
        if not DwgbCmdConst.ITEM:
            self.transport.writeChannel("Нет записи в реестре", message, True)
            return True
        # Отправим
        self.setcostgraph(message, True)
        # Не удалось совершить операцию
        return True

    def setcostgraph(self, message: DwgbMessage, showgraph: bool):
        """ View a graph of cost """
        tmp_url = self._API_URL % (self._ACT_TYPE_ITEM % DwgbCmdConst.ITEM.code, self.transport.api)
        try:
            tmp_response = requests.post(tmp_url, headers=self.apiHeaders())
            tmp_match = re.search("graph_data = (.+?);", tmp_response.text)
            if not tmp_match:
                self.transport.writeChannel("Нет данных для %s" % DwgbCmdConst.ITEM.id, message, True)
                return True
            tmp_params = json.loads(tmp_match[1])
            tmp_label = []
            tmp_data = []
            for tmp_param in tmp_params:
                tmp_label.append(datetime.fromtimestamp(tmp_param[0]).strftime('%H:%M'))
                tmp_data.append(tmp_param[1])
                DwgbCmdConst.ITEM.average += tmp_param[1]
            DwgbCmdConst.ITEM.average //= len(tmp_params)
            # Сейв и отправка
            if showgraph:
                plt.plot(tmp_label, tmp_data, "o-", markersize=4)
                plt.xticks(rotation=90)
                plt.rc("grid", lw=0.2)
                plt.grid(True)
                plt.savefig(self.__PLOT_IMAGE)
                plt.cla()
                self.transport.writeChannel("%s%s\nСредняя: %s, в базе: %s, сток: %s, срок: %s" % (DwgbCmdConst.ITEM.icon, DwgbCmdConst.ITEM.id.capitalize(), DwgbCmdConst.ITEM.average, DwgbCmdConst.ITEM.cost, DwgbCmdConst.ITEM.trade, (datetime.today() - DwgbCmdConst.ITEM.date).days), message, False, 120, self.__PLOT_IMAGE)
        except Exception as e:
            print("Read failed %s %s" % (e, traceback.format_exc().replace("\n", " ")))

    def setcostdb(self, cost: str):
        """ Set cost of good """
        tmp_params = []
        tmp_name = DwgbCmdConst.ITEM.id
        self.read(["цена", cost], tmp_params)
        DwgbCmdConst.ITEM = None
        # Запишем
        tmp_value = ",".join(tmp_params)
        self.database.exec(self.__QUERY_STORAGE_SET.format(tmp_value), {"owner": self.transport.getOwnerId(), "item": tmp_name})
        # Перезагрузим
        self.reloadStorages()

    def setcostlast(self):
        """ Search a last day good """
        tmp_min = datetime.max
        for tmp_key, tmp_item in DwgbCmdConst.STORE_DATA.items():
            if tmp_item.icon != "📕" and tmp_item.icon != "📘":
                continue
            if tmp_item.date < tmp_min:
                tmp_min = tmp_item.date
                DwgbCmdConst.ITEM = tmp_item

    def setcosttime(self):
        """ Time to auto showing """
        return datetime.today() + timedelta(minutes=30)

    def setcostchange(self, message: DwgbMessage):
        """ Change cost of last time good """
        self.date = self.setcosttime()
        # Установим новую цену
        self.setcostlast()
        self.setcostgraph(message, False)
        # Проверим цену
        tmp_item = DwgbCmdConst.ITEM
        if tmp_item.average <= 0:
            self.setcostdb(DwgbCmdConst.ITEM.cost)
            DwgbCmdConst.ITEM = None
            return self.transport.writeChannel("Аукцион недоступен для %s%s" % (tmp_item.icon, tmp_item.id.capitalize()), message, False)
        # Цена
        tmp_cost = str(tmp_item.average)
        self.setcostdb(tmp_cost)
        # Ответим
        self.transport.writeChannel("Установлено 🌕%s для %s%s" % (tmp_cost, tmp_item.icon, tmp_item.id.capitalize()), message, False)
        # Запросим инвентарь
        self.loadbag(message)

    def loadbag(self, message: DwgbMessage):
        """ Загрузка сумки для сверки значений """
        self.message = DwgbMessage()
        self.message.channel = self._GAME_BOT_ID
        self.transport.writeChannel("Мой инвентарь", self.message, False)
        # Сохраним для приема
        self.message.channel = message.channel

    def rebag(self, message: DwgbMessage):
        """ Проверка предметов """
        tmp_bags = self.regInventory.findall(message.text)
        tmp_item: DwgbStorage
        tmp_key: str
        tmp_dict = {}
        # Соберем с регулярки
        for tmp_bag in tmp_bags:
            tmp_dict[str(tmp_bag[0]).lower()] = int(tmp_bag[1])
        # Проверим совпадение
        for tmp_key, tmp_item in DwgbCmdConst.STORE_DATA.items():
            # Обработаем простой товар
            if tmp_key == self._ITEM_SHARDS:
                tmp_find = "осколки сердца"
            else:
                tmp_find = tmp_key
            tmp_book = "книга - " + tmp_find
            # Поищем
            if tmp_find in tmp_dict:
                tmp_count = tmp_dict[tmp_find]
            elif tmp_book in tmp_dict:
                tmp_count = tmp_dict[tmp_book]
            else:
                tmp_count = 0
            # Установим
            if tmp_item.count != tmp_count:
                self.setStorage(0, tmp_key, -tmp_item.count + tmp_count)
                self.transport.writeChannel("🐼Восстановлено количество %s для %s%s" % (tmp_count, tmp_item.icon, tmp_item.id.capitalize()), self.message, False)
            # Страница
            tmp_page = "страница - " + tmp_key
            if tmp_page in tmp_dict:
                tmp_count = math.trunc(tmp_dict[tmp_page] / 5)
            else:
                tmp_count = 0
            # Сохраним
            if tmp_item.valueex != tmp_count:
                self.setStorage(0, tmp_key, -tmp_item.valueex + tmp_count, -tmp_item.valueex + tmp_count)
                self.transport.writeChannel("🐼Восстановлены страницы %s для %s%s" % (tmp_count, tmp_item.icon, tmp_item.id.capitalize()), self.message, False)
        # Все хорошо
        return True
