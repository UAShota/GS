"""
Messenger message worker
"""

import time
import traceback

from .class_database import DwgbDatabase
from .class_message import DwgbMessage
from ..vkapi import *
from ..vkapi.longpoll import *


class DwgbTransport(object):
    """ Структура описания передачи предмета или золота """

    # Создание таблицы удаляемых сообщений
    __QUERY_MESSAGE_CREATE = "CREATE TABLE IF NOT EXISTS dwgb_messages (id integer NOT NULL," + "ts timestamp NOT NULL)"

    # Добавление сообщения в стек удаления
    __QUERY_MESSAGE_ADD = "INSERT INTO dwgb_messages VALUES (%(id)s, now() + INTERVAL '%(time)s seconds') "

    # Удаление сообщения из стека сообщений
    __QUERY_MESSAGE_DEL = "DELETE FROM dwgb_messages WHERE id in ({0})"

    # Возвращение сообщений, доступных для удаления
    __QUERY_MESSAGE_GET = "SELECT id FROM dwgb_messages WHERE ts < now() - INTERVAL '60 seconds'"

    # Создание таблицы настроек сервера
    __QUERY_SERVER_CREATE = "CREATE TABLE IF NOT EXISTS dwgb_server (key integer PRIMARY KEY," + "value integer NOT NULL)"

    # Установка таймстампа последнего сообщения
    __QUERY_SERVERTS_SET = "INSERT INTO dwgb_server VALUES (1, %(ts)s) ON CONFLICT (key) DO UPDATE SET value = %(ts)s"

    # Получение таймстампа последнего сообщения
    __QUERY_SERVERTS_GET = "SELECT value FROM dwgb_server WHERE key=1"

    def __init__(self, database: DwgbDatabase, token: str, ownerId: int, api: str):
        """ Конструктор """
        self.database = database
        self.token = token
        self.ownerId = ownerId
        self.api = api
        self.client = VkApi(token=self.token)
        self.poll = VkLongPoll(self.client)
        # Создадим таблицы
        self.database.exec(self.__QUERY_MESSAGE_CREATE, {})
        self.database.exec(self.__QUERY_SERVER_CREATE, {})
        # Определим последний слепок времени
        self.poll.ts = self.database.queryone(self.__QUERY_SERVERTS_GET, {})
        if self.poll.ts is not None:
            self.poll.ts = self.poll.ts["value"]
        return

    def getOwnerId(self):
        """ Идентификатор бота """
        return self.ownerId

    def getName(self, peerid: int, data: dict):
        """ Возвращение имени отправителя из расширенных полей сообщения """
        if peerid < 0:
            tmp_field = "groups"
        else:
            tmp_field = "profiles"
        # Проверим что есть такой
        if tmp_field not in data:
            return str(peerid)
        # Переберем доступные массивы
        for tmp_item in data[tmp_field]:
            if tmp_item["id"] != abs(peerid):
                continue
            # Определим группа или пользователь
            if peerid < 0:
                return tmp_item["name"]
            else:
                return tmp_item["first_name"] + " " + tmp_item["last_name"]
        # На случай если ничего не найдено
        return str(peerid)

    def getText(self, event: {}, data: dict):
        """ Получение текста из сообщения """
        tmp_text = event.text
        for tmp_row in data["items"]:
            if "conversation_message_id" not in tmp_row:
                continue
            if (tmp_row["conversation_message_id"] == event.raw[10]) and (len(tmp_row['fwd_messages']) > 0):
                tmp_text = "\n" + tmp_row['fwd_messages'][0]["text"]
        return tmp_text

    def readEvents(self, events: []):
        """ Запрос параметров сообщения из расширенных полей сообщения """
        tmp_messages = []
        tmp_data = self.poll.preload_message_events_data(events, 1)
        for tmp_event in events:
            tmp_message = DwgbMessage()
            if tmp_event.from_group:
                tmp_message.user = -tmp_event.group_id
            elif tmp_event.from_chat or tmp_event.from_user or tmp_event.from_me:
                tmp_message.user = tmp_event.user_id
            else:
                continue
            tmp_message.id = tmp_event.message_id
            tmp_message.channel = tmp_event.peer_id
            tmp_message.name = self.getName(tmp_message.user, tmp_data)
            tmp_message.text = self.getText(tmp_event, tmp_data)
            tmp_messages.append(tmp_message)
        return tmp_messages

    def readChannels(self):
        """ Итерация чтения каналов """
        self.clearChannel()
        tmp_events = set()
        try:
            for tmp_event in self.poll.check():
                if tmp_event.type == VkEventType.MESSAGE_NEW:
                    tmp_events.add(tmp_event)
            if tmp_events:
                yield self.readEvents(tmp_events)
            self.database.exec(self.__QUERY_SERVERTS_SET, {"ts": self.poll.ts})
        except Exception as e:
            print("Read failed %s %s" % (e, traceback.format_exc().replace("\n", " ")))
            time.sleep(3)
        return

    def writeChannel(self, text: str, message: DwgbMessage, reply: bool, lifetime: int = 0, photo: str = "", params="", client=None):
        """ Отправка сообщения """
        if not params:
            params = {
                "peer_id": message.channel,
                "message": text,
                "random_id": 0,
                "dont_parse_links": 1,
                "disable_mentions": 1
            }
        if reply:
            params["reply_to"] = message.id
        if photo:
            tmp_photo = VkUpload(self.client.get_api()).photo_messages(photo, self.getOwnerId())
            params["attachment"] = "photo%s_%s" % (tmp_photo[0]["owner_id"], tmp_photo[0]["id"])
        if not client:
            client = self.client
        tmp_id = client.method("messages.send", params)
        if lifetime >= 0:
            self.clearQueue(tmp_id, lifetime)
        # Подождем между отправками
        time.sleep(3)
        return tmp_id

    def clearQueue(self, msgid: str, lifetime: int = 0):
        """ Adding msg to queue for clearing """
        self.database.exec(self.__QUERY_MESSAGE_ADD, {"id": msgid, "time": lifetime})

    def removeChannel(self, ids: str):
        """ Очистка оставленных сообщений """
        tmp_params = {
            "message_ids": ids,
            "delete_for_all": 1
        }
        try:
            self.client.method("messages.delete", tmp_params)
        except Exception as e:
            print("Remove message failed %s %s" % (e, traceback.format_exc().replace("\n", " ")))
        return

    def clearChannel(self):
        """ Очистка оставленных сообщений """
        tmp_messages = self.database.queryall(self.__QUERY_MESSAGE_GET, {})
        if not tmp_messages:
            return
        tmp_line = ",".join(str(tmp_message["id"]) for tmp_message in tmp_messages)
        self.removeChannel(tmp_line)
        self.database.exec(self.__QUERY_MESSAGE_DEL.format(tmp_line), {})
