# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from IPython import get_ipython


# %%
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')

from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

import plotly.graph_objs as go

print(__version__) # requires version >= 1.9.0

init_notebook_mode(connected=True)


# %%
portfolio_df = pd.read_excel('Sample stocks acquisition dates_costs.xlsx', sheetname='Sample')

portfolio_df.head(10)


# %%
# The below will pull back stock prices from 2010 until end date specified.
start_sp = datetime.datetime(2013, 1, 1)
end_sp = datetime.datetime(2018, 3, 9)

# This variable is used for YTD performance.
end_of_last_year = datetime.datetime(2017, 12, 29)

# These are separate if for some reason want different date range than SP.
stocks_start = datetime.datetime(2013, 1, 1)
stocks_end = datetime.datetime(2018, 3, 9)


# %%
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override() 

sp500 = pdr.get_data_yahoo('^GSPC', 
                           start_sp,
                             end_sp)
                          
sp500.head()


# %%
sp500.tail()


# %%
sp500_adj_close = sp500[['Adj Close']].reset_index()


# %%
sp500_adj_close.tail()


# %%
sp_500_adj_close_start = sp500_adj_close[sp500_adj_close['Date']==end_of_last_year]
sp_500_adj_close_start


# %%
tickers = portfolio_df['Ticker'].unique()
tickers


# %%
def get(tickers, startdate, enddate):
    def data(ticker):
        return (pdr.get_data_yahoo(ticker, start=startdate, end=enddate))
    datas = map(data, tickers)
    return(pd.concat(datas, keys=tickers, names=['Ticker', 'Date']))
               
all_data = get(tickers, stocks_start, stocks_end)


# %%
all_data.head()


# %%
adj_close = all_data[['Adj Close']].reset_index()
adj_close.head()


# %%
adj_close_start = adj_close[adj_close['Date']==end_of_last_year]
adj_close_start.head()


# %%
adj_close_latest = adj_close[adj_close['Date']==stocks_end]
adj_close_latest


# %%
adj_close_latest.set_index('Ticker', inplace=True)
adj_close_latest.head()


# %%
portfolio_df.set_index(['Ticker'], inplace=True)

portfolio_df.head()


# %%
merged_portfolio = pd.merge(portfolio_df, adj_close_latest, left_index=True, right_index=True)
merged_portfolio.head()


# %%
merged_portfolio['ticker return'] = merged_portfolio['Adj Close'] / merged_portfolio['Unit Cost'] - 1

merged_portfolio


# %%

merged_portfolio.reset_index(inplace=True)


# %%
merged_portfolio_sp = pd.merge(merged_portfolio, sp500_adj_close, left_on='Acquisition Date', right_on='Date')
# .set_index('Ticker')

merged_portfolio_sp.head()


# %%
del merged_portfolio_sp['Date_y']

merged_portfolio_sp.rename(columns={'Date_x': 'Latest Date', 'Adj Close_x': 'Ticker Adj Close'
                                    , 'Adj Close_y': 'SP 500 Initial Close'}, inplace=True)

merged_portfolio_sp.head()


# %%
merged_portfolio_sp['Equiv SP Shares'] = merged_portfolio_sp['Cost Basis'] / merged_portfolio_sp['SP 500 Initial Close']
merged_portfolio_sp.head()


# %%
merged_portfolio_sp_latest = pd.merge(merged_portfolio_sp, sp500_adj_close, left_on='Latest Date', right_on='Date')

merged_portfolio_sp_latest.head()


# %%
del merged_portfolio_sp_latest['Date']

merged_portfolio_sp_latest.rename(columns={'Adj Close': 'SP 500 Latest Close'}, inplace=True)

merged_portfolio_sp_latest.head()


# %%
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

merged_portfolio_sp_latest.head()


# %%
merged_portfolio_sp_latest_YTD = pd.merge(merged_portfolio_sp_latest, adj_close_start, on='Ticker')
# , how='outer'

merged_portfolio_sp_latest_YTD.head()


# %%
# Deleting date again as it's an unnecessary column.  Explaining that new column is the Ticker Start of Year Close.

del merged_portfolio_sp_latest_YTD['Date']

merged_portfolio_sp_latest_YTD.rename(columns={'Adj Close': 'Ticker Start Year Close'}, inplace=True)

merged_portfolio_sp_latest_YTD.head()


# %%

merged_portfolio_sp_latest_YTD_sp = pd.merge(merged_portfolio_sp_latest_YTD, sp_500_adj_close_start
                                             , left_on='Start of Year', right_on='Date')

merged_portfolio_sp_latest_YTD_sp.head()


# %%
# Deleting another unneeded Date column.


# Renaming so that it's clear this column is SP 500 start of year close.
merged_portfolio_sp_latest_YTD_sp.rename(columns={'Adj Close': 'SP Start Year Close'}, inplace=True)

# YTD return for portfolio position.
merged_portfolio_sp_latest_YTD_sp['Share YTD'] = merged_portfolio_sp_latest_YTD_sp['Ticker Adj Close'] / merged_portfolio_sp_latest_YTD_sp['Ticker Start Year Close'] - 1

# YTD return for SP to run compares.
merged_portfolio_sp_latest_YTD_sp['SP 500 YTD'] = merged_portfolio_sp_latest_YTD_sp['SP 500 Latest Close'] / merged_portfolio_sp_latest_YTD_sp['SP Start Year Close'] - 1

merged_portfolio_sp_latest_YTD_sp.head()


# %%

merged_portfolio_sp_latest_YTD_sp = merged_portfolio_sp_latest_YTD_sp.sort_values(by='Ticker', ascending=True)
merged_portfolio_sp_latest_YTD_sp


# %%

# Cumulative sum of original investment
merged_portfolio_sp_latest_YTD_sp['Cum Invst'] = merged_portfolio_sp_latest_YTD_sp['Cost Basis'].cumsum()

# Cumulative sum of Ticker Share Value (latest FMV based on initial quantity purchased).
merged_portfolio_sp_latest_YTD_sp['Cum Ticker Returns'] = merged_portfolio_sp_latest_YTD_sp['Ticker Share Value'].cumsum()

# Cumulative sum of SP Share Value (latest FMV driven off of initial SP equiv purchase).
merged_portfolio_sp_latest_YTD_sp['Cum SP Returns'] = merged_portfolio_sp_latest_YTD_sp['SP 500 Value'].cumsum()

# Cumulative CoC multiple return for stock investments
merged_portfolio_sp_latest_YTD_sp['Cum Ticker ROI Mult'] = merged_portfolio_sp_latest_YTD_sp['Cum Ticker Returns'] / merged_portfolio_sp_latest_YTD_sp['Cum Invst']

merged_portfolio_sp_latest_YTD_sp.head()


# %%

# Referencing the adj_close dataframe from above

adj_close.head()


# %%
portfolio_df.head()


# %%
# Need to factor in that some positions were purchased much more recently than others.
# Join adj_close dataframe with portfolio in order to have acquisition date.

portfolio_df.reset_index(inplace=True)

adj_close_acq_date = pd.merge(adj_close, portfolio_df, on='Ticker')

adj_close_acq_date.head()


# %%

# delete_columns = ['Quantity', 'Unit Cost', 'Cost Basis', 'Start of Year']

del adj_close_acq_date['Quantity']
del adj_close_acq_date['Unit Cost']
del adj_close_acq_date['Cost Basis']
del adj_close_acq_date['Start of Year']

# Sort by these columns in this order in order to make it clearer where compare for each position should begin.
adj_close_acq_date.sort_values(by=['Ticker', 'Acquisition Date', 'Date'], ascending=[True, True, True], inplace=True)


# %%

# Anything less than 0 means that the stock close was prior to acquisition.
adj_close_acq_date['Date Delta'] = adj_close_acq_date['Date'] - adj_close_acq_date['Acquisition Date']

adj_close_acq_date['Date Delta'] = adj_close_acq_date[['Date Delta']].apply(pd.to_numeric)  

adj_close_acq_date.head()


# %%

# Modified the dataframe being evaluated to look at highest close which occurred after Acquisition Date (aka, not prior to purchase).

adj_close_acq_date_modified = adj_close_acq_date[adj_close_acq_date['Date Delta']>=0]

adj_close_acq_date_modified.head()


# %%

# This pivot table will index on the Ticker and Acquisition Date, and find the max adjusted close.

adj_close_pivot = adj_close_acq_date_modified.pivot_table(index=['Ticker', 'Acquisition Date'], values='Adj Close', aggfunc=np.max)

adj_close_pivot.reset_index(inplace=True)

adj_close_pivot


# %%

# Merge the adj close pivot table with the adj_close table in order to grab the date of the Adj Close High (good to know).

adj_close_pivot_merged = pd.merge(adj_close_pivot, adj_close
                                             , on=['Ticker', 'Adj Close'])

adj_close_pivot_merged.head()


# %%

# Merge the Adj Close pivot table with the master dataframe to have the closing high since you have owned the stock.

merged_portfolio_sp_latest_YTD_sp_closing_high = pd.merge(merged_portfolio_sp_latest_YTD_sp, adj_close_pivot_merged
                                             , on=['Ticker', 'Acquisition Date'])

# Renaming so that it's clear that the new columns are two year closing high and two year closing high date.
merged_portfolio_sp_latest_YTD_sp_closing_high.rename(columns={'Adj Close': 'Closing High Adj Close', 'Date': 'Closing High Adj Close Date'}, inplace=True)

merged_portfolio_sp_latest_YTD_sp_closing_high['Pct off High'] = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker Adj Close'] / merged_portfolio_sp_latest_YTD_sp_closing_high['Closing High Adj Close'] - 1 

merged_portfolio_sp_latest_YTD_sp_closing_high


# %%

trace1 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp['Share YTD'][0:10],
    name = 'Ticker YTD')

trace2 = go.Scatter(
    x = merged_portfolio_sp_latest_YTD_sp['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp['SP 500 YTD'][0:10],
    name = 'SP500 YTD')
    
data = [trace1, trace2]

layout = go.Layout(title = 'YTD Return vs S&P 500 YTD'
    , barmode = 'group'
    , yaxis=dict(title='Returns', tickformat=".2%")
    , xaxis=dict(title='Ticker')
    , legend=dict(x=.8,y=1)
    )

fig = go.Figure(data=data, layout=layout)
iplot(fig)


# %%
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


# %%
trace1 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['ticker return'][0:10],
    name = 'Ticker Total Return')

trace2 = go.Scatter(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['SP Return'][0:10],
    name = 'SP500 Total Return')
    
data = [trace1, trace2]

layout = go.Layout(title = 'Total Return vs S&P 500'
    , barmode = 'group'
    , yaxis=dict(title='Returns', tickformat=".2%")
    , xaxis=dict(title='Ticker', tickformat=".2%")
    , legend=dict(x=.8,y=1)
    )

fig = go.Figure(data=data, layout=layout)
iplot(fig)


# %%

trace1 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['Stock Gain / (Loss)'][0:10],
    name = 'Ticker Total Return ($)')

trace2 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['SP 500 Gain / (Loss)'][0:10],
    name = 'SP 500 Total Return ($)')

trace3 = go.Scatter(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'][0:10],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['ticker return'][0:10],
    name = 'Ticker Total Return %',
    yaxis='y2')

data = [trace1, trace2, trace3]

layout = go.Layout(title = 'Gain / (Loss) Total Return vs S&P 500'
    , barmode = 'group'
    , yaxis=dict(title='Gain / (Loss) ($)')
    , yaxis2=dict(title='Ticker Return', overlaying='y', side='right', tickformat=".2%")
    , xaxis=dict(title='Ticker')
    , legend=dict(x=.75,y=1)
    )

fig = go.Figure(data=data, layout=layout)
iplot(fig)


# %%
trace1 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['Cum Invst'],
    # mode = 'lines+markers',
    name = 'Cum Invst')

trace2 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['Cum SP Returns'],
    # mode = 'lines+markers',
    name = 'Cum SP500 Returns')

trace3 = go.Bar(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['Cum Ticker Returns'],
    # mode = 'lines+markers',
    name = 'Cum Ticker Returns')

trace4 = go.Scatter(
    x = merged_portfolio_sp_latest_YTD_sp_closing_high['Ticker'],
    y = merged_portfolio_sp_latest_YTD_sp_closing_high['Cum Ticker ROI Mult'],
    # mode = 'lines+markers',
    name = 'Cum ROI Mult'
    , yaxis='y2')


data = [trace1, trace2, trace3, trace4]

layout = go.Layout(title = 'Total Cumulative Investments Over Time'
    , barmode = 'group'
    , yaxis=dict(title='Returns')
    , xaxis=dict(title='Ticker')
    , legend=dict(x=.4,y=1)
    , yaxis2=dict(title='Cum ROI Mult', overlaying='y', side='right')               
    )

fig = go.Figure(data=data, layout=layout)
iplot(fig)


# %%


