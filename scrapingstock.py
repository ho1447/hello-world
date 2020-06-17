import requests
from bs4 import BeautifulSoup
import pandas as pd
from pandas_datareader import data
from datetime import date
from dfvaluetoint import format

def getbettermentlist():
    dictlist=[]
    dictlist.append({'value':'VTI', 'label':'U.S. Total stock Market (VTI)'})
    dictlist.append({'value':'VEA', 'label':'International Developed Stocks (VEA)'})
    dictlist.append({'value':'VWO', 'label':'Emerging Market Stocks (VWO)'})
    dictlist.append({'value':'SHV', 'label':'Short-Term Treasuries (SHV)'})
    dictlist.append({'value':'SHY', 'label':'iShares 1-3 Year Treasury Bond ETF (SHY)'})
    dictlist.append({'value':'TLT', 'label':'iShares 20+ Year Treasury Bond ETF (TLT)'})
    dictlist.append({'value':'IEF', 'label':'iShares 7-10 Year Treasury Bond ETF (IEF)'})
    dictlist.append({'value':'IAU', 'label':'iShares Gold Trust (IAU)'})
    dictlist.append({'value':'VNQ', 'label':'Vanguard Real Estate ETF (VNQ)'})
    dictlist.append({'value':'DBC', 'label':'Invesco DB Commodity Index Tracking Fund (DBC)'})
    return dictlist

def saveSp500StocksInfo():
    soup = BeautifulSoup(requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies').text, 'lxml')
    tickers = []
    securities=[]
    gics_industries=[]
    gics_sub_industries=[]

    for row in soup.table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        security = row.findAll('td')[1].text
        gics_industry = row.findAll('td')[3].text
        gics_sub_industry = row.findAll('td')[4].text

        tickers.append(ticker.lower().replace("\n", " "))
        securities.append(security)
        gics_industries.append(gics_industry.lower())
        gics_sub_industries.append(gics_sub_industry.lower())

    stocks_info_df = pd.DataFrame({'tickers':tickers, 'securities': securities, 'gics_industries': gics_industries, 'gics_sub_industries':gics_sub_industries})

# Create a list of dict based on tickers and labels
    dictlist = []
    for index, row in stocks_info_df.iterrows():
         dictlist.append({'value':row["tickers"],'label':row["securities"]})
    return dictlist

# self append
def save_self_stocks_info():
    dictlist = []

    dictlist.append({'value':'sq', 'label':'SQ Square SA'})
    dictlist.append({'value':'kbsty', 'label':'Kobe steel'})
    dictlist.append({'value':'NESN', 'label':'Nestle'})
    dictlist.append({'value':'BN', 'label':'Danone'})
    
    return dictlist

#table of critical values
def getfinancialreportingdf(ticker):
    urlfinancials = 'https://www.marketwatch.com/investing/stock/'+ticker+'/financials'
    urlbalancesheet = 'https://www.marketwatch.com/investing/stock/'+ticker+'/financials/balance-sheet'

    text_soup_financials = BeautifulSoup(requests.get(urlfinancials).text,"lxml") #read in
    text_soup_balancesheet = BeautifulSoup(requests.get(urlbalancesheet).text,"lxml") #read in

    #Income statement
    titlesfinancials = text_soup_financials.findAll('td', {'class': 'rowTitle'})
    epslist =[]
    netincomelist = []
    interestexpenselist = []
    ebitdalist = []
    yearlist = [2015, 2016, 2017, 2018, 2019]

    for title in titlesfinancials:
        if 'EPS (Basic)' in title.text:
            epslist.append([td.text for td in title.findNextSiblings('td', {'class': 'valueCell'})])    
        if 'Net Income' in title.text:
            netincomelist.append([td.text for td in title.findNextSiblings('td', {'class': 'valueCell'})])
        if 'Interest Expense' in title.text:
            interestexpenselist.append([td.text for td in title.findNextSiblings('td', {'class': 'valueCell'})])
        if 'EBITDA' in title.text:
            ebitdalist.append([td.text for td in title.findNextSiblings('td', {'class': 'valueCell'})])
    
    #take only the correct rows of data
    eps = epslist[0]
    epsgrowth = epslist[1]
    netincome = netincomelist[1]
    interestexpense = interestexpenselist[0]
    ebitda = ebitdalist[0]

    #Balance sheet
    titlesbalance = text_soup_balancesheet.findAll('td', {'class': 'rowTitle'})
    shareholdersquitylist = []
    longtermdebtlist = []

    for title in titlesbalance:
        if 'Total Shareholders\' Equity' in title.text:
            shareholdersquitylist.append([td.text for td in title.findNextSiblings('td', {'class': 'valueCell'})])
        if 'Long-Term Debt' in title.text:
            longtermdebtlist.append([td.text for td in title.findNextSiblings('td', {'class': 'valueCell'})])



    shareholderquity = shareholdersquitylist[0]
    longtermdebt = longtermdebtlist[0]
    ROA = shareholdersquitylist[1]

    df = pd.DataFrame({'EPS': eps, 'EPS Growth':epsgrowth, 'Net Income': netincome, 'Shareholder Equity':shareholderquity,'ROA': ROA, 'Long-Term Debt': longtermdebt, 'Interest Expense': interestexpense, 'EBITDA': ebitda}, index=yearlist)
    df.index.name = 'Year'
    return df

def includecalcvariablesdf(ticker):
    df = getfinancialreportingdf(ticker)
    dftoint = df.apply(format)
    dftoint['ROE'] = dftoint['Net Income']/dftoint['Shareholder Equity']
    dftoint['Interest Coverage Ratio'] = dftoint['EBITDA']/dftoint['Interest Expense']
    return dftoint


def getetfdf(ticker):
    url="https://finance.yahoo.com/quote/"+ticker+"?p="+ticker
    soup=BeautifulSoup(requests.get(url).text, 'lxml')

    titlelist=[]
    valuelist=[]

    #get the titles wanted
    titles=soup.findAll('td', class_="C($primaryColor)")
    for i in titles: 
        if "Volume"==i.text or "Net Assets"==i.text or "NAV"==i.text or "PE Ratio (TTM)"==i.text or "Yield"==i.text or "YTD Daily Total Return"==i.text \
            or "Beta (5Y Monthly)"==i.text or "Expense Ratio (net)"==i.text or "Inception Date"==i.text:
            titlelist.append(i.text)
    
    #get the values wanted
    values=soup.findAll('td', class_="Ta(end) Fw(600) Lh(14px)")
    for i in values:
        valuelist.append(i.text)

    #remove values that are not needed (e.g. value of Previous Close)
    valuelist=[valuelist[6]]+valuelist[8:]

    #create a dataframe
    df = pd.DataFrame([valuelist], columns=titlelist)
    df=df.set_index("Inception Date")
    return df


if __name__ == '__main__':
    getfinancialreportingdf('AAPL')