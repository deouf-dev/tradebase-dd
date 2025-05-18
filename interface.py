import tkinter as tk
import math
from PIL import Image, ImageTk #type: ignore
from graphs import showgraph
import requests
import re
import io
from datetime import datetime

class Interface:
    def __init__(self, trading):
        self.root = tk.Tk()
        self.trading = trading

        self.frame_balance = {}
        self.cryptoPrice = {}
        self.cryptoFrame = {}

        self.cryptoContainer = tk.Frame(self.root, bg="#222222")
        self.disinvestButtons = {}

        self.cryptosIcons = {}
        self.deleteBtnImage = ImageTk.PhotoImage(Image.open("addons/delete_btn.png").resize((25, 30)))

        self.fetchCryptos()


        

    def launch(self):
        # Créer la fenêtre principale
        self.root.title("TradeBase DD")
        self.root.config(bg="#222222")

        # Centrer la fenetre au millieu de l'écran
        screenWidth = self.root.winfo_screenwidth()
        screenHeight = self.root.winfo_screenheight()

        x = int((screenWidth - 600) / 2)
        y = int((screenHeight - 600) / 2)
        self.root.geometry(f"600x600+{x}+{y}")
        self.loginPage()

        self.initInterface()
        tk.mainloop()




    def initInterface(self):
        # Label principal (titre)
        tk.Label(self.root, text="TradeBase DD", font=("Helvetica", 16, "bold"), bg="#222222", fg="gold").pack(pady=10)
        
        #Boutons d'actions:
        actionFrame = tk.Frame(self.root, bg="#222222")
        actionFrame.pack(anchor="e", padx=10, pady=5)

        tk.Button(actionFrame,
                text="Historique",
                command=self.openHistory,
                bg="#222222", fg="white",
                width=12).pack(side="left", padx=5)

        tk.Button(actionFrame,
                text="Déconnexion",
                command=self.logout,
                bg="#222222", fg="red",
                width=12).pack(side="left", padx=5)

        # Infos Soldes
        frame_balance = tk.Frame(self.root, bg="#222222")
        frame_balance.pack(pady=10)
        rest = tk.Label(frame_balance, text=f"Solde Restant : {self.trading.currentUser['budget']}", font=("Helvetica", 16), bg="#222222", fg="blue")
        rest.grid(row=0, column=0, sticky="w")

        inv = tk.Label(frame_balance, text="Calcul...", font=("Helvetica", 16), bg="#222222", fg="white")
        inv.grid(row=1, column=0, sticky="w")

        total = tk.Label(frame_balance, text="Calcul...", font=("Helvetica", 16, "bold"), bg="#222222", fg="gold")
        total.grid(row=2, column=0, sticky="w")

        self.frame_balance = {"rest": rest, "inv": inv, "total": total}


        self.cryptoContainer.pack()
        # Sections pour chaque crypto
        for crypto in self.trading.currentUser["listenedCryptos"]:
            crypto = self.cryptoList[crypto]
            self.createCryptoSection(crypto)

        # Lancer l'application
        self.checkIfInvestedAndAddBtn()
        


    def loginPage(self):
        loginWindow = tk.Toplevel(self.root)
        self.loginWindow = loginWindow
        loginWindow.config(bg="#222222")
        loginWindow.title("Connexion")
        loginWindow.grab_set()
        loginWindow.transient(self.root)

        # Centrer le popup sur la fenetre root
        loginWindow.geometry(self.centerPopUp(300,200))

        tk.Label(loginWindow, text="Nom d'utilisateur", bg="#222222", fg="white").pack(pady=5)
        username = tk.Entry(loginWindow, bg="#222222", fg="white")
        username.focus()
        username.pack()

        tk.Label(loginWindow, text="Mot de passe", bg="#222222", fg="white").pack(pady=5)
        password = tk.Entry(loginWindow, show="*", bg="#222222", fg="white")
        password.pack()

        def login(event=None):
            self.checkIdentity(username.get(), password.get())

        btn_frame = tk.Frame(loginWindow, bg="#222222")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Se connecter", command=login, bg="#222222", fg="white").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Créer un compte", command=self.signUpPage, bg="#222222", fg="white").pack(side="left", padx=10)
        loginWindow.bind("<Return>", login)
        # Fermer tout si l'utilisateur ne se connecte pas
        loginWindow.protocol("WM_DELETE_WINDOW", self.root.destroy)
        loginWindow.wait_window()
        self.trading.connectWebsocket()

    def signUpPage(self):
        self.loginWindow.destroy()
        signUpWindow = tk.Toplevel(self.root)
        signUpWindow.title("Créer un compte")
        signUpWindow.geometry("350x350")
        signUpWindow.config(bg="#222222")
        signUpWindow.grab_set()
        signUpWindow.transient(self.root)

        # Centrer la fenêtre sur la fenetre root
        signUpWindow.geometry(self.centerPopUp(350,350))

        tk.Label(signUpWindow, text="Nom d'utilisateur", bg="#222222", fg="white").pack(pady=5)
        username = tk.Entry(signUpWindow, bg="#222222", fg="white")
        username.focus()
        username.pack()

        tk.Label(signUpWindow, text="Budget de départ", bg="#222222", fg="white").pack(pady=5)
        budget = tk.Entry(signUpWindow, bg="#222222", fg="white")
        budget.pack()

        tk.Label(signUpWindow, text="Mot de passe", bg="#222222", fg="white").pack(pady=5)
        password = tk.Entry(signUpWindow, show="*", bg="#222222", fg="white")
        password.pack()

        tk.Label(signUpWindow, text="Confirmation du mot de passe", bg="#222222", fg="white").pack(pady=5)
        passwordConfirmation = tk.Entry(signUpWindow, show="*", bg="#222222", fg="white")
        passwordConfirmation.pack()

        def isFloat(str):
            try:
                float(str)
                return True
            except ValueError:
                return False

        def signUp(event=None):
            if not password.get() == passwordConfirmation.get():
                tk.messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas!")
            if not isFloat(budget.get()):
                tk.messagebox.showerror("Erreur", "Le budget doit être un chiffre!")

            createdUser = self.trading.database.createUser({
                "username": username.get(),
                "password": password.get(),
                "listenedCryptos": ["BTCUSDT", "ETHUSDT", "DOGEUSDT"],
                "investments": [],
                "budget": float(budget.get()),
                "history": []
            })

            if not createdUser[0]:
                tk.messagebox.showerror("Erreur", createdUser[1])
            else:
                self.trading.database.setCurrentUser(createdUser[1])
                signUpWindow.destroy()

        def backToLogin():
            signUpWindow.destroy()
            self.loginPage()

        btn_frame = tk.Frame(signUpWindow, bg="#222222")
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Créer son compte", command=signUp, bg="#222222", fg="white").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Retour à la connexion", command=backToLogin, bg="#222222", fg="white").pack(side="left", padx=10)

        signUpWindow.bind("<Return>", signUp)
        # Fermer tout si l'utilisateur ne crée pas de compte
        signUpWindow.protocol("WM_DELETE_WINDOW", self.root.destroy)
        signUpWindow.wait_window()
    

    def logout(self):
        self.trading.currentUser = None
        self.clearInterface()
        self.loginPage()

        self.cryptoContainer = tk.Frame(self.root, bg="#222222")
        self.initInterface()
        
        pass;

    def openHistory(self):
            history = self.trading.currentUser["history"]
            historyPage = tk.Toplevel(self.root)
            historyPage.title("Historique de transactions")
            historyPage.grab_set()
            historyPage.geometry(self.centerPopUp(500, 500))

            historyFrame = tk.Frame(historyPage)
            historyFrame.pack(fill=tk.BOTH, expand=True)

            canvas = tk.Canvas(historyFrame, bg="#222222", highlightthickness=0)
            scrollbar = tk.Scrollbar(historyFrame, orient=tk.VERTICAL, command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollableFrame = tk.Frame(canvas, bg="#222222")
            scrollableWindow = canvas.create_window((0, 0), window=scrollableFrame, anchor="nw")

            def resizeFrame(event):
                canvas.itemconfig(scrollableWindow, width=event.width)

            scrollableFrame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.bind("<Configure>", resizeFrame)

            #Bout de code généré par IA pour le scroll
            def onMouseWheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            scrollableFrame.bind_all("<MouseWheel>", onMouseWheel)
            scrollableFrame.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            scrollableFrame.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units")) 

            buttonFrame = tk.Frame(historyPage, bg="#333333")
            buttonFrame.pack(fill=tk.X)

            self.historySort = "Date"
            self.historyReverse = False
            self.historyFilter = "Tout"

            def sortAndRefresh(by):
                if by == self.historySort:
                    self.historyReverse = not self.historyReverse
                else:
                    self.historySort = by
                    self.historyReverse = False

                if by == "Date":
                    keyIndex = 3
                elif by == "Montant":
                    keyIndex = 2
                else:
                    keyIndex = 3
                
                history.sort(key=lambda x: x[keyIndex], reverse=self.historyReverse)

                for widget in scrollableFrame.winfo_children():
                    widget.destroy()

                for tx in history:
                    operation, cryptoName, gain, timestamp = tx

                    if self.historyFilter == "Vente" and operation == 0:
                        continue
                    if self.historyFilter == "Achat" and operation == 1:
                        continue

                    isBuy = (operation == 0)
                    icon = self.getIcon(cryptoName)
                    self.cryptosIcons[cryptoName] = icon

                    dateStr = datetime.fromtimestamp(timestamp).strftime('%d/%m/%y')
                    if isBuy:
                        bgColor = "#3366cc"
                        labelText = f"Achat: {cryptoName} - {gain:.2f}$ ({dateStr})"
                    else:
                        bgColor = "#33cc33" if gain > 0 else "#cc3333"
                        sign = "+" if gain >= 0 else ""
                        labelText = f"Vente: {cryptoName} - {sign}{gain:.2f}$ ({dateStr})"

                    txFrame = tk.Frame(scrollableFrame, bg=bgColor, pady=5)
                    txFrame.pack(fill=tk.X, expand=True, padx=10, pady=5)

                    iconLabel = tk.Label(txFrame, image=icon, bg=bgColor)
                    iconLabel.pack(side=tk.LEFT, padx=5)

                    textLabel = tk.Label(txFrame, text=labelText, fg="white", bg=bgColor, anchor="w")
                    textLabel.pack(side=tk.LEFT, padx=10)

            def handleButton(k):
                if not k in ["Date", "Montant"]:
                    self.historyFilter = k
                    for btn in buttonFrame.winfo_children():
                        if btn.cget("text") == k:
                            btn.config(state=tk.DISABLED, bg="#555555")
                        else:
                            btn.config(state=tk.NORMAL, bg="#222222")
                sortAndRefresh(k)
                    


            for key in ["Date", "Montant", "Tout", "Vente", "Achat"]:
                sortButton = tk.Button(buttonFrame, text=key, command=lambda k=key: handleButton(k),
                                    bg="#222222", fg="white")
                sortButton.pack(side=tk.LEFT, padx=5, pady=5)

            sortAndRefresh(self.historySort)
            historyPage.protocol("WM_DELETE_WINDOW", historyPage.destroy)







    def clearInterface(self):
        for widget in self.root.winfo_children():
            widget.destroy()


    def checkIdentity(self, username, password):
        if username == "":
            return tk.messagebox.showerror("Erreur de connexion", "Veuillez indiquer un nom d'utilisateur!")
        if password == "":
            return tk.messagebox.showerror("Erreur de connexion", "Veuillez indiquer un mot de passe!")
        for key in self.trading.database.users.keys():
            user = self.trading.database.users[key]
            if user["username"] == username and user["password"] == password:
                self.trading.database.setCurrentUser(user)
                self.loginWindow.destroy()
                del self.loginWindow
                return
        tk.messagebox.showerror("Erreur de connexion", "Nom d'utilisateur ou mot de passe incorrect.")

    def createCryptoSection(self, cryptoData):
        crypto = cryptoData["symbol"]
        frame = tk.Frame(self.cryptoContainer, bd=2, relief="groove", padx=10, pady=10, bg="#222222")
        self.cryptoFrame[crypto] = frame
        frame.pack(fill="x", expand=True)
        
        self.cryptosIcons[crypto] = self.getIcon(crypto)

        # Configuration des colonnes pour aligner les boutons à droite
        frame.columnconfigure(0, weight=1)  # Icône
        frame.columnconfigure(1, weight=1)  # Nom de la crypto
        frame.columnconfigure(2, weight=1)  # Prix
        frame.columnconfigure(3, weight=1)  # Espace
        frame.columnconfigure(4, weight=1)  # Boutons

        # Icône de la crypto
        tk.Label(frame, image=self.cryptosIcons[crypto], bg="#222222").grid(row=0, column=0, sticky="w")

        # Bouton pour supprimer une crypto
        deleteBtn = tk.Button(frame, image=self.deleteBtnImage, font=("Helvetica", 10, "bold"), bg="#222222", fg="red", command=lambda c=crypto: self.deleteCryptoButton(c), borderwidth=0, highlightthickness=0, activebackground="#222222")
        deleteBtn.grid(row=1, column=0, sticky="w")
        frame.after(100, deleteBtn.grid_remove)

        # Afficher / cacher le bouton au survol
        def show_button(event):
            deleteBtn.grid()

        def hide_button(event):
            deleteBtn.grid_remove()

        frame.bind("<Enter>", show_button)
        frame.bind("<Leave>", hide_button)
        deleteBtn.bind("<Enter>", show_button)
        deleteBtn.bind("<Leave>", hide_button)

        # Nom de la crypto
        tk.Label(frame, text=crypto[:-4], font=("Helvetica", 18, "bold"), bg="#222222", fg="gold").grid(row=0, column=1, sticky="w")

        # Label du prix
        label = tk.Label(frame, text="Connexion en cours...", font=("Helvetica", 16), fg="green", bg="#222222", width=20)
        label.grid(row=1, column=1, sticky="w", pady=5)
        self.cryptoPrice[crypto] = label

        # Boutons
        tk.Button(frame, text="Graphique", command=lambda: showgraph(self, crypto), width=15, bg="#222222", fg="white").grid(row=0, column=1, padx=10, sticky="e")
        tk.Button(frame, text="Investir", command=lambda: self.trading.startInvest(crypto), width=15, bg="#222222", fg="white").grid(row=0, column=5, padx=10, sticky="e")

        disbtn = tk.Button(frame, text="Récupérer", command=lambda: self.trading.endInvest(crypto), width=15, bg="#222222", fg="white")
        disbtn.grid(row=1, column=5, padx=10, sticky="e", columnspan=3)
        disbtn.grid_remove()

        self.disinvestButtons[crypto] = disbtn

        addCryptoBtn = tk.Button(self.root, text="Ajouter une crypto", command= lambda: self.addCryptoButton(), bg="#222222", fg="white")
        addCryptoBtn.place(relx=0.5, rely=1.0, anchor="s", y=-10)




    def addCryptoButton(self):
        newCryptoPage = tk.Toplevel(self.root)
        newCryptoPage.title("Ajouter une nouvelle crypto")
        newCryptoPage.grab_set()
        newCryptoPage.config(bg="#222222")
        newCryptoPage.transient(self.root)
        newCryptoPage.geometry(self.centerPopUp(450,500))
        tk.Label(newCryptoPage, text="Rechercher une crypto:")

        entryVar = tk.StringVar()
        entry = tk.Entry(newCryptoPage, textvariable=entryVar, bg="#222222", fg="white")
        entry.pack(pady=5)
        entry.focus()
        
        frame = tk.Frame(newCryptoPage, bg="#222222")
        frame.pack(fill=tk.BOTH, expand=True, padx=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, height=10, yscrollcommand=scrollbar.set, bg="#222222", fg="white")
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=listbox.yview)

        def updateListbox(*args):
            search = entryVar.get().lower()
            listbox.delete(0, tk.END)
            for cryptoKey in self.cryptoList:
                crypto = self.cryptoList[cryptoKey]
                if search in crypto["name"].lower() or search in crypto["symbol"].lower():
                    listbox.insert(tk.END, f"[{crypto['symbol'].upper()[:-4]}] {crypto['name']} ({crypto['price']}$)")

        entryVar.trace_add("write", updateListbox)
        updateListbox()

        def onSelect(*args):
            try:
                index = listbox.curselection()[0]
                selected = listbox.get(index)
            except IndexError:
                selected = entryVar.get()

            match = re.search(r"\[(.*?)\]", selected) #regex généré par IA afin d'extraire le symbole de la crypto entre []
            symbol = match.group(1).upper()
            cryptoSelected = self.cryptoList[f"{symbol}USDT"]
            self.trading.database.addCryptoListener(cryptoSelected["symbol"])

            newCryptoPage.destroy()
        listbox.bind("<Double-Button-1>", onSelect)




    def fetchCryptos(self):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd", 
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": False
        }

        response = requests.get(url, params=params)
        data = response.json()

        self.cryptoList = {
            f'{coin["symbol"].upper()}USDT': {
                "symbol": f"{coin['symbol']}USDT".upper(),
                "name": coin["name"],
                "image": coin["image"],
                "price": coin["current_price"] 
            }
            for coin in data
        }
    


    def getIcon(self, cryptoName):
        if self.cryptosIcons.get(cryptoName):
            return self.cryptosIcons[cryptoName]
        crypto = self.cryptoList[cryptoName]
        iconData = requests.get(crypto["image"]).content
        icon = Image.open(io.BytesIO(iconData))
        icon = icon.resize((30, 30))
        icon = ImageTk.PhotoImage(icon)
        return icon


    def centerPopUp(self, w,h):
        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        x = root_x + (root_width // 2) - (w // 2)
        y = root_y + (root_height // 2) - (h // 2)
        return f"{w}x{h}+{x}+{y}"

    def deleteCryptoButton(self, crypto):
        for i in self.trading.currentUser["investments"]:
            if i[0] == crypto:
                return tk.messagebox.showerror("Erreur", "Veuillez récupérer votre investissement!")
        self.trading.database.removeCryptoListener(crypto)
        self.cryptoFrame[crypto].destroy()
        del self.cryptoFrame[crypto]
        del self.cryptoPrice[crypto]

    def addDivestButton(self, crypto):
        self.disinvestButtons[crypto].grid()

    def removeDivestButton(self, crypto):
        self.disinvestButtons[crypto].grid_remove()

    def checkIfInvestedAndAddBtn(self):
        for i in self.trading.currentUser["investments"]:
            self.addDivestButton(i[0])

    def updateBalanceRest(self):
        self.trading.currentUser["budget"] = math.floor(self.trading.currentUser["budget"] * 100) / 100
        self.frame_balance["rest"].config(text=f"Solde Restant : {self.trading.currentUser['budget']}$")

    def updateBalanceInvest(self):
        amount = self.trading.simulateInvest()
        self.frame_balance["inv"].config(text=f"Solde (Invest.): {amount}$", fg="green" if amount > 0 else "red")
        self.updateBalanceTotal(amount)

    def updateBalanceTotal(self, amount):
        amount += float(self.trading.currentUser["budget"]) + self.trading.getInvested()
        amount = math.floor(amount * 100) / 100
        self.frame_balance["total"].config(text=f"Solde (Total): {amount}$")

    def updateCrypto(self, crypto, amount):
        if self.trading.currentUser == None:
            return
        amount = math.floor(float(amount) * 100) / 100
        oldAmount = self.trading.database.getOldPrice(crypto)
        self.trading.database.editCryptoValue(crypto, amount)

        if not self.cryptoPrice.get(crypto):
            return 

        if crypto in [inv[0] for inv in self.trading.currentUser["investments"]]:
            invested_amount = self.trading.simulateInvest(crypto)
            self.cryptoPrice[crypto].config(
                text=f"{amount}$ ({invested_amount}$)",
                fg="green" if invested_amount > 0 else "red",
                font=("Helvetica", 16, "bold" if invested_amount > 0 else "normal")
            )
        else:
            self.cryptoPrice[crypto].config(
                text=f"{amount}$",
                fg="green" if amount > oldAmount else "red",
                font=("Helvetica", 16)
            )

        self.updateBalanceInvest()
