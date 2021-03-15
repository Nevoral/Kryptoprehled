import pandas as pd
import streamlit as st
from coinbasepro import Order, Coin, Portfolio, User, Deposit, Withdrawal
import plotly.graph_objects as go
from bs4 import BeautifulSoup
import requests
import json
import copy
import base64

def fill(user, address):
    try: 
        special = []
        file = open(address + '\\fills.txt', 'r')
        p = 0
        while True:
            line = file.readline()
            if not line:
                break
            lines = line.split(",")
            if p > 0:
                order = Order(lines[0], lines[1], lines[2], lines[3], lines[4], lines[5], lines[6], lines[7], lines[8], lines[9], lines[10])
                zapis = 0
                for t in range(user.getLengthPortfolios()):
                    zapis = 0
                    if user.getPortfolios(t).getName() == order.getPortfolio():
                        zapis += 1
                        for p in range(user.getPortfolios(t).getLengthCryptocoins()):
                            if user.getPortfolios(t).getCryptocoins(p).getCoin() == order.getUnit():
                                user.getPortfolios(t).getCryptocoins(p).addTrade(order)
                                zapis += 1
                                if order.getSide() == "SELL" and order.getCurrency() != "EUR":
                                    sp = Order(order.getPortfolio(), order.getTrade(), order.getCurrency() + "-" + order.getUnit(), "BUY", order.getDate(), order.getTotal(), order.getCurrency(), 0, 0, 0, "EUR")
                                    special.append(sp)
                                elif order.getSide() == "BUY" and order.getCurrency() != "EUR":
                                    sp = Order(order.getPortfolio(), order.getTrade(), order.getCurrency() + "-" + order.getUnit(), "SELL", order.getDate(), order.getTotal(), order.getCurrency(), 0, 0, 0, "EUR")
                                    special.append(sp)
                                break
                        break
                if zapis == 0:
                    coin = Coin(order.getUnit())
                    coin.addTrade(order)
                    portfolium = Portfolio(order.getPortfolio())
                    portfolium.addCrypto(coin)
                    user.addPortfolios(portfolium)
                elif zapis == 1:
                    coin = Coin(order.getUnit())
                    coin.addTrade(order)
                    user.getPortfolios(t).addCrypto(coin)
            else:
                p += 1
        file.close()
    except:
        st.title('Prvně musíte zadat adresu ke složce ve, které se vám bude ukládat stav vašeho portfolia pro jednoduší budoucí přístup')

def deposit(user, address):
    try:
        file = open(address + '\deposits.txt', 'r')
        p = 0
        while True:
            line = file.readline()
            if not line:
                break
            lines = line.split(",")
            if p > 0:
                pru = False
                if lines[4] == "1":
                    pru = True
                d = Deposit(lines[0], lines[1], lines[2], float(lines[3]), pru, float(lines[5]))
                for t in range(user.getLengthPortfolios()):
                    if user.getPortfolios(t).getName() == d.getPortfolio():
                        user.getPortfolios(t).addDeposit(d)
            else:
                p += 1
        file.close()
    except:
        print('1')

def withdrawal(user, address):
    try:
        file = open(address + '\withdrawals.txt', 'r')
        p = 0
        while True:
            line = file.readline()
            if not line:
                break
            lines = line.split(",")
            if p > 0:
                pru = False
                if lines[5] == "1":
                    pru = True
                d = Withdrawal(lines[0], lines[1], lines[2], float(lines[3]), float(lines[4]), pru)
                for t in range(user.getLengthPortfolios()):
                    if user.getPortfolios(t).getName() == d.getPortfolio():
                        user.getPortfolios(t).addWithdrawal(d)
            else:
                p += 1
        file.close()
    except:
        print('2')

def firstUpdate(user):
    for i in range(user.getLengthPortfolios()):
        for j in range(user.getPortfolios(i).getLengthCryptocoins()):  
            user.getPortfolios(i).getCryptocoins(j).currentPrice()
            user.getPortfolios(i).getCryptocoins(j).countAmount()
            user.getPortfolios(i).getCryptocoins(j).countBalance()
            user.getPortfolios(i).getCryptocoins(j).countProfit()
            #user.getPortfolios(i).getCryptocoins(j).countAsset()
            user.getPortfolios(i).getCryptocoins(j).countAverageBuy()
        user.getPortfolios(i).countBalance()
        user.getPortfolios(i).countAsset()
        user.getPortfolios(i).countPercent()
        user.getPortfolios(i).givePercent()

def jsonFile(obj):
    print(json.dumps(obj, indent=10))

@st.cache
def load_data(currency_price_unit):
    cmc = requests.get('https://coinmarketcap.com')
    soup = BeautifulSoup(cmc.content, 'html.parser')
    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coin_data = json.loads(data.contents[0])
    listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []
    for i in listings:
      coin_name.append(i['name'])
      coin_symbol.append(i['symbol'])
      price.append(i['quote'][currency_price_unit]['price'])
      percent_change_1h.append(i['quote'][currency_price_unit]['percentChange1h'])
      percent_change_24h.append(i['quote'][currency_price_unit]['percentChange24h'])
      percent_change_7d.append(i['quote'][currency_price_unit]['percentChange7d'])
      market_cap.append(i['quote'][currency_price_unit]['marketCap'])
      volume_24h.append(i['quote'][currency_price_unit]['volume24h'])
    df = pd.DataFrame(columns=['Název coinu', 'Zkratka', 'Cena', 'Změna ceny za hodinu', 'Změna ceny za 24 hodin', 'Změna ceny za 7 dnů', 'Tržní kapitalizace', 'Volume za 24 hodin'])
    df['Název coinu'] = coin_name
    df['Zkratka'] = coin_symbol
    df['Cena'] = price
    df['Změna ceny za hodinu'] = percent_change_1h
    df['Změna ceny za 24 hodin'] = percent_change_24h
    df['Změna ceny za 7 dnů'] = percent_change_7d
    df['Tržní kapitalizace'] = market_cap
    df['Volume za 24 hodin'] = volume_24h
    return df

def expandTable(portfolio, coin):
    portfolio.sortCoin()
    for i in range(portfolio.getLengthCryptocoins()):
        if coin == portfolio.getCryptocoins(i).getCoin():
            text = "{}".format(portfolio.getCryptocoins(i).getCoin())
            expand = st.beta_expander(text, expanded=False)
            port = portfolio.getCryptocoins(i).createTradePD()
            with expand:
                st.table(port)

def depositList(user, address):
    col = st.beta_columns(7)
    name = user.getNamePortfolios()
    with col[0]:
        portfolium = st.selectbox('Název portfolia', name)
    with col[1]:
        date = st.date_input('Zadej datum depositu', value = None)
        time = st.text_input('Zadej čas depositu', value = '', type = "default")
    with col[2]:
        unit = st.text_input('Zadej měnu')
    with col[3]:
        size = st.number_input('Zadej množství')
    with col[4]:
        walet = st.selectbox('Přišlo to z tvého Ledgeru?', ('True', 'False'))
        if walet == 'True':
            su = 1
        else:
            su = 0
    with col[5]:
        price = st.number_input('Kolik tě to stálo?', value = 0.0)
    with col[6]:
        #dep = Deposit(portfolium, str(date) + 'T' + str(time) + 'Z', unit, size, bool(walet), price)
        #user.getPortfolios(name.index(portfolium)).addDeposit(copy.deepcopy(dep))
        #st.markdown(filedownload(user.getPortfolios(name.index(portfolium)).createDepositPD(), 'deposit1'), unsafe_allow_html=True)
        if st.button('Přidat do depositu', key=1):
            dep = Deposit(portfolium, str(date) + 'T' + time + 'Z', unit, size, su, price)
            file = open(address + '\deposits.txt', 'a')
            if testfile('deposits.txt'):
                file.write('{},{},{},{},{},{}\n'.format('Portfolio', 'Datum', 'Měna', 'Objem', 'Ledger', 'Cena'))
            file.write('{},{},{},{},{},{}\n'.format(dep.getPortfolio(), dep.getDate(), dep.getCoin(), dep.getAmount(), dep.getWalet(), dep.getCost()))
            file.close()
            user.getPortfolios(name.index(portfolium)).deleteAllDeposit()
            deposit(user, address)
    st.table(user.getPortfolios(name.index(portfolium)).createDepositPD())

def withdrawalList(user, address):
    col = st.beta_columns(7)
    name = user.getNamePortfolios()
    with col[0]:
        portfolium = st.selectbox('Název portfolia', name)
    with col[1]:
        date = st.date_input('Zadej datum withdrawal', value = None)
        time = st.text_input('Zadej čas withdrawal', value = '', type = "default")
    with col[2]:
        unit = st.text_input('Zadej měnu')
    with col[3]:
        size = st.number_input('Zadej množství')
    with col[4]:
        fee = st.number_input('Poplatek', value = 0.0)
    with col[5]:
        walet = st.selectbox('Odešlo to na tvůj Ledger?', ('True', 'False'))
        if walet == 'True':
            su = 1
        else:
            su = 0
    with col[6]:
        #dep = Deposit(portfolium, str(date) + 'T' + str(time) + 'Z', unit, size, bool(walet), price)
        #user.getPortfolios(name.index(portfolium)).addDeposit(copy.deepcopy(dep))
        #st.markdown(filedownload(user.getPortfolios(name.index(portfolium)).createDepositPD(), 'deposit1'), unsafe_allow_html=True)
        if st.button('Přidat do withdrawal', key=9):
            dep = Withdrawal(portfolium, str(date) + 'T' + str(time) + 'Z', unit, size, float(fee), su)
            file = open(address + '\withdrawals.txt', 'a')
            if testfile('withdrawals.txt'):
                file.write('{},{},{},{},{},{}\n'.format('Portfolio', 'Datum', 'Měna', 'Objem', 'Fee', 'Ledger'))
            file.write('{},{},{},{},{},{}\n'.format(dep.getPortfolio(), dep.getDate(), dep.getCoin(), dep.getAmount(), dep.getFee(), dep.getWalet()))
            file.close()
            user.getPortfolios(name.index(portfolium)).deleteAllWithdrawal()
            withdrawal(user, address)
    st.table(user.getPortfolios(name.index(portfolium)).createWithfrawalPD())

def testfile(name):
    file = open(name, "r")
    lines = file.readlines()
    file.close()
    if len(lines) > 0:
        return False
    else:
        return True

def startingPage(user):  
    address = st.sidebar.text_input("Zadej adresu, kde se nachází fill.txt", value = '', type = "default")
    fill(user, address)
    try:
        deposit(user, address)
    except:
        depositList(user, address)  
    try:
        withdrawal(user, address)
    except:
        withdrawalList(user, address)
    return address

def displayPortfolium(user, address):
    port, name, coinName, percent, coinNameT = [], [], [], [], []
    for i in range(user.getLengthPortfolios()):
        port.append(user.getPortfolios(i).createPortfolioPD())
        name.append(user.getPortfolios(i).getName())
    portfolium = st.sidebar.selectbox("Tvé portfolia", name)
    for i in range(user.getPortfolios(name.index(portfolium)).getLengthCryptocoins()):
        coinNameT.append(user.getPortfolios(name.index(portfolium)).getCryptocoins(i).getCoin())
        if user.getPortfolios(name.index(portfolium)).getCryptocoins(i).getAmount() > 0.000001:
            coinName.append(user.getPortfolios(name.index(portfolium)).getCryptocoins(i).getCoin())
            percent.append(user.getPortfolios(name.index(portfolium)).getCryptocoins(i).getPercent())
    coin = st.sidebar.selectbox("Trady specifického coinu", coinNameT)
    #tady bude grafický vývoj hodnoty portfolia
    if st.sidebar.checkbox("Rozložení portfolia graficky", value = False, key = 0):
        fig = go.Figure(data=[go.Pie(labels=coinName, values=percent, pull=[0.2, 0, 0, 0, 0, 0, 0, 0])])
        st.sidebar.plotly_chart(fig, use_container_width=True)
    if st.sidebar.checkbox('Vytvořit/Přidat deposit/withdrawal', value=False, key = 88):
        dep = st.sidebar.radio('', ['Přidání do Deposit listu', 'Přidání do Withdrawal listu'])
        if dep == 'Přidání do Deposit listu':
            depositList(user, address)
        elif dep == 'Přidání do Withdrawal listu':
            withdrawalList(user, address)
    else:
        expand2 = st.beta_expander("Tvé {} portfolio".format(portfolium), expanded=True)
        with expand2:
            if len(name) > 1:
                st.table(port[name.index(portfolium)])
            elif len(name) == 1:
                st.table(port[0])
        expandTable(user.getPortfolios(name.index(portfolium)), coin)

def crypto_cap(pop):
    st.title(pop)
    st.markdown("""Tato aplikace získává data o 100 největších kryptoměnách z **CoinMarketCap**!""")
    df = load_data('USD')
    sorted_coin = sorted( df['Zkratka'] )
    num_coin = st.sidebar.slider('Zobras Top N Kryptomněn', 1, 100, 100)
    selected_coin = st.sidebar.multiselect('Kryptoměny', sorted_coin, sorted_coin)
    df_selected_coin = df[ (df['Zkratka'].isin(selected_coin)) ] # Filtering data
    df_coins = df_selected_coin[:num_coin]
    st.subheader('Informace o Kryptoměnách')
    st.dataframe(df_coins)
    st.markdown(filedownload(df_selected_coin, 'cryptoCap'), unsafe_allow_html=True)
    # Download CSV data
    # https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806

def filedownload(df, name):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="{name}.csv"><input type="button" value="Download"></a>'
    return href

if __name__ == '__main__':
    st.set_page_config(page_title="Antyho cryptopřehled", page_icon="🧊", layout="wide", initial_sidebar_state="expanded")
    address = ''
    user = User()
    try:
        address = startingPage(user)
    except:
        print("nekdy jindy")
    radio = ['Portfolium', 'Crypto Market Cap', 'Coinbase grafy']
    pop = st.sidebar.radio("", (radio))
    if pop == 'Portfolium':
        firstUpdate(user)
        if user.getLengthPortfolios() > 0:
            displayPortfolium(user, address)
    elif pop == 'Crypto Market Cap':
        crypto_cap(pop)
    else:
        pass
            #res = requests.get("https://api.pro.coinbase.com/products/BTC-USD/candles?start=2021-02-24T12:00:00&stop=2021-02-25T12:00:00&granularity=21600")
            #jsonFile(res.json())
