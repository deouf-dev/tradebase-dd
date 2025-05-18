import mysql.connector #type: ignore
import json
import random
import time


class Database:
    def __init__(self, trading):

        self._databaseData = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "trading"
        }
        self.trading = trading;
        self._databaseConnection = None;
        self.cryptos = {}
        self.users = {}

    def connect(self):
        self._databaseConnection = mysql.connector.connect(
            host = self._databaseData["host"],
            user = self._databaseData["user"],
            password = self._databaseData["password"],
            database = self._databaseData["database"]
        )
        self.cursor = self._databaseConnection.cursor(dictionary=True)
        self._initTable();
        self._updateDatas();


    def disconnect(self):
        self.cursor.close();
        self._databaseConnection.close();
    

    def reconnect(self):
        self.disconnect();
        self.connect();


    def _initTable(self):
        # Table users
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, password VARCHAR(100), budget DECIMAL(10,2), listenedCryptos JSON DEFAULT NULL, investments JSON DEFAULT NULL, history JSON DEFAULT NULL)")
        # Table cryptos (global)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS cryptos(cryptoName VARCHAR(50) NOT NULL UNIQUE, oldPrice DECIMAL(18,8) DEFAULT 1000.00)")
    

    def _updateDatas(self):
        self.cursor.execute("SELECT * FROM users")
        users = self.cursor.fetchall()
        self.users = {user["id"]: user for user in users}

        self.cursor.execute("SELECT * FROM cryptos")
        cryptos = self.cursor.fetchall()
        self.cryptos = {crypto["cryptoName"]: crypto for crypto in cryptos}



    def _getFieldsAndValues(self, datas):
        fields = []
        values = []

        for (key, value) in datas.items():
            fields.append(f"{key}")
            if isinstance(value, (list, dict)): #Convetir en JSON pour mysql
                values.append(json.dumps(value))
            else:
                values.append(value)
        
        return (fields, values)
    
    def editUser(self, id, datas):
        user = self.getUser({"id": id})
        if user == []: return None
        user = user[0]
        datas = {**user, **datas}

        fields, values = self._getFieldsAndValues(datas)
        fields = ", ".join([f"{key} = %s" for key in fields])

        query = f"UPDATE users SET {fields} WHERE id = {id}"
        self.cursor.execute(query, values)
        self._databaseConnection.commit()
        return self.getUser(datas)
        
    def addCryptoListener(self, cryptoName):
        currentUser = self.trading.currentUser
        listenedCryptos = currentUser["listenedCryptos"]
        if not cryptoName in listenedCryptos:
            listenedCryptos.append(cryptoName)
            self.editUser(currentUser["id"], {"listenedCryptos": listenedCryptos})
            self.trading.currentUser["listenedCryptos"] = listenedCryptos
            self.trading.interface.createCryptoSection(self.trading.interface.cryptoList[cryptoName])

    def removeCryptoListener(self, cryptoName):
        currentUser = self.trading.currentUser
        listenedCryptos = currentUser["listenedCryptos"]
        if  cryptoName in listenedCryptos:
            listenedCryptos.remove(cryptoName)
            self.editUser(currentUser["id"], {"listenedCryptos": listenedCryptos})
            self.trading.currentUser["listenedCryptos"] = listenedCryptos

        

    def createUser(self, datas):
        (fields, values) = self._getFieldsAndValues(datas)
        if self._usernameExists(datas["username"]):
            return (False,"Nom d'utilisateur non disponible!")
        query = f"INSERT INTO users ({', '.join(fields)}) VALUES ({', '.join(['%s'] * len(fields))})"
        self.cursor.execute(query, values)
        self._databaseConnection.commit()
        self._updateDatas();
        return (True, self.getUser({"username": datas["username"]})[0])
    

    def _usernameExists(self, username):
        values = self.users.values();
        for datas in values: 
            if datas["username"] == username:
                return True;
        return False;



    def getUser(self, datas):
        #Création de conditions dynamiques en fonction des données passés dans le paramètre datas
        conditions = " AND ".join([f"{key} = %s" for key in datas.keys()])
        values = tuple(
        json.dumps(v) if isinstance(v, (list, dict)) else v
        for v in datas.values()
        )
        query = f"SELECT * FROM users WHERE {conditions}"
        self.cursor.execute(query, values)

        return self.cursor.fetchall()
    
    def setCurrentUser(self, userDatas):
        userDatas["listenedCryptos"] = json.loads(userDatas["listenedCryptos"]) if isinstance(userDatas["listenedCryptos"], (bytes, bytearray, str)) else userDatas["listenedCryptos"]
        userDatas["investments"] = json.loads(userDatas["investments"]) if isinstance(userDatas["investments"], (bytes, bytearray, str)) else userDatas["investments"] or []
        userDatas["history"] = json.loads(userDatas["history"]) if isinstance(userDatas["history"], (bytes, bytearray, str)) else userDatas["history"] or []
        self.trading.currentUser = userDatas 


    def editCryptoValue(self, cryptoName, value):
        if not cryptoName in self.cryptos: self.cryptos[cryptoName] = {}

        self.cryptos[cryptoName]["oldPrice"] = value
        query = """
                INSERT INTO cryptos (cryptoName, oldPrice)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE oldPrice = VALUES(oldPrice);
                """
        self.cursor.execute(query, (cryptoName, value))
        self._databaseConnection.commit()



        
    def getOldPrice(self, cryptoName):
        if cryptoName in self.cryptos:
            return float(self.cryptos[cryptoName]["oldPrice"])
        else:
            return self.trading.interface.cryptoList[cryptoName]["oldPrice"]
        


    def addInvestment(self, cryptoName, amount, current):
        self.trading.currentUser["investments"].append([cryptoName, amount, current])
        self.trading.currentUser["budget"] = float(self.trading.currentUser["budget"]) - amount
        self.trading.currentUser["history"].append([0, cryptoName, round(amount, 2), time.time()])
        self.editUser(self.trading.currentUser["id"], {"investments": self.trading.currentUser["investments"], "budget": self.trading.currentUser["budget"], "history": self.trading.currentUser["history"]})

    
    def removeInvestment(self, cryptoName):
        inv = self.trading.currentUser["investments"]
        invested = self.trading.getInvested(cryptoName)
        amount = self.trading.simulateInvest(cryptoName)

        self.trading.currentUser["investments"] = [i for i in inv if i[0] != cryptoName]
        self.trading.currentUser["budget"] = float(self.trading.currentUser["budget"]) + amount + invested
        self.trading.currentUser["history"].append([1, cryptoName, round(amount, 2), time.time()])
        self.editUser(self.trading.currentUser["id"], {"investments": self.trading.currentUser["investments"], "budget": self.trading.currentUser["budget"], "history": self.trading.currentUser["history"]})
        