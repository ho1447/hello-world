import dash, json 
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from scrapingstock import saveSp500StocksInfo, getfinancialreportingdf, includecalcvariablesdf, save_self_stocks_info, getetfdf, getbettermentlist
from checkeligibility import checkeligibility
from decision import getprice
from pandas_datareader import data
from datetime import datetime as dt
import numpy as np
import dash_table
import plotly.graph_objects as go
from plotly.tools import mpl_to_plotly

app = dash.Dash(__name__)
server = app.server


app.layout = html.Div(
    children=[
        html.H1('ETF Investing'),   
        html.Div(
            id='app-container',
            children=[
                #left column
                html.Div(
                    id='left-col',
                    className='four columns',
                    children=[
                        #dropdown to choose stk ticker
                        html.Div(
                            children=[    
                                html.H2('Choose a stock ticker'),
                                dcc.Dropdown(id='my-dropdown', options=getbettermentlist(), value='VEA'),                            
                            ],
                            className='etf-dropdown',
                            style={'width':'100%','display': 'inline-block'}
                        ),
                    ],
                    style={'width':'30%'}
                ),
                #right column
                html.Div(
                    id='right-col',
                    className='eight columns',
                    children=[ 
                        #table of critical values and ratios
                        html.H2('Critical Values and Ratios'),
                        html.Div(
                            children=[
                                html.Table(id='my-table'),               
                            ],
                            className='crit-values-table',
                            style={'display': 'inline-block','text-align': 'left'}
                        ),
                        #graph of stk price
                        html.Div(
                            children=[
                                html.H2('ETF 5-year price graph'),
                                dcc.Graph(id='my-graph'),
                            ],
                            className='stk-graph',
                        ),
                    ],
                    style={'display':'inline-block', 'width':'60%'}
                ),  
            ]
        )
        
    ]
)



#stocks graph
@app.callback(Output('my-graph', 'figure'), [Input('my-dropdown', 'value')])
def graphing(selectedValue):
    stockPricedf = data.DataReader(selectedValue.strip(), 'yahoo', dt(2015,1,1), dt.now())
    return {
        'data': [{
            'x': stockPricedf.index,
            'y': stockPricedf.Close
        }]
    }

#critical values table
@app.callback(Output('my-table', 'children'), [Input('my-dropdown', 'value')])
def generate_table(selectedValue,max_rows=10):
    financialreportingdf = getetfdf(selectedValue.strip().lower()).reset_index()
    # Header
    return [html.Tr([html.Th(col) for col in financialreportingdf.columns])]+ [html.Tr([
        html.Td(financialreportingdf.iloc[i][col]) for col in financialreportingdf.columns
    ]) for i in range(min(len(financialreportingdf), max_rows))]




  
if __name__ == '__main__':
    app.run_server(debug=True)
