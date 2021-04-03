import requests
import pandas as pd
from coinbasepro_API import PublicClient
from datetime import datetime
import copy
class Order():
    def __init__(self, portfolio, trade, product, side, date, size, unit, price, fee, total, currency):
        self.portfolio = portfolio
        self.trade = trade
        self.product = product
        self.side = side
        self.date = date
        self.size = size
        self.unit = unit
        self.price = price
        self.fee = fee
        self.total = total
        self.currency = currency
        
    def getPortfolio(self):
        return self.portfolio
    
    def getTrade(self):
        return self.trade

    def getProduct(self):
        return self.product

    def getSide(self):
        return self.side
    
    def getDate(self):
        return self.date

    def getSize(self):
        return self.size

    def getUnit(self):
        return self.unit
        
    def getPrice(self):
        return self.price

    def getFee(self):
        return self.fee
    
    def getTotal(self):
        return self.total
    
    def getCurrency(self):
        return self.currency

class Coin():
    def __init__(self, coin):
        self.coin = coin
        self.amount = 0.0
        self.act_price = 0.0
        self.asset = 0.0
        self.balance = 0.0
        self.trade = []
        self.percent_port = 0.0
        self.profit = 0.0
        self.averageBuy = 0.0
        self.firstTrade = ''
        self.amountInTime = []
        self.moneyInTime = pd.DataFrame()

    def addTrade(self, order):
        self.trade.append(order)
    
    def currentPrice(self):
        if self.coin != "XRP":
            res = requests.get("https://api.coinbase.com/v2/prices/" + self.coin + "-EUR/spot")
            self.act_price = float(res.json()["data"]['amount'])
    
    def countBalance(self):
        if self.amount > 0.000001:
            self.balance = self.amount * self.act_price
        else:
            self.balance = 0.0

    def countProfit(self):
        try:
            if self.balance < 0.000001:
                self.profit = 0.0
            else:
                self.profit = ((self.balance / self.asset) - 1) * 100
        except:
            self.profit = 0.0

    def addPercent(self, percent):
        self.percent_port = percent

    def countAverageBuy(self):
        if self.amount > 0.000001:
            self.averageBuy =  self.asset / self.amount
        else:
            self.averageBuy = 0.0

    def addAmount(self, amount):
        self.amount += float(amount)

    def addAsset(self, asset):
        self.asset += float(asset)

    def createTradePD(self):
        product, side, date, size, unit, price, fee, total, currency = [], [], [], [], [], [], [], [], []
        col = ['Side', 'Date', 'Size', 'Unit', 'Price', 'Fee', 'Total price', 'Currency']
        for i in self.trade:
            product.append(i.getProduct())
            side.append(i.getSide())
            date.append(i.getDate().strftime("%Y/%m/%d, %H:%M:%S"))
            size.append(i.getSize())
            unit.append(i.getUnit())
            price.append(i.getPrice())
            fee.append(i.getFee())
            total.append(i.getTotal())
            currency.append(i.getCurrency())
        df = pd.DataFrame({col[0]:side, col[1]:date, col[2]:size, col[3]:unit, 
        col[4]:price, col[5]:fee, col[6]:total, col[7]:currency}, index=product, columns=col) 
        return df.sort_values(by = [col[1]], ascending=True)

    def createAmountInTimePD(self):
        date, size = [], []
        col = ['Množství', 'Datum']
        for i in self.amountInTime:
            date.append(i.getTime().strftime("%Y/%m/%d, %H:%M:%S"))
            size.append(i.getAmount())
        client = PublicClient()
        f = client.get_time()['iso']
        f = datetime.strptime(f, "%Y-%m-%dT%H:%M:%S.%fZ")
        date.append(f.strftime("%Y/%m/%d, %H:%M:%S"))
        size.append(self.amount)
        return pd.DataFrame({col[0]:size, col[1]:date}, columns=col)
        
    def setPriceInTime(self):
        client = PublicClient()
        f = client.get_time()
        f['iso']
        m = MoneyInTime(self.coin + '-EUR',self.firstTrade, f['iso'], 86400)
        m.setHistData()
        self.moneyInTime = m.getHistData()

    def setFirstTimeTrade(self):
        self.firstTrade = self.trade[0].getDate()
        #Coin.setPriceInTime(self)

    def setAmountInTimeFirst(self):
        spec = []
        amount, asset = 0.0, 0.0
        for i in range(len(self.trade)):
            if self.trade[i].getSide() == "BUY":
                amount += self.trade[i].getSize()
                if self.trade[i].getCurrency() == 'EUR':
                    asset -= self.trade[i].getTotal()
                else:
                    order = Order(self.trade[i].getPortfolio(), self.trade[i].getTrade, self.trade[i].getCurrency() + "-" + self.trade[i].getUnit(), 'SELL', self.trade[i].getDate(), abs(self.trade[i].getTotal()), self.trade[i].getCurrency(), 0, 0, 0, self.trade[i].getUnit())
                    spec.append(order)
            else:   
                if self.trade[i].getCurrency() == 'EUR':
                    asset -= self.trade[i].getTotal()
                else:
                    ass = asset * self.trade[i].getSize() / amount
                    
                    asset -= ass
                    cur = ''
                    if self.trade[i].getCurrency() == self.trade[i - 1].getCurrency():
                        try:
                            cur = self.trade[i - 2].getCurrency()
                        except:
                            cur = self.trade[i - 1].getCurrency()
                    else:
                        cur = self.trade[i - 1].getCurrency()
                    order = Order(self.trade[i].getPortfolio(), self.trade[i].getTrade, self.trade[i].getCurrency() + "-" + cur, 'BUY', self.trade[i].getDate(), self.trade[i].getTotal(), self.trade[i].getCurrency(), ass / self.trade[i].getTotal(), 0, -ass, cur)
                    spec.append(order)
                amount -= self.trade[i].getSize()
        return spec

    def setAmountInTime(self):
        for i in range(len(self.trade)):
            if self.trade[i].getSide() == "BUY":
                self.amount += self.trade[i].getSize()
                if self.trade[i].getCurrency() == 'EUR':
                    self.asset -= self.trade[i].getTotal()
            else:
                self.amount -= self.trade[i].getSize()
                if self.trade[i].getCurrency() == 'EUR':
                    self.asset -= self.trade[i].getTotal()
                else:
                    self.asset -= self.asset * self.trade[i].getSize() / (self.amount + self.trade[i].getSize())
            amit = AmountInTime(self.amount, self.asset, self.trade[i].getDate())
            amit.setEpoch()
            self.amountInTime.append(amit)

    def sortTradeByTime(self):
        self.trade.sort(key=lambda x: x.getDate(), reverse=False)

    def getCoin(self):
        return self.coin

    def getAmount(self):
        return self.amount
    
    def getAct_price(self):
        return self.act_price

    def getAsset(self):
        return self.asset

    def getBalance(self):
        return self.balance
    
    def getTrade(self, i):
        return self.trade[i]

    def getLengthTrade(self):
        return len(self.trade)
    
    def getPercent(self):
        return self.percent_port

    def getProfit(self):
        return self.profit
    
    def getAverageBuy(self):
        return self.averageBuy

    def getMoneyInTime(self):
        return self.moneyInTime

class AmountInTime:
    def __init__(self, amount, asset, time):
        self.amount = amount
        self.asset = asset
        self.time = time
        self.epoch = 0.0

    def getAmount(self):
        return self.amount

    def getAsset(self):
        return self.asset
    
    def getTime(self):
        return self.time

    def setEpoch(self):
        self.epoch = datetime.timestamp(self.time) + 7200

    def getEpoch(self):
        return self.epoch

class MoneyInTime:
    def __init__(self, coinID, start, end, granuality):
        self.coinID = coinID
        self.start = start
        self.end = end
        self.granuality = granuality
        self.histData = pd.DataFrame()

    def setHistData(self):
        col = ['low', 'high', 'open', 'close', 'volume']
        client = PublicClient()
        list = client.get_product_historic_rates(self.coinID, self.start, self.end, self.granuality)
        low, high, openp, close, vol, time = [], [], [], [], [], []
        for i in range(len(list)):
            time.append(list[i][0])
            low.append(list[i][1])
            high.append(list[i][2])
            openp.append(list[i][3])
            close.append(list[i][4])
            vol.append(list[i][5])
        self.histData = pd.DataFrame({col[0]:low, col[1]:high, col[2]:openp, col[3]:close, col[4]:vol}, index=time, columns=col)

    def getHistData(self):
        return self.histData

class nevim:
    def __init__(self, portfolium, date, coin, amount, walet):
        self.portfolium = portfolium
        self.date = date
        self.coin = coin
        self.amount = amount
        self.walet = walet

    def getPortfolio(self):
        return self.portfolium
        
    def getDate(self):
        return self.date

    def getCoin(self):
        return self.coin

    def getAmount(self):
        return self.amount

    def getWalet(self):
        return self.walet

class Deposit(nevim):
    def __init__(self, portfolium, date, coin, amount, walet, cost):
        super().__init__(portfolium, date, coin, amount, walet)
        self.cost = cost

    def getCost(self):
        return self.cost

class Withdrawal(nevim):
    def __init__(self, portfolium, date, coin, amount, fee, walet):
        super().__init__(portfolium, date, coin, amount, walet)
        self.fee = fee
    
    def getFee(self):
        return self.fee
    
class Portfolio():
    def __init__(self, name):
        self.name = name
        self.cryptocoins = []
        self.balance = 0.0
        self.asset = 0.0
        self.percent = 0.0
        self.deposit = []
        self.withdrawal = []
    
    def addCrypto(self, coin):
        self.cryptocoins.append(coin)
    
    def addDeposit(self, deposit):
        self.deposit.append(deposit)

    def addWithdrawal(self, withdrawal):
        self.withdrawal.append(withdrawal)

    def countBalance(self):
        for i in self.cryptocoins:
            self.balance += i.getBalance()

    def countAsset(self):
        for i in self.deposit:
            if i.getCoin() == "EUR":
                self.asset += i.getAmount()
            else:
                for j in range(self.getLengthCryptocoins()):
                    if self.cryptocoins[j].getCoin() == i.getCoin():
                        if i.getWalet() == False:
                            self.cryptocoins[j].addAmount(i.getAmount())
                            self.cryptocoins[j].addAsset(i.getCost())
                            self.asset += i.getCost()
        for i in self.withdrawal:
            if i.getCoin() == "EUR":
                self.asset -= i.getAmount
            else:
                for j in range(self.getLengthCryptocoins()):
                    if self.cryptocoins[j].getCoin() == i.getCoin():
                        if i.getWalet() == True:
                            self.cryptocoins[j].addAmount(-i.getFee())
                        else:
                            self.cryptocoins[j].addAmount(-i.getAmount())

    def countPercent(self):
        if abs(self.asset) > 0.000001:
            self.percent = self.balance / self.asset
        else:
            self.percent = 0

    def givePercent(self):
        for i in self.cryptocoins:
            try:
                i.addPercent(i.getBalance() / self.balance * 100)
            except:
                i.addPercent(0.0)
    
    def createDepositPD(self):
        portfolio, date, unit, size, walet, price = [],[],[],[],[],[]
        col = ['Portfolio', 'Datum', 'Měna', 'Objem', 'Ledger', 'Cena']
        for j in self.deposit:
            portfolio.append(j.getPortfolio())
            date.append(j.getDate().strftime("%Y/%m/%d, %H:%M:%S"))
            unit.append(j.getCoin())
            size.append(j.getAmount())
            walet.append(j.getWalet())
            price.append(j.getCost())
        return pd.DataFrame({col[0]:portfolio, col[1]:date, col[2]:unit, col[3]:size, 
        col[4]:walet, col[5]:price}, columns = col)

    def createWithfrawalPD(self):
        portfolio, date, unit, size, walet, fee = [],[],[],[],[],[]
        col = ['Portfolio', 'Datum', 'Měna', 'Objem', 'Fee', 'Ledger']
        for j in self.withdrawal:
            portfolio.append(j.getPortfolio())
            date.append(j.getDate().strftime("%Y/%m/%d, %H:%M:%S"))
            unit.append(j.getCoin())
            size.append(j.getAmount())
            walet.append(j.getWalet())
            fee.append(j.getFee())
        return pd.DataFrame({col[0]:portfolio, col[1]:date, col[2]:unit, col[3]:size, 
        col[4]:fee, col[5]:walet}, columns = col)

    def createPortfolioPD(self):
        coin, amount, currentPrice, yourAsset, balance, portfolium, profit, averageBuy = [], [], [], [], [], [], [], []
        col = ['Amount', 'Current price', 'Your asset', 'Balance', 'Portfolium', 'Profit', 'Average buy price']
        for i in self.cryptocoins:
            coin.append(i.getCoin())
            a = 0.0
            if i.getAmount() > 0.000001:
                amount.append(i.getAmount())
            else:
                amount.append(a)
            currentPrice.append(i.getAct_price())
            a = 0.0
            if abs(i.getAsset()) > 0.000001:
                yourAsset.append(i.getAsset())
            else:
                yourAsset.append(a)
            balance.append(i.getBalance())
            portfolium.append(i.getPercent())
            profit.append(i.getProfit())
            averageBuy.append(i.getAverageBuy())
        df = pd.DataFrame({col[0]:amount, col[1]:currentPrice, col[2]:yourAsset, col[3]:balance, 
        col[4]:portfolium, col[5]:profit, col[6]:averageBuy}, index=coin, columns=col) 
        return df.sort_values(by = [col[4]], ascending=False)

    def sortCoin(self):
        self.cryptocoins.sort(key=lambda x: x.percent_port, reverse=True)
    
    def getBalance(self):
        return self.balance
    
    def getAsset(self):
        return self.asset

    def getPercent(self):
        return self.percent
    
    def getName(self):
        return self.name
    
    def getCryptocoins(self, i):
        return self.cryptocoins[i]

    def getLengthCryptocoins(self):
        return len(self.cryptocoins)
    
    def getDeposit(self, i):
        return self.deposit[i]

    def getAllDeposit(self):
        return self.deposit
    
    def deleteAllDeposit(self):
        self.deposit.clear()
    
    def getLengthDeposit(self):
        return len(self.deposit)

    def getWithdrawal(self, i):
        return self.withdrawal[i]
    
    def deleteAllWithdrawal(self):
        self.withdrawal.clear()

    def getLengthWithdrawal(self):
        return len(self.withdrawal)

class User:
    def __init__(self):
        self.portfolios = []

    def addPortfolios(self, portfolio):
        self.portfolios.append(portfolio)
    
    def getPortfolios(self, i):
        return self.portfolios[i]
    
    def getLengthPortfolios(self):
        return len(self.portfolios)
    
    def getNamePortfolios(self):
        name = []
        for i in range(len(self.portfolios)):
            name.append(self.portfolios[i].getName())
        return name