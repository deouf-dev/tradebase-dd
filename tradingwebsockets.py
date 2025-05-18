import websockets, json, asyncio #type: ignore
import random


class TradingWebsocket:
    def __init__(self, tradingClient):
        self.websocket_url = "wss://stream.binance.com:9443/ws";
        self.tradingClient = tradingClient;
        self.isRunning = False;



    async def connect(self):
        if self.isRunning:
            return;
        print("Connexion en cours avec le websocket de Binance.")
        self.parseUrl()
        async with websockets.connect(self.websocket_url, ping_interval=10, ping_timeout=15) as websocket:
            self.isRunning = True;
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                self.tradingClient.interface.root.after(0, self.tradingClient.interface.updateCrypto, data["s"], data["c"])


    async def fakeWebsocket(self):
        print("Faux websocket actif, génération de fausses variations de crypto.")
        while True:
            self.cryptos = self.tradingClient.currentUser["listenedCryptos"]
            for cryptoName in self.cryptos:
                oldPrice = self.tradingClient.database.getOldPrice(cryptoName)
                variation = random.uniform(-1, 1.5)
                price = max(0, oldPrice * (1 + variation / 100))
                self.tradingClient.interface.root.after(0, self.tradingClient.interface.updateCrypto, cryptoName, price)

            await asyncio.sleep(1)
                

    def parseUrl(self):
        for crypto in self.tradingClient.interface.cryptoList:
            self.websocket_url = f"{self.websocket_url}/{crypto.lower()}@ticker"



    def start(self, fake=False):
        loop = asyncio.new_event_loop()
        self.loop = loop
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect() if not fake else self.fakeWebsocket())
    
        

        



