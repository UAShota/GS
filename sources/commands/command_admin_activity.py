"""
User activity stat
"""

from datetime import datetime

from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdAdminActivity(DwgbCmdCustom):
    """ Администрирование активности """

    #: Вывод активности
    __QUERY_ACTIVITY = "SELECT id, elite, level, date FROM dwgb_profiles WHERE date in (SELECT max(date) FROM dwgb_profiles GROUP BY id) ORDER BY date ASC"

    # Удаление активности
    __QUERY_DELETE = "DELETE FROM dwgb_profiles WHERE id=%(id)s"

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.reg_del = self.getRegex(r"^склад активность удалить (\d+)$")
        self.reg_show = self.getRegex(r"^склад активность$")

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        if (message.user != 384297286) and (message.user != 66313242):
            return False
        # Удаление
        tmp_match = self.reg_del.match(message.text)
        if tmp_match:
            return self.delete(tmp_match, message)
        # Отображение
        tmp_match = self.reg_show.match(message.text)
        if tmp_match:
            return self.show(message)
        # Ничегошеньки
        return False

    def show(self, message: DwgbMessage):
        """ Отображение """
        tmp_data = self.database.queryall(self.__QUERY_ACTIVITY, {})
        tmp_text = ""
        # Разберем
        for tmp_item in tmp_data:
            tmp_date = tmp_item["date"]
            tmp_today = datetime.today()
            # Определим светофор
            if (tmp_today - tmp_date).days <= 7:
                tmp_alert = "✅"
            elif (tmp_today - tmp_date).days <= 14:
                tmp_alert = "⚠"
            else:
                tmp_alert = "⛔"
            # Статуя
            if (tmp_today - tmp_date).days > 30:
                tmp_alert = "🗿"
            # Дату в текст
            tmp_date = tmp_date.strftime("%m.%d")
            # 100+ спрятаны
            if tmp_item["level"] >= 100:
                tmp_alert = "🦖"
                tmp_text += "%s%s [id%s|%s]\n" % (tmp_alert, tmp_date, tmp_item["id"], tmp_item["id"])
            else:
                tmp_text += "%s%s [id%s|%s] 🎄%s ☠%s\n" % (tmp_alert, tmp_date, tmp_item["id"], tmp_item["id"], tmp_item["level"], tmp_item["elite"])
        # Ответим
        self.transport.writeChannel(tmp_text, message, False, 360)
        return True

    def delete(self, match: dict, message: DwgbMessage):
        """ Отображение """
        self.database.exec(self.__QUERY_DELETE, {"id": int(match[1])})
        # Ответим
        self.transport.writeChannel("%s стёрт без сожаления" % (match[1]), message, True)
        return True
