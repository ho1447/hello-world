import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from pandas_datareader import data as web
import plotly.graph_objs as go
from datetime import datetime as dt
import pandas as pd
import numpy as np
import yfinance as yf


app = dash.Dash(__name__)


data = pd.read_csv('analyzed_portfolio.csv')
tickers = pd.read_csv('tickers.csv')
tickers.set_index('Ticker', inplace=True)


options = []

for tic in tickers.index:
	#{'label': 'user sees', 'value': 'script sees'}
	mydict = {}
	mydict['label'] = tic #Apple Co. AAPL
	mydict['value'] = tic
	options.append(mydict)

app.layout = html.Div([
    html.H1('Portfolio Dashboard'),
    dcc.Markdown('''---'''),
    html.H1('Relative Returns Comparison'),
	html.Div([html.H3('Enter a stock symbol:', style={'paddingRight': '30px'}),
	dcc.Dropdown(
		id='my-tickers',
		options = options,
		value = ['SPY'], 
		multi = True,
	)
    ], style={'display': 'inline-block', 'verticalAlign':'top', 'width': '30%'}), 
    html.Div([
        html.H3('Enter start/end date:'),
        dcc.DatePickerRange(
            id='my-date-picker',
            min_date_allowed=dt(2016,1,1),
            max_date_allowed=dt.today(),
            start_date=dt(2019,1,1),
            end_date=dt.today(),
        )
    ], style={'display':'inline-block'}),
    html.Div([
        html.Button(id='submit-button', n_clicks=0, children='Submit', style = {'fontSize': 24, 'marginLeft': '30px'})
    ], style={'display': 'inline-block'}),
    
	dcc.Graph(id='compare-graph',
		figure={'data':[
			{'x':[1,2], 'y':[3,1]}], 
        'layout':go.Layout(title='Relative Stock Returns Comparison', 
            showlegend = True,
            yaxis = {'title':'Returns', 'tickformat':".2%"}
        )}
	),

    dcc.Markdown(''' --- '''),
    html.Div([
        html.H1('YTD and Total Position Returns versus S&P 500'),
        dcc.Graph(id='ytd-graph',
            figure={'data':[
                go.Bar(
                    x = data['Ticker'][0:20],
                    y = data['Share YTD'][0:20],
                    name = 'Ticker YTD',
                ),
                go.Scatter(
                    x = data['Ticker'][0:20],
                    y = data['SP 500 YTD'][0:20],
                    name='SP500 YTD',
                ),
            ], 'layout':go.Layout(title='YTD Return v.s. S&P 500 YTD',
                barmode='group',
                xaxis={'title': 'Ticker'},
                yaxis={'title': 'Returns', 'tickformat': ".2%"}
            ),
            }, style={'width': '45%', 'display': 'inline-block'}
        ),
        html.H1('Total Returns'),
        dcc.Graph(id='totalgraph',
            figure={
                'data':[
                    go.Bar(
                        x = data['Ticker'][0:20],
                        y = data['ticker return'],
                        name = 'Ticker Total Return'
                    ),
                    go.Scatter(
                        x = data['Ticker'][0:20],
                        y = data['SP Return'][0:20],
                        name = 'SP 500 Total Return'
                    ),
                ], 
                'layout': go.Layout(
                    title='Total Return vs S&P500', 
                    barmode='group', 
                    xaxis={'title': 'Ticker'},
                    yaxis={'title': 'Returns', 'tickformat': '.2%'}
                ), 
            
            }, style={'width': '45%', 'display': 'inline-block'}        
        ),
    ]),
    dcc.Markdown(''' --- '''),

    html.H1('Cumulative Returns per Position Over Time'),
    dcc.Graph(id='cumugraph',
        figure={
            'data': [
                go.Bar(
                    x = data['Ticker'][0:20],
                    y = data['Stock Gain / (Loss)'][0:20],
                    name = 'Ticker Total Return ($)',
                    yaxis='y'
                ),
                go.Bar(
                    x = data['Ticker'][0:20],
                    y = data['SP 500 Gain / (Loss)'][0:20],
                    name = 'SP500 Total Return ($)',
                    yaxis='y'
                ),
                go.Scatter(
                    x = data['Ticker'][0:20],
                    y = data['ticker return'][0:20],
                    name = 'Ticker Total Return (%)',
                    yaxis='y2'
                )
            ],
            'layout': go.Layout(title='Gain / (Loss) and Total Return vs S&P500',
                showlegend=True,
                barmode = 'group',
                xaxis={'title': 'Ticker'},
                yaxis={'title': 'Gain / (Loss) ($)', 'side':'left'},
                yaxis2={'title':'Ticker Return', 'side':'right', 'tickformat':".1%", 'overlaying':'y'},
                legend={'x': 0.75, 'y': 1.2}
            )
        }
    ),

    dcc.Markdown(''' --- '''),
    html.H1('Total Cumulative Investments by Portfolio Over Time'),
    dcc.Graph(id='totalcumu',
        figure={
            'data':[
                go.Scatter(
                    x= data['Ticker'][0:20],
                    y = data['Cum Invst'],
                    name = 'Cum Invest'
                ),
                go.Scatter(
                    x=data['Ticker'][0:20],
                    y=data['Cum SP Returns'],
                    name = 'Cum SP 500 Returns'
                ),
                go.Scatter(
                    x=data['Ticker'],
                    y=data['Cum Ticker Returns'],
                    name = 'Cum Ticker Returns'
                )
            ],
            'layout': go.Layout(title='Cumulative Investment Returns',
                barmode='group',
                xaxis={'title':'Ticker'},
                yaxis={'title': 'Returns ($)'}
            )
        }
    ),
    dcc.Graph(id='totalcumu2',
        figure={
            'data':[
                go.Bar(
                    x=data['Ticker'],
                    y=data['Cum Invst'],
                    name='Cum Invest'
                ),
                go.Bar(
                    x=data['Ticker'],
                    y=data['Cum SP Returns'],
                    name='Cum SP 500 Returns'
                ),
                go.Bar(
                    x=data['Ticker'],
                    y=data['Cum Ticker Returns'],
                    name='Cum Ticker Returns'
                ),
                go.Scatter(
                    x=data['Ticker'],
                    y=data['Cum Ticker ROI Mult'],
                    name='Cum ROI Mult',
                    yaxis='y2'
                )
            ],
            'layout':go.Layout(title='Total Cumulative Investments | ROI Multiple, Over Time',
                barmode='group',
                xaxis={'title':'Ticker'},
                yaxis={'title':'Returns ($)'},
                yaxis2={'title':'Cum ROI Mult', 'overlaying':'y', 'side':'right'},
                legend = {'x':0.75, 'y':1.2}
            )
        }, style={'width':'50%'}
    ),
    dcc.Markdown(''' --- '''),
    html.H1(),
    dcc.Graph(id='price-graph',
        figure={
            'data':[
                go.Bar(
                    x=data['Ticker'][0:20],
                    y=data['Pct off High'][0:20],
                    name='Pct off High'
                ),
                go.Scatter(
                    x=data['Ticker'][0:20],
                    y=[-0.25]*20,
                    name='Trailing Stop Marker',
                    mode='lines',
                    line={'color':'red'}
                )
            ],
            'layout': go.Layout(title='Adj Close % off of High Since Purchased',
                barmode='group',
                xaxis={'title':'Ticker'},
                yaxis={'title':'% Below High Since Purchased', 'tickformat':".2%"},
                legend = {'x':0.8, 'y':1.2}
            ),
            
        }, style={'width':'50%'}
    ),

])

@app.callback(Output('compare-graph', 'figure'), [Input('submit-button', 'n_clicks')], 
    [State('my-tickers', 'value'), State('my-date-picker', 'start_date'), State('my-date-picker', 'end_date')])
def update_graph(n_clicks, ticker, start_date, end_date):
    start = dt.strptime(start_date[:10], '%Y-%m-%d')
    end = dt.strptime(end_date[:10], '%Y-%m-%d')
    traces = []
    for tic in ticker:
        df = web.DataReader(tic, 'yahoo', start, end)
        traces.append({'x':df.index, 'y':(df.Close/df.Close.iloc[0])-1, 'name': tic})
    fig = {
		'data': traces,
		'layout': {'title':ticker}
	}
    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8000) 