"""
Store and view profile progress
"""

from datetime import *

import matplotlib.pyplot as plt

from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdProfile(DwgbCmdCustom):
    """ Учет изменения профиля """

    # Создание таблицы профиля
    __QUERY_PROFILE_CREATE = "CREATE TABLE IF NOT EXISTS dwgb_profiles (" + "uid serial primary key," + "id integer NOT NULL," + "elite integer NOT NULL," + "level integer NOT NULL," + "power integer NOT NULL," + "speed integer NOT NULL," + "hp integer NOT NULL," + "funny integer NOT NULL," + "attack integer NOT NULL," + "defend integer NOT NULL," + "date timestamp NOT NULL);" + "CREATE INDEX IF NOT EXISTS id_idx ON dwgb_profiles (id);"

    # Запрос параметров профиля
    __QUERY_PROFILE_GET = "SELECT * FROM dwgb_profiles WHERE id = %(id)s ORDER BY date DESC LIMIT 1"

    # Запрос данных профиля
    __QUERY_PROFILE_SHOW = "SELECT * FROM dwgb_profiles WHERE id = %(id)s ORDER BY date ASC"

    # Добавление записи о профиле
    __QUERY_PROFILE_SET = "INSERT INTO dwgb_profiles VALUES(default, %(id)s, %(elite)s, %(level)s, %(power)s, %(speed)s, %(hp)s, %(funny)s, %(attack)s, %(defend)s, to_timestamp(%(date)s))"

    # Имя файла плоттера
    __PLOT_IMAGE = "./profilestat.png"

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.database.exec(self.__QUERY_PROFILE_CREATE, {})
        self.regGet = self.getRegex(r"^[👑]?\[id(\d+)\|(.+?)\].+?уровень : (\d+).+?👊(\d+) 🖐(\d+) ❤(\d+) 🍀(\d+) 🗡(\d+) 🛡(\d+)")
        self.regShow = self.getRegex(r"^хочу профиль$")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        # Запись профиля
        tmp_match = self.regGet.match(message.text)
        if tmp_match:
            return self.saveProfile(message, tmp_match)
        # Показ профиля
        tmp_match = self.regShow.match(message.text)
        if tmp_match:
            return self.showProfile(message)
        # Ничегошеньки
        return False

    def showProfile(self, message: DwgbMessage):
        """ Показ дампа профиля """
        tmp_data = self.database.queryall(self.__QUERY_PROFILE_SHOW, {"id": message.user})
        if not tmp_data:
            return True
        tmp_label = []
        tmp_elite = []
        tmp_level = []
        tmp_power = []
        tmp_speed = []
        tmp_hp = []
        tmp_funny = []
        tmp_attack = []
        tmp_defend = []
        # Забьем в массив
        for tmpRow in tmp_data:
            tmp_label.append(tmpRow["date"].strftime("%m.%d"))
            tmp_elite.append(tmpRow["elite"] // 10)
            tmp_level.append(tmpRow["level"])
            tmp_power.append(tmpRow["power"])
            tmp_speed.append(tmpRow["speed"])
            tmp_hp.append(tmpRow["hp"])
            tmp_funny.append(tmpRow["funny"])
            tmp_attack.append(tmpRow["attack"])
            tmp_defend.append(tmpRow["defend"])
        # Ставим точки
        plt.plot(tmp_label, tmp_elite, "o-", label="Трофеи", markersize=2)
        plt.plot(tmp_label, tmp_level, "o-", label="Уровень", markersize=2)
        plt.plot(tmp_label, tmp_power, "o-", label="Сила", markersize=2)
        plt.plot(tmp_label, tmp_speed, "o-", label="Ловкость", markersize=2)
        plt.plot(tmp_label, tmp_hp, "o-", label="Выносливость", markersize=2)
        plt.plot(tmp_label, tmp_funny, "o-", label="Удача", markersize=2)
        plt.plot(tmp_label, tmp_attack, "o-", label="Атака", markersize=2)
        plt.plot(tmp_label, tmp_defend, "o-", label="Броня", markersize=2)
        # Сейв и отправка
        plt.title(message.name)
        plt.xticks(rotation=90)
        plt.legend(loc=0, prop={'size': 8})
        plt.rc("grid", lw=0.2)
        plt.grid(True)
        plt.savefig(self.__PLOT_IMAGE)
        plt.cla()
        self.transport.writeChannel("", message, False, photo=self.__PLOT_IMAGE)
        return True

    def saveProfile(self, message: DwgbMessage, data: dict):
        """ Сохранение дампа профиля """
        if message.user != self._DW_BOT_ID:
            return True
        # Учет
        tmp_now = datetime.today()
        tmp_params = dict()
        tmp_params["elite"] = 0
        tmp_params["level"] = int(data[3])
        tmp_params["power"] = int(data[4])
        tmp_params["speed"] = int(data[5])
        tmp_params["hp"] = int(data[6])
        tmp_params["funny"] = int(data[7])
        tmp_params["attack"] = int(data[8])
        tmp_params["defend"] = int(data[9])
        tmp_params["date"] = tmp_now
        tmp_snapshot = self.database.queryone(self.__QUERY_PROFILE_GET, {"id": data[1]})
        if tmp_snapshot is None:
            tmp_snapshot = tmp_params
            self.saveData(data[1], data[2], tmp_snapshot, tmp_params, True, message)
        elif (tmp_now - tmp_snapshot["date"]).days >= 3:
            self.saveData(data[1], data[2], tmp_snapshot, tmp_params, True, message)
        else:
            self.saveData(data[1], data[2], tmp_snapshot, tmp_params, False, message)
        return True

    def saveData(self, peerid: str, name: str, snapshot: dict, params: dict, save: bool, message: DwgbMessage):
        """ Запись профиля в базу """
        if save:
            self.database.exec(self.__QUERY_PROFILE_SET, {"id": peerid, "elite": params["elite"], "level": params["level"], "power": params["power"], "speed": params["speed"], "hp": params["hp"], "funny": params["funny"], "attack": params["attack"], "defend": params["defend"], "date": params["date"].timestamp()})
            tmp_text = "🏁 Реестр обновлен. "
            tmp_time = -1
        else:
            tmp_text = ""
            tmp_time = 0
        tmp_text += self.getAccountTag(int(peerid), name) + ", последний учет: " + snapshot["date"].strftime("%Y.%m.%d %H:%M") + "\n"
        tmp_text += self.getBlock("☠", params["elite"], snapshot["elite"])
        tmp_text += self.getBlock("🎄", params["level"], snapshot["level"])
        tmp_text += self.getBlock("👊", params["power"], snapshot["power"])
        tmp_text += self.getBlock("🖐", params["speed"], snapshot["speed"])
        tmp_text += self.getBlock("❤", params["hp"], snapshot["hp"])
        tmp_text += self.getBlock("🍀", params["funny"], snapshot["funny"])
        tmp_text += self.getBlock("🗡", params["attack"], snapshot["attack"])
        tmp_text += self.getBlock("🛡", params["defend"], snapshot["defend"])
        self.transport.writeChannel(tmp_text, message, False, tmp_time)

    def getBlock(self, icon: str, newValue: int, oldValue: int):
        """ Получение блока параметра """
        tmp_value = newValue - oldValue
        tmp_text = icon + str(newValue)
        if tmp_value > 0:
            tmp_text += "(+" + str(tmp_value) + ")"
        elif tmp_value < 0:
            tmp_text += "(" + str(tmp_value) + ")"
        return tmp_text + " "
