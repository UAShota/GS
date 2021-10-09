"""
Displaying the balance
"""

from .command_custom import DwgbCmdCustom
from ..classes import DwgbDatabase, DwgbTransport, DwgbMessage


class DwgbCmdBaraban(DwgbCmdCustom):
    """ Команда проверки баланса """

    def __init__(self, database: DwgbDatabase, transport: DwgbTransport):
        """ Конструктор """
        super().__init__(database, transport)
        self.regGet = self.getRegex(r"Символы:(.+?)Отправьте")
        self.baraban = [
            "лен",
            "железная руда",
            "бревно",
            "камень",
            # вторичка
            "каменный блок",
            "доска",
            "железный слиток",
            "ткань",
            # ресурсы
            "пещерный корень",
            "рыбий жир",
            "камнецвет",
            "необычный цветок",
            "адский гриб",
            "адский корень",
            "чистая первозданная вода",
            "болотник",
            "кровавый гриб",
            "сквернолист",
            "чернильник",
            "корень знаний",
            "сверкающая чешуя",
            "рыбий глаз",
            "необычная ракушка",
            "камень судьбы",
            "трофей победителя",
            # активные книги
            "грязный удар",
            "слабое исцеление",
            "удар вампира",
            "мощный удар",
            "сила теней",
            "расправа",
            "слепота",
            "рассечение",
            "берсеркер",
            "таран",
            "проклятие тьмы",
            "огонек надежды",
            "целебный огонь",
            "кровотечение",
            "заражение",
            "раскол",
            # пассивные книги
            "браконьер",
            "быстрое восстановление",
            "мародер",
            "внимательность",
            "инициативность",
            "исследователь",
            "ведьмак",
            "собиратель",
            "запасливость",
            "охотник за головами",
            "подвижность",
            "упорность",
            "регенерация",
            "расчетливость",
            "ошеломление",
            "рыбак",
            "неуязвимый",
            "колющий удар",
            "бесстрашие",
            "режущий удар",
            "феникс",
            "непоколебимый",
            "суеверность",
            "гладиатор",
            "воздаяние",
            "ученик",
            "прочность",
            "расторопность",
            "устрашение",
            "контратака",
            "дробящий удар",
            "защитная стойка",
            "стойка сосредоточения",
            "водохлеб",
            "картограф",
            "парирование",
            "ловкость рук",
            "презрение к боли",
            # кольца
            "малое кольцо силы",
            "малое кольцо ловкости",
            "малое кольцо выносливости",
            "малое кольцо концентрации",
            "малое кольцо точности",
            "кольцо великана",
            "кольцо гоблина",
            "кольцо зелий",
            "кольцо навыков",
            "кольцо экипировки",
            "кольцо редкостей",
            "рунное кольцо",
            "кольцо s ранга",
            # зелья
            "зелье отравления",
            "зелье меткости",
            "зелье регенерации",
            "зелье характеристик",
            "зелье травм",
            "зелье снятия травм",
            # карты
            "карта озера",
            "карта сокровищ",
            "карта угодий",
            "карта источника",
            "карта испытания",
            "карта окрестностей",
            "карта руин"
        ]

    def work(self, message: DwgbMessage):
        """ Обработка выражения """
        tmp_match = self.regGet.search(message.text)
        if not tmp_match:
            return False
        tmp_solve = str(tmp_match[1]).strip().lower()
        tmp_len = len(tmp_solve)
        tmp_result = []
        # Добавим все слова с нашего словаря
        for tmp_name in self.baraban:
            if len(tmp_name) != tmp_len:
                continue
            tmp_wrong = False
            for tmp_i in range(0, tmp_len):
                if (tmp_solve[tmp_i] != "■") and (tmp_name[tmp_i] != tmp_solve[tmp_i]):
                    tmp_wrong = True
                    break
                if (tmp_name[tmp_i] == " ") and (tmp_name[tmp_i] != tmp_solve[tmp_i]):
                    tmp_wrong = True
                    break
            if tmp_wrong:
                continue
            tmp_result.append(tmp_name)
        # Если слов не найдено - уведомим
        if not tmp_result:
            return self.transport.writeChannel("Не знаю такого слова", message, False)
        # Отпишем примерно найденные слова
        return self.transport.writeChannel("\n".join(tmp_result), message, False, -1)
