"""
Request the item
"""

from .command_custom import DwgbCmdCustom, DwgbCmdConst
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage, DwgbStorage


class DwgbCmdGetItem(DwgbCmdCustom):
    """ Запрос на получение предмета или золота """

    # Размер овердрафта
    __OVERDRAFT = 3000

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regGet = self.getRegex(r"^хочу (\d+)?(\D+)")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        tmp_data = self.regGet.match(message.text)
        if not tmp_data:
            return False
        # Учет количества
        if not tmp_data[1]:
            tmp_count = 1
        else:
            tmp_count = int(tmp_data[1])
        # Определим тип предмета и найдем его в базе
        tmp_type = tmp_data[2].strip().lower()
        tmp_item = self.getStorage(tmp_type)
        # Если предмет не найден, орудуем только описанием
        if tmp_item is not None:
            tmp_type = tmp_item.id
        # Передача золота отличается от передачи предмета
        if tmp_type == self._ITEM_GOLD:
            return self.getGold(message, tmp_item, tmp_count)
        if tmp_type == self._ITEM_SHARDS:
            return self.getShards(message, tmp_item, tmp_count)
        else:
            return self.getItem(message, tmp_item, tmp_type, tmp_count)

    def getGold(self, message: DwgbMessage, _item: DwgbStorage, _count: int):
        """ Передача золота """
        self.transport.writeChannel("😢В связи с ленью игроков продавать на ауке, выдача золота временно ограничена, используйте бартер", message, True)
        return True
        # Если золото есть - снимем
        # count = min(count - self.__MINCOUNT, self.getStorageItem(message.user, type))
        # Запретим передачу если мало на складе
        # if (count <= 0):
        #     self.transport.writeChannel("%s, нет средств. Но вы держитесь." % (self.getAccountTag(message.user, message.name)), message, False)
        # else:
        #     self.transport.writeChannel("Передать %s %s" % (count, type), message, True)
        # return True

    def getShards(self, message: DwgbMessage, item: DwgbStorage, count: int):
        """ Передача осколков """
        # Если золото есть - снимем
        count = min(count, item.count)
        tmp_cost = item.cost * count // 100
        tmp_have = self.getStorageItem(message.user, self._ITEM_GOLD)
        # Запретим передачу если мало на складе
        if tmp_have < tmp_cost:
            self.transport.writeChannel("%s, нехватка средств 🌕%s для покупки %s %s за 🌕%s (%s за 100шт)" % (self.getAccountTag(message.user, message.name), tmp_have, count, item.id, tmp_cost, item.cost), message, False)
        else:
            self.transport.writeChannel("Передать %s осколков" % count, message, True)
        return True

    def getItem(self, message: DwgbMessage, storage: DwgbStorage, itemtype: str, count: int):
        """ Передача предмета """
        if storage:
            if storage.valueex > 0:
                count = min(DwgbCmdConst.STORE_FREE, min(5, min(count, storage.count + storage.valueex)))
            else:
                count = min(count, storage.count)
        else:
            count = 0
        # Нет в наличии
        if count <= 0:
            if storage and (storage.valueex > 0):
                self.transport.writeChannel("👝 на складе недостаточно мест для сбора книг", message, False)
            else:
                self.transport.writeChannel("👝 %s нет в наличии" % itemtype, message, False)
            return True
        # Предмет не описан а базе
        if not storage.cost:
            self.transport.writeChannel("Передать %s - %s штук" % (itemtype, count), message, True)
            return True
        # Определим наличие
        tmp_have = self.getStorageItem(message.user, self._ITEM_GOLD)
        tmp_cost = count * self.getCostOut(storage.cost)
        # Нехватка средств
        if tmp_cost > tmp_have + self.__OVERDRAFT:
            self.transport.writeChannel("%s, нехватка средств 🌕%s для покупки %s %s за 🌕%s (%s за шт)" % (self.getAccountTag(message.user, message.name), tmp_have, count, storage.id, tmp_cost, self.getCostOut(storage.cost)), message, False)
            return True
        # Соберем книги если надо
        if count > storage.count:
            tmp_book_id = self.getBookPresent(storage)
            if tmp_book_id:
                tmp_book_count = 0
                # Соберем книги по одной
                for tmp_i in range(0, min(count - storage.count, storage.valueex)):
                    tmp_book_count += self.apiBuy(tmp_book_id, 0)
                # Уменьшим в базе количество страничных книг
                if tmp_book_count > 0:
                    self.setStorage(0, storage.id, 0, -tmp_book_count)
                    self.setStorage(0, self._ITEM_GOLD, -300 * tmp_book_count)
        # Хватка средств
        self.transport.writeChannel("Передать %s - %s штук" % (storage.id, count), message, True)
        return True
