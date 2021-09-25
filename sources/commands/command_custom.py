"""
Base command class
"""

import json
import math
import random
import re
import traceback
from urllib import parse

import requests

from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage, DwgbStorage


class DwgbCmdConst(object):
    """ Класс глобальных констант """

    # Последний обработанный элемент
    ITEM: DwgbStorage = None

    # Процент покупки
    PERCENT_BUY = 0.85

    # Процент продажи
    PERCENT_SELL = 0.90

    # Позиции склада
    STORE_DATA = {}

    # Максимальный размер текущего склада
    STORE_SIZE = 255

    # Свободных мест на складе
    STORE_FREE = 0

    # Книги
    BOOKS = [("13580", "грязный удар"),
             ("13581", "слабое исцеление"),
             ("13582", "удар вампира"),
             ("13583", "мощный удар"),
             ("13592", "сила теней"),
             ("13595", "расправа"),
             ("13600", "слепота"),
             ("13603", "рассечение"),
             ("13606", "берсеркер"),
             ("13609", "таран"),
             ("13612", "проклятие тьмы"),
             ("13615", "огонек надежды"),
             ("13619", "целебный огонь"),
             ("13623", "кровотечение"),
             ("13626", "заражение"),
             ("13628", "раскол"),
             ("13639", "быстрое восстановление"),
             ("13642", "мародер"),
             ("13644", "внимательность"),
             ("13646", "инициативность"),
             ("13648", "исследователь"),
             ("13650", "ведьмак"),
             ("13652", "собиратель"),
             ("13654", "запасливость"),
             ("13656", "охотник за головами"),
             ("13658", "подвижность"),
             ("13660", "упорность"),
             ("13662", "регенерация"),
             ("13664", "расчетливость"),
             ("13666", "презрение к боли"),
             ("13670", "рыбак"),
             ("13672", "неуязвимый"),
             ("13674", "колющий удар"),
             ("13677", "бесстрашие"),
             ("13679", "режущий удар"),
             ("13681", "феникс"),
             ("13683", "непоколебимый"),
             ("13685", "суеверность"),
             ("13687", "гладиатор"),
             ("13689", "воздаяние"),
             ("13691", "ученик"),
             ("13693", "прочность"),
             ("13695", "расторопность"),
             ("13697", "устрашение"),
             ("13699", "контратака"),
             ("14505", "дробящий удар"),
             ("14507", "защитная стойка"),
             ("14777", "стойка сосредоточения"),
             ("14779", "водохлеб"),
             ("14970", "картограф"),
             ("14972", "браконьер"),
             ("14986", "парирование"),
             ("14988", "ловкость рук"),
             ("13668", "ошеломление")]


class DwgbCmdCustom(object):
    """ Базовый класс комманд """

    # Создание таблицы хранилища
    __QUERY_STORAGE_CREATE = "CREATE TABLE IF NOT EXISTS dwgb_storages (uid SERIAL PRIMARY KEY, owner INTEGER NOT NULL, item VARCHAR (50) NOT NULL, short VARCHAR (10) DEFAULT NULL, cost INTEGER DEFAULT 0, value INTEGER DEFAULT 0, maxlimit INTEGER DEFAULT 0, trade INTEGER DEFAULT 0, valueex INTEGER DEFAULT 0, code INTEGER DEFAULT 0, date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, icon VARCHAR(4) default '🌕'); CREATE UNIQUE INDEX IF NOT EXISTS owneritem_idx ON dwgb_storages (owner, item);"

    # Сохранение количества предмета на складе
    __QUERY_STORAGE_SET = "INSERT INTO dwgb_storages (owner, item, value) VALUES (%(owner)s, %(item)s, %(value)s)  ON CONFLICT (owner, item) DO UPDATE SET value = dwgb_storages.value + %(value)s, valueex = dwgb_storages.valueex + %(valueex)s"

    # Возвращение количества предмета на складе
    __QUERY_STORAGE_GET = "SELECT value, valueex FROM dwgb_storages WHERE owner=%(owner)s AND item=%(item)s"

    # Возвращение всех параметров склада
    __QUERY_STORAGE_SHOW = "SELECT * FROM dwgb_storages WHERE owner=%(owner)s ORDER BY icon, item"

    # Возвращение определенного параметра склада
    __QUERY_STORAGE_FIND = "SELECT * FROM dwgb_storages WHERE owner=%(owner)s AND (item=%(name)s OR short=%(name)s)"

    # Параметр золота для учета транзакций
    _ITEM_GOLD = "золота"

    # Параметр осколков для учета транзакций
    _ITEM_SHARDS = "осколков сердца"

    # Параметр золота для учета транзакций
    _ITEM_PAGE = "пустая страница"

    # Идентификатор бота колодца
    _DW_BOT_ID = -183040898

    # Идентификатор игрового бота
    _GAME_BOT_ID = -182985865

    # Ссылка на рюкзак
    _API_URL = "https://vip3.activeusers.ru/app.php?act=%s&auth_key=%s&group_id=182985865&api_id=7055214"

    # Ссылка на данные предметов
    _ACT_TYPE_ITEM = "item&id=%s"

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        self.transport = transport
        self.database = database
        # Загрузим базу в первый раз
        if not DwgbCmdConst.STORE_DATA:
            self.database.exec(self.__QUERY_STORAGE_CREATE, {})
            self.reloadStorages()
        return

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        return False

    def reloadStorages(self, message: DwgbMessage = None):
        """ Перезагрузка параметров склада """
        tmp_raw = self.database.queryall(self.__QUERY_STORAGE_SHOW, {"owner": self.transport.ownerId})
        # Загрузим
        DwgbCmdConst.STORE_DATA = {}
        DwgbCmdConst.STORE_FREE = DwgbCmdConst.STORE_SIZE
        for tmp_row in tmp_raw:
            tmp_storage = self.getStorageRow(tmp_row)
            DwgbCmdConst.STORE_DATA[tmp_storage.id] = tmp_storage
            if tmp_storage.id != self._ITEM_GOLD and tmp_storage.id != self._ITEM_PAGE and tmp_storage.id != self._ITEM_SHARDS:
                DwgbCmdConst.STORE_FREE -= tmp_storage.count
        # Уведомим
        if message:
            self.transport.writeChannel("Кэш обновлен", message, True)

    def setBookPages(self, storage: DwgbStorage, count: int):
        """ Разбор книг """
        tmp_page_count = DwgbCmdConst.STORE_DATA[self._ITEM_PAGE].count
        tmp_book_count = 0
        tmp_book_id = self.getBookPresent(storage)
        if tmp_book_id:
            for tmp_i in range(0, count):
                tmp_book_count += tmp_page_count >= (tmp_book_count + 1) * 5 and self.apiSell(tmp_book_id, 1)
        # Уберем использованные страницы
        if tmp_book_count > 0:
            self.setStorage(0, self._ITEM_PAGE, -tmp_book_count * 5)
        # Увеличим в базе количество предметов
        self.setStorage(0, storage.id, count, tmp_book_count)

    def getBookPresent(self, storage: DwgbStorage):
        """ Определение книги """
        if storage.icon != "📕" and storage.icon != "📘":
            return None
        # Поищем
        for tmp_code, tmp_id in DwgbCmdConst.BOOKS:
            if storage.id == tmp_id:
                return tmp_code
        # Книга есть, но не описана
        return None

    def getAccountTag(self, peerid: int, name: str):
        """ Возвращение идентификатора отправителя """
        if peerid > 0:
            tmp_prefix = "@id"
        else:
            tmp_prefix = "@club"
        return "%s%s (%s)" % (tmp_prefix, peerid, name)

    def getRegex(self, pattern: str):
        """ Создание регулярного выражения """
        return re.compile(pattern, re.IGNORECASE | re.UNICODE | re.DOTALL | re.MULTILINE | re.S)

    def getStorageRow(self, row: dict):
        """ Разбор строки запроса """
        if row is not None:
            tmp_storage = DwgbStorage()
            tmp_storage.id = row["item"]
            tmp_storage.short = row["short"]
            tmp_storage.cost = row["cost"]
            tmp_storage.limit = row["maxlimit"]
            tmp_storage.count = row["value"]
            tmp_storage.icon = row["icon"]
            tmp_storage.trade = row["trade"]
            tmp_storage.valueex = row["valueex"]
            tmp_storage.code = row["code"]
            tmp_storage.date = row["date"]
            return tmp_storage
        else:
            return row

    def getCostIn(self, cost: int):
        """ Возвращение цены приема """
        return int(cost * DwgbCmdConst.PERCENT_BUY)

    def getCostOut(self, cost: int):
        """ Возвращение цены отправки """
        return int(cost * DwgbCmdConst.PERCENT_SELL)

    def getCostFixed(self, cost: int, vol: float = 0.9):
        """ Возвращение чистой цены перевода """
        return math.ceil(cost / vol)

    def getCostFloat(self, cost: int, vol: float = 0.9):
        """ Возвращение грязной цены перевода """
        return math.ceil(cost * vol)

    def setStorage(self, owner: int, itemid: str, value: int, valueex: int = 0):
        """ Установка количества товара на складе """
        value -= valueex
        # Для склада обновим кэш
        if not owner:
            owner = self.transport.getOwnerId()
            if itemid in DwgbCmdConst.STORE_DATA:
                tmp_data = DwgbCmdConst.STORE_DATA[itemid]
                tmp_data.count += value
                tmp_data.valueex += valueex
            # Поправим свободное место
            if itemid != self._ITEM_GOLD and itemid != self._ITEM_PAGE and itemid != self._ITEM_SHARDS:
                DwgbCmdConst.STORE_FREE -= value
        # Сохраним в базе
        self.database.exec(self.__QUERY_STORAGE_SET, {"owner": owner, "item": itemid, "value": value, "valueex": valueex})
        # Перегрузим если новый товар
        if itemid not in DwgbCmdConst.STORE_DATA:
            self.reloadStorages()

    def setBonus(self, message: DwgbMessage):
        """ Выброс бонусного лута """
        tmp_bonus = []
        for tmp_item, tmp_storage in DwgbCmdConst.STORE_DATA.items():
            if tmp_storage.icon == "🍄" and tmp_storage.count > 0:
                tmp_bonus.append(tmp_storage.id)
        # Определим
        if not tmp_bonus:
            return
        # Определим тип
        tmp_item = tmp_bonus[random.randint(0, len(tmp_bonus) - 1)]
        # Определим текст
        tmp_index = random.randint(1, 5)
        if tmp_index == 1:
            tmp_text = "🐾Вы наблюдаете как в очередной раз телега с чумазыми гоблинами врезалась в единственное дерево в поле и с нее что то выпало..."
        elif tmp_index == 2:
            tmp_text = "💥Вы наблюдаете как рыцарь в сияющих доспехах пытается вызвать босса, несмотря на прыгающих рядом гномиков. Он что то бросил им, чтобы отвлечь от себя..."
        elif tmp_index == 3:
            tmp_text = "🐷Несмотря на старания орка из таверны, снежок прилетел прямо в лоб его пугалу на лужайке города. С пугала что то отломалось и покатилось к вам..."
        elif tmp_index == 4:
            tmp_text = "👀Тараканы? У меня нет тараканов! Вы просто не замечайте их как я! Кричал управляющий местного борделя, что то кидая в вас..."
        else:
            tmp_text = "🐀'Ну ты заходи если что' - послышался в голос вдалеке - 'И за собой кого нибудь приводи, у меня лучше' - приглядевшись, вы увидели человека в маске кота с очками, который бросил своему спутнику какую-то подачку... "
        # Уменьшим в базу
        self.setStorage(0, tmp_item, -1)
        # Отправим
        self.transport.writeChannel(tmp_text, message, False, -1)
        self.transport.removeChannel(self.transport.writeChannel("Бросить %s" % tmp_item, message, False, -1))

    def getStorageItem(self, owner: int, itemid: str, onlyvalue: bool = True):
        """ Возвращение количества товара на складе """
        tmp_result = self.database.queryone(self.__QUERY_STORAGE_GET, {"owner": owner, "item": itemid})
        if tmp_result is not None:
            if onlyvalue:
                return tmp_result["value"]
            else:
                return tmp_result
        else:
            return 0

    def getStorage(self, itemtype: str):
        """ Поиск товара в базе """
        for tmp_item, tmp_storage in DwgbCmdConst.STORE_DATA.items():
            if tmp_item == itemtype:
                return tmp_storage
            if tmp_storage.short == itemtype:
                return tmp_storage
        # Ничегошеньки
        return None

    def apiQuery(self, data):
        """ Build PHP Array from JS Array """
        m_parents = list()
        m_pairs = dict()

        def renderKey(parents: list):
            """ Key decoration """
            depth, out_str = 0, ''
            for x in parents:
                s = "[%s]" if depth > 0 or isinstance(x, int) else "%s"
                out_str += s % str(x)
                depth += 1
            return out_str

        def r_urlencode(rawurl: str):
            """ Encode URL """
            if isinstance(rawurl, list) or isinstance(rawurl, tuple):
                for tmp_index in range(len(rawurl)):
                    m_parents.append(tmp_index)
                    r_urlencode(rawurl[tmp_index])
                    m_parents.pop()
            elif isinstance(rawurl, dict):
                for tmp_key, tmp_value in rawurl.items():
                    m_parents.append(tmp_key)
                    r_urlencode(tmp_value)
                    m_parents.pop()
            else:
                m_pairs[renderKey(m_parents)] = str(rawurl)
            return m_pairs

        return parse.urlencode(r_urlencode(data))

    def apiHeaders(self, lenght: int = 0, referer: str = "", host: str = "vip3.activeusers.ru"):
        """ Возвращение заголовка запроса """
        tmp_headers = {
            'Host': host,
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="90", "Chromium";v="90", ";Not A Brand";v="100"',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'DNT': '1',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/5388.36 (KHTML, like Gecko) Chrome/90.0.4389.90 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://%s' % host,
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        if lenght:
            tmp_headers['Content-Length'] = str(lenght)
        if referer:
            tmp_headers['Referer']: referer
        return tmp_headers

    def apiUse(self, itemid: str, action: int, page: str):
        """ Использование предмета """
        tmp_data = {
            "id": itemid,
            "m": action
        }
        tmp_url = self._API_URL % (page, self.transport.api)
        tmp_referer = self._API_URL % (self._ACT_TYPE_ITEM % itemid, self.transport.api)
        # Отправим
        try:
            tmp_response = requests.post(tmp_url, tmp_data, headers=self.apiHeaders(7 + len(str(itemid)), tmp_referer))
            return tmp_response.ok and json.loads(tmp_response.text)["result"] == 1
        except Exception as e:
            print("Query failed %s %s" % (e, traceback.format_exc().replace("\n", " ")))
            return False

    def apiSell(self, itemid: str, action: int):
        """ Продажа или разбор предмета """
        return self.apiUse(itemid, action, "a_sell_item")

    def apiBuy(self, itemid: str, action: int):
        """ Покупка или сбор предмета """
        return self.apiUse(itemid, action, "a_get_item")
