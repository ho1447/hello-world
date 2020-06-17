import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd 
import requests
import yfinance as yf
from bs4 import BeautifulSoup
import time
import datetime as dt
from pytrends.request import TrendReq
from yahooquery import Ticker

#access to gspreads
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('stock-info-center-e644b7e86ffd.json', scope)
gc = gspread.authorize(credentials)
spreadsheet = gc.open('My stock info page')

#df for worksheet "filtered info"
soup = BeautifulSoup(requests.get('https://slickcharts.com/sp500').text, "html5lib")
content = soup.findAll('table')[0].findAll('tr')[1:]

nameList = []
labelList = []
weightList = []

for i in content:
    nameList.append(i.findAll('td')[1].text)
    labelList.append(i.findAll('td')[2].text.replace('.', '-'))
    weightList.append(float(i.findAll('td')[3].text))

df = pd.DataFrame({'Name': nameList, 'Label': labelList, 'Weight': weightList})

df = df.iloc[:30,:]
stk_list=df.Label

#df for company info and stock info
stkBasicData = Ticker('AAPL').price
    #column names of df
info_columns = list(stkBasicData.get('AAPL').keys())

stk_info_df = pd.DataFrame(index = stk_list)
failedList = []
valuelist1=[]
valuelist2=[]
namelist=[]
regmarketchangepercentlist=[]
regmarketpricelist=[]
postmarketchangepercentlist=[]
postmarketpricelist=[]

    #df for "other info"
stk_price_df = pd.DataFrame(columns = ['label','Open','High','Low','Close','Adj Close','Volume'])

failedList = []
    #appending basic info of each company
for i in stk_list:
    try:
        print(i)
        infoDict = Ticker(i).price.get(i)
        colIncluded = list(infoDict.keys())
        intersectCol = [x for x in info_columns if x in colIncluded]
# # 示範頁呈現的股票基本資料包含：股票名稱 / 最後報酬率 / 盤前報酬率 / 盤後報酬率 / 最後收盤價 / 盤前股價 / 盤後股價 / 最近一交易日股價區間 / 近一年股價區間
        namelist.append(infoDict.get('longName'))
        regmarketchangepercentlist.append(infoDict.get('regularMarketChangePercent'))
        postmarketchangepercentlist.append(infoDict.get('postMarketChangePercent'))
        regmarketpricelist.append(infoDict.get('regularMarketPrice'))
        postmarketpricelist.append(infoDict.get('postMarketPrice'))
        time.sleep(1)
        temp = yf.download(i, start = dt.datetime.today() + dt.timedelta(-200))
        temp['label'] = i
        #only data from last 90 days
        temp = temp.iloc[-90:,:]
        stk_price_df = stk_price_df.append(temp)
        time.sleep(1)
    except:
        failedList.append(i)
        continue

for ticker in stk_list:
    url="https://finance.yahoo.com/quote/"+ticker+"?p="+ticker
    soup=BeautifulSoup(requests.get(url).text, 'lxml')
    values=soup.findAll('td', class_="Ta(end) Fw(600) Lh(14px)")
    valuelist=[]
    for i in values:
        valuelist.append(i.text)
    #remove values that are not needed (e.g. value of Previous Close)
    valuelist1.append(valuelist[4])
    valuelist2.append(valuelist[5])
stk_info_df['longName']=namelist
stk_info_df['regularMarketChangePercent']=regmarketchangepercentlist
stk_info_df['postMarketChangePercent']=postmarketchangepercentlist
stk_info_df['regularMarketPrice']=regmarketpricelist
stk_info_df['postMarketPrice']=postmarketpricelist
stk_info_df['Day\'s Range']=valuelist1
stk_info_df['52 Week Range']=valuelist2

stk_price_df['Date'] = list(map(lambda x: dt.datetime.strftime(x, '%Y-%m-%d'), list(stk_price_df.index)))
stk_price_df = stk_price_df[['label','Date','Open','High','Low','Close','Adj Close','Volume']]


# GoogleTrends df
pytrends = TrendReq(hl = 'en-US', tz = 360)
trend_df = pd.DataFrame(columns = stk_list)

for stk in stk_list:
    try:
        print('processing : ' + stk)
        kw_list = [stk]
        pytrends.build_payload(kw_list, timeframe = 'today 3-m')
        trend_df[stk] = pytrends.interest_over_time()[stk]
        time.sleep(1)
    except:
        continue

trend_df.index = list(map(lambda x: dt.datetime.strftime(x, '%Y-%m-%d'), list(trend_df.index)))


#gurufocus investor holdings df

result=[]
for ticker in stk_list:
    try:
        ticker.replace('-','.')
        soup=BeautifulSoup(requests.get('https://www.gurufocus.com/stock/'+ticker+'/guru-trades').text, 'html5lib')
        table = soup.find_all('table')[5]
        table
        for i in range(1, len(soup.find_all('table')[4].find_all('tr'))):
            data = {'stk': None,
                    'investor': None,
                    'port_date': None,
                    'current_share': None,
                    'per_outstand': None,
                    'per_total_asset': None,
                    'comment': None}

            data['stk'] = ticker
            data['investor'] = soup.find_all('table')[4].find_all('tr')[i].find_all('td')[0].get_text().replace('\n','')
            data['port_date'] = soup.find_all('table')[4].find_all('tr')[i].find_all('td')[1].get_text()
            data['current_share'] = soup.find_all('table')[4].find_all('tr')[i].find_all('td')[2].get_text()
            data['per_outstand'] = soup.find_all('table')[4].find_all('tr')[i].find_all('td')[3].get_text()
            data['per_total_asset'] = soup.find_all('table')[4].find_all('tr')[i].find_all('td')[4].get_text()
            data['comment'] = soup.find_all('table')[4].find_all('tr')[i].find_all('td')[5].get_text()  
            
            result.append(data)
    except:
        continue 

    # change from dictionary to DataFrame
big_trader_df = pd.DataFrame.from_dict(result)


#df for data from investing.com
result=[]
url=requests.get(('https://investing.com/economic-calendar'), headers={'User-agent': 'Mosilla/5.0'})
soup=BeautifulSoup(url.text, 'html5lib')
table = soup.find('table', class_='genTbl closedTbl ecoCalTbl persistArea js-economic-table')
rows=table.find('tbody').findAll('tr', class_='js-event-item')
rows
result = []
for i in rows:
    news = {'time': None,
            'country': None,
            'impact': None,
            'event': None,
            'actual': None,
            'forecast': None,
            'previous': None}
    
    news['time'] = i.attrs['data-event-datetime']
    news['country'] = i.find('td', {'class': 'flagCur'}).find('span').get('title')
    news['impact'] = i.find('td', {'class': 'sentiment'}).get('title')
    news['event'] = i.find('td', {'class': 'event'}).find('a').text.strip()
    news['actual'] = i.find('td', {'class': 'bold'}).text.strip()
    news['forecast'] = i.find('td', {'class': 'fore'}).text.strip()
    news['previous'] = i.find('td', {'class': 'prev'}).text.strip()
    result.append(news)

event_df = pd.DataFrame.from_dict(result)


def pyToGspread():
    #update stk labels to 'filered info'
    ws = spreadsheet.worksheet('filtered info')    
    set_with_dataframe(ws, df, 1, 1, True, True)

    #update stk_info_df to worksheet "basic info"
    ws = spreadsheet.worksheet('basic info')    
    set_with_dataframe(ws, stk_info_df, row = 1, col = 1, include_index = True, include_column_header = True)

    #update stk_price_df to "other info"
    ws = spreadsheet.worksheet('other info')
    set_with_dataframe(ws, stk_price_df, 1, 1, True, True)

    #update trend_df to "googleTrendData"
    ws = spreadsheet.worksheet('googleTrendsData')
    set_with_dataframe(ws, trend_df, 1, 1, True, True)

    #update big_trader_df to "investorsHoldings"
    ws = spreadsheet.worksheet('investorsHoldings')
    set_with_dataframe(ws, big_trader_df, 1, 1, False, True)

    #update event_df to "economicEvents"
    ws = spreadsheet.worksheet('economicEvents')
    set_with_dataframe(ws, event_df, 1, 2, False, True)

pyToGspread()