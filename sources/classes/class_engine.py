"""
Command engine
"""
import signal
import traceback

from .class_database import DwgbDatabase
from .class_message import DwgbMessage
from .class_transport import DwgbTransport
from ..commands import DwgbCmdConsts, DwgbCmdAdminActivity, DwgbCmdBaraban, DwgbCmdFlooder, DwgbCmdAdminStorage, DwgbCmdButtons, DwgbCmdHelp, DwgbCmdProfile, DwgbCmdPapper, DwgbCmdBalance, DwgbCmdStorage, DwgbCmdTransferGold, DwgbCmdTransferItem, DwgbCmdBaf, DwgbCmdGetItem, DwgbCmdConvert, DwgbCmdTrader, DwgbCmdCustom


class DwgbEngine(object):
    """ Движок обработки команд """

    def __init__(self, vktoken: str, dbtoken: str, owner: int, api: str, channels: dict):
        """ Конструктор """
        self.database = DwgbDatabase(dbtoken)
        self.transport = DwgbTransport(self.database, vktoken, owner, api)
        self.commands = {}
        self.channels = channels
        self.registerCommands()
        self.active = True
        signal.signal(signal.SIGINT, self.onExit)
        signal.signal(signal.SIGTERM, self.onExit)

    def onExit(self, _frame: any, _signals: any):
        """ Supress SIGTERM signal """
        self.active = False

    def registerCommand(self, name: str, cmdclass: callable):
        """ Регистрация команды """
        self.commands[name] = cmdclass(self.database, self.transport)

    def registerCommands(self):
        """ Регистрация доступных команд """
        self.registerCommand(DwgbCmdConsts.ADMIN_ACTIVITY, DwgbCmdAdminActivity)
        self.registerCommand(DwgbCmdConsts.ADMIN_STORAGE, DwgbCmdAdminStorage)
        self.registerCommand(DwgbCmdConsts.BUTTONS, DwgbCmdButtons)
        self.registerCommand(DwgbCmdConsts.HELP, DwgbCmdHelp)
        self.registerCommand(DwgbCmdConsts.SAVEPROFILE, DwgbCmdProfile)
        self.registerCommand(DwgbCmdConsts.PAPPER, DwgbCmdPapper)
        self.registerCommand(DwgbCmdConsts.BALANCE, DwgbCmdBalance)
        self.registerCommand(DwgbCmdConsts.BARABAN, DwgbCmdBaraban)
        self.registerCommand(DwgbCmdConsts.STORAGE, DwgbCmdStorage)
        self.registerCommand(DwgbCmdConsts.TRANSFERGOLD, DwgbCmdTransferGold)
        self.registerCommand(DwgbCmdConsts.TRANSFERITEM, DwgbCmdTransferItem)
        self.registerCommand(DwgbCmdConsts.GETBAF, DwgbCmdBaf)
        self.registerCommand(DwgbCmdConsts.GETITEM, DwgbCmdGetItem)
        self.registerCommand(DwgbCmdConsts.CONVERT, DwgbCmdConvert)
        self.registerCommand(DwgbCmdConsts.TRADER, DwgbCmdTrader)
        self.registerCommand(DwgbCmdConsts.FLOODER, DwgbCmdFlooder)

    def exec(self, command: DwgbCmdCustom, message: DwgbMessage):
        """ Выполнение команды для сообщения """
        try:
            if self.channels[message.channel] is None:
                return self.commands[command].work(message)
            elif command in self.channels[message.channel]:
                return self.commands[command].work(message)
            else:
                return False
        except Exception as e:
            print("Exec failed %s %s" % (e, traceback.format_exc().replace("\n", " ")))
            return True

    def check(self, messages: dict):
        """ Проверка сообщений для выполнения """
        for tmp_message in messages:
            if tmp_message.channel not in self.channels:
                continue
            for tmp_cmd in self.commands:
                if self.exec(tmp_cmd, tmp_message):
                    break
        return

    def listen(self):
        """ Проверка сообщений для выполнения """
        tmp_read = self.transport.readChannels
        tmp_check = self.check
        while self.active:
            for tmp_messages in tmp_read():
                tmp_check(tmp_messages)
