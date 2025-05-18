import threading
import math
from tradingwebsockets import TradingWebsocket
from interface import Interface
from tkinter import simpledialog
from database import Database


class Trading:
    def __init__(self, fakeWebsocket=False):
        self.fakeWebsocket = fakeWebsocket
        self.database = Database(self);
        self.websocket = TradingWebsocket(self)
        self.interface = Interface(self)

    def initApp(self):
        self.initDatabase()
        self.interface.launch()

    def connectWebsocket(self):
        threading.Thread(target=self.websocket.start, kwargs={"fake": self.fakeWebsocket}, daemon=True).start()

    def initDatabase(self):
        self.database.connect();


    def startInvest(self, crypto):
        amount = simpledialog.askfloat(
            "Investir", f"Combien voulez-vous investir dans {crypto} ?", minvalue=1, maxvalue=self.currentUser["budget"]
        )
        if amount is not None:
            self.database.addInvestment(crypto, amount, self.database.getOldPrice(crypto))
            self.interface.updateBalanceRest()
            self.interface.addDivestButton(crypto)

    def endInvest(self, crypto):
        self.database.removeInvestment(crypto)
        self.interface.updateBalanceRest()
        self.interface.updateBalanceInvest()
        self.interface.removeDivestButton(crypto)

    def simulateInvest(self, crypto="all"):
        amount = 0
        investments = [i for i in self.currentUser["investments"] if crypto == "all" or i[0] == crypto]

        for i in investments:
            current = self.database.getOldPrice(i[0])
            amount += i[1] * ((current / i[2]) - 1)

        return math.floor(amount * 100) / 100

    def getInvested(self, crypto="all"):
        if crypto != "all":
            for i in self.currentUser["investments"]:
                if i[0] == crypto:
                    return i[1]
        else:
            return sum(i[1] for i in self.currentUser["investments"])
        return []
