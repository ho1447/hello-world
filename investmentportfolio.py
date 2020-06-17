import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import plotly.graph_objs as go

from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

from pandas_datareader import data as pdr
import fix_yahoo_finance as yf
yf.pdr_override

print(__version__)
init_notebook_mode(connected=True)

#Import sample worksheet with acquisition dates and initial cost basis
portfoliodf = pd.read_excel('Sample stocks acquisition date_costs.xlsx', sheet_name='Sample')

#pull back stock prices in the range
start_sp = dt.datetime(2013, 1, 1)
end_sp = dt.datetime(2018, 3, 9)
sp_500_adj_close = dt.datetime(2018, 3, 9)
endoflastyear = dt.datetime(2017, 12, 29)

#get from yahoo finance
sp500 = pdr.get_data_yahoo('^GSPC', start_sp, end_sp)

tickers = portfoliodf['Ticker'].unique()

def get(tickers, startdate, enddate):
    def data(ticker):
        return (pdr.get_data_yahoo(ticker, start=startdate, end=enddate))
    datas = map(data, tickers)
    return (pd.concat(datas, keys=tickers, names=['Ticker', 'Date']))

all_data = get(tickers, start_sp, end_sp)

adj_close = all_data[['Adj Close']].reset_index()
adj_close_start = adj_close[adj_close['Date']==endoflastyear]

adj_close_latest = adj_close[adj_close['Date']==end_sp]
sp_500_adj_close_start = sp_500_adj_close[sp_500_adj_close['Date']==endoflastyear]
portfoliodf.set_index(['Ticker'], implace = True)

mergedportfolio = pd.merge(portfoliodf, adj_close_latest, left_index=True, right_index=True)

mergedportfolio['ticker return'] = mergedportfolio['Adj Close'] / mergedportfolio['Unit Cost'] - 1
mergedportfolio.reset_index(inplace=True)
mergedportfoliosp = pd.merge(mergedportfolio, adj_close, left_on='Acquisition Date', right_on='Date')
del mergedportfoliosp['Date_y']

mergedportfoliosp.rename(columns={'Date_x': 'Latest Date', 'Adj Close_x': 'Ticker Adj Close'
                                    , 'Adj Close_y': 'SP 500 Initial Close'}, inplace=True)

# This new column determines what SP 500 equivalent purchase would have been at purchase date of stock.
mergedportfoliosp['Equiv SP Shares'] = mergedportfoliosp['Cost Basis'] / mergedportfoliosp['SP 500 Initial Close']


# We are joining the developing dataframe with the sp500 closes again, this time with the latest close for SP.
merged_portfolio_sp_latest = pd.merge(mergedportfoliosp, sp_500_adj_close, left_on='Latest Date', right_on='Date')


# Once again need to delete the new Date column added as it's redundant to Latest Date.  
# Modify Adj Close from the sp dataframe to distinguish it by calling it the SP 500 Latest Close.

del merged_portfolio_sp_latest['Date']

merged_portfolio_sp_latest.rename(columns={'Adj Close': 'SP 500 Latest Close'}, inplace=True)

# Percent return of SP from acquisition date of position through latest trading day.
merged_portfolio_sp_latest['SP Return'] = merged_portfolio_sp_latest['SP 500 Latest Close'] / merged_portfolio_sp_latest['SP 500 Initial Close'] - 1

# This is a new column which takes the tickers return and subtracts the sp 500 equivalent range return.
merged_portfolio_sp_latest['Abs. Return Compare'] = merged_portfolio_sp_latest['ticker return'] - merged_portfolio_sp_latest['SP Return']

# This is a new column where we calculate the ticker's share value by multiplying the original quantity by the latest close.
merged_portfolio_sp_latest['Ticker Share Value'] = merged_portfolio_sp_latest['Quantity'] * merged_portfolio_sp_latest['Ticker Adj Close']

# We calculate the equivalent SP 500 Value if we take the original SP shares * the latest SP 500 share price.
merged_portfolio_sp_latest['SP 500 Value'] = merged_portfolio_sp_latest['Equiv SP Shares'] * merged_portfolio_sp_latest['SP 500 Latest Close']

# This is a new column where we take the current market value for the shares and subtract the SP 500 value.
merged_portfolio_sp_latest['Abs Value Compare'] = merged_portfolio_sp_latest['Ticker Share Value'] - merged_portfolio_sp_latest['SP 500 Value']

# This column calculates profit / loss for stock position.
merged_portfolio_sp_latest['Stock Gain / (Loss)'] = merged_portfolio_sp_latest['Ticker Share Value'] - merged_portfolio_sp_latest['Cost Basis']

# This column calculates profit / loss for SP 500.
merged_portfolio_sp_latest['SP 500 Gain / (Loss)'] = merged_portfolio_sp_latest['SP 500 Value'] - merged_portfolio_sp_latest['Cost Basis']

merged_portfolio_sp_latest_YTD = pd.merge(merged_portfolio_sp_latest, adj_close_start, on='Ticker')

# Join the SP 500 start of year with current dataframe for SP 500 ytd comparisons to tickers.

merged_portfolio_sp_latest_YTD_sp = pd.merge(merged_portfolio_sp_latest_YTD, sp_500_adj_close_start
                                             , left_on='Start of Year', right_on='Date')

del merged_portfolio_sp_latest_YTD_sp['Date']

# Renaming so that it's clear this column is SP 500 start of year close.
merged_portfolio_sp_latest_YTD_sp.rename(columns={'Adj Close': 'SP Start Year Close'}, inplace=True)

# YTD return for portfolio position.
merged_portfolio_sp_latest_YTD_sp['Share YTD'] = merged_portfolio_sp_latest_YTD_sp['Ticker Adj Close'] / merged_portfolio_sp_latest_YTD_sp['Ticker Start Year Close'] - 1

# YTD return for SP to run compares.
merged_portfolio_sp_latest_YTD_sp['SP 500 YTD'] = merged_portfolio_sp_latest_YTD_sp['SP 500 Latest Close'] / merged_portfolio_sp_latest_YTD_sp['SP Start Year Close'] - 1

merged_portfolio_sp_latest_YTD_sp = merged_portfolio_sp_latest_YTD_sp.sort_values(by='Ticker', ascending=True)

# Cumulative sum of original investment
merged_portfolio_sp_latest_YTD_sp['Cum Invst'] = merged_portfolio_sp_latest_YTD_sp['Cost Basis'].cumsum()

# Cumulative sum of Ticker Share Value (latest FMV based on initial quantity purchased).
merged_portfolio_sp_latest_YTD_sp['Cum Ticker Returns'] = merged_portfolio_sp_latest_YTD_sp['Ticker Share Value'].cumsum()

# Cumulative sum of SP Share Value (latest FMV driven off of initial SP equiv purchase).
merged_portfolio_sp_latest_YTD_sp['Cum SP Returns'] = merged_portfolio_sp_latest_YTD_sp['SP 500 Value'].cumsum()

# Cumulative CoC multiple return for stock investments
merged_portfolio_sp_latest_YTD_sp['Cum Ticker ROI Mult'] = merged_portfolio_sp_latest_YTD_sp['Cum Ticker Returns'] / merged_portfolio_sp_latest_YTD_sp['Cum Invst']


# Need to factor in that some positions were purchased much more recently than others.
# Join adj_close dataframe with portfolio in order to have acquisition date.

portfoliodf.reset_index(inplace=True)

adj_close_acq_date = pd.merge(adj_close, portfoliodf, on='Ticker')

adj_close_acq_date.head()


# delete_columns = ['Quantity', 'Unit Cost', 'Cost Basis', 'Start of Year']

del adj_close_acq_date['Quantity']
del adj_close_acq_date['Unit Cost']
del adj_close_acq_date['Cost Basis']
del adj_close_acq_date['Start of Year']

# Sort by these columns in this order in order to make it clearer where compare for each position should begin.
adj_close_acq_date.sort_values(by=['Ticker', 'Acquisition Date', 'Date'], ascending=[True, True, True], inplace=True)


# Anything less than 0 means that the stock close was prior to acquisition.
adj_close_acq_date['Date Delta'] = adj_close_acq_date['Date'] - adj_close_acq_date['Acquisition Date']

adj_close_acq_date['Date Delta'] = adj_close_acq_date[['Date Delta']].apply(pd.to_numeric)  


# Modified the dataframe being evaluated to look at highest close which occurred after Acquisition Date (aka, not prior to purchase).

adj_close_acq_date_modified = adj_close_acq_date[adj_close_acq_date['Date Delta']>=0]

# This pivot table will index on the Ticker and Acquisition Date, and find the max adjusted close.

adj_close_pivot = adj_close_acq_date_modified.pivot_table(index=['Ticker', 'Acquisition Date'], values='Adj Close', aggfunc=np.max)

adj_close_pivot.reset_index(inplace=True)


# Merge the adj close pivot table with the adj_close table in order to grab the date of the Adj Close High (good to know).

adj_close_pivot_merged = pd.merge(adj_close_pivot, adj_close
                                             , on=['Ticker', 'Adj Close'])


# Merge the Adj Close pivot table with the master dataframe to have the closing high since you have owned the stock.

merged_portfolio_sp_latest_YTD_sp_closing_high = pd.merge(merged_portfolio_sp_latest_YTD_sp, adj_close_pivot_merged
                                             , on=['Ticker', 'Acquisition Date'])

# Renaming so that it's clear that the new columns are two year closing high and two year closing high date.
merged_portfolio_sp_latest_YTD_sp_closing_high.rename(columns={'Adj Close': 'Closing High Adj Close', 'Date': 'Closing High Adj Close Date'}, inplace=True)

merged_portfolio_sp_latest_YTD_sp_closing_high['Pct off High'] = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker Adj Close'] / merged_portfolio_sp_latest_YTD_sp_closing_high['Closing High Adj Close'] - 1 

# Current Share Price versus Closing High Since Purchased

trace1 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['Pct off High'][0:10],
    name = 'Pct off High')
    
data = [trace1]

layout = go.Layout(title = 'Adj Close % off of High'
    , barmode = 'group'
    , yaxis=dict(title='% Below Adj Close High', tickformat=".2%")
    , xaxis=dict(title='Ticker')
    , legend=dict(x=.8,y=1)
    )

fig = go.Figure(data=data, layout=layout)
iplot(fig)
print(fig)
