from dash import Dash, html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
px.defaults.template = "ggplot2"

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

# from sklearn.cluster import OPTICS

import json 
import pandas as pd
import numpy as np
import QueryOptionsDB as qdb
import QueryYF as qyf
import datetime as dte

external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/optionExplorer_dashStyles.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets,  meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],)
# app = Dash(__name__)

defaultTicker = "AAPL"

def appHeader():
    return html.Div( 
        id="banner",
        className="banner",
        children=[
            html.Div(id="banner-logo",
                    children=[                    
                        html.A(
                            html.Img(id="logo", src=app.get_asset_url("LogisticMap.png")),
                            href="https://www.mathew-marzanek.com/",
                        ),
                        html.Div(
                            id="banner-text",
                            children=[
                                html.H5("Options Unchained"),
                                html.H6("Intuitive Market Data For Retail Traders"),
                            ],
                    )
                ],
            ),

            html.Div(
                id="banner-links",
                children=[
                    html.A(
                        html.Button(children="Owner Info"),
                        href="https://www.mathew-marzanek.com/",
                    ),
                    # html.Button(
                    #     id="learn-more-button", children="LEARN MORE", n_clicks=0
                    # ),
                ],
            ),
        ],
    )

def plotTitles():
    return(dbc.Row(
            id="plot-titles",
            children = [dbc.Col(
                            [
                                html.H5("Calls",style={'textAlign': 'center',"font-weight": "bold"})
                            ],
                            width = 5, align="center"
                        ),
                        dbc.Col(
                            [
                                html.H5("Puts",style={'textAlign': 'center', "font-weight": "bold"})
                            ],
                            width = 7, align="center"
                        ),
                    ],style={"margin-left": "100px", "margin-right": "90px", "margin-bottom": "-100px"}
                )
    )

def tickerDropdown():
    return html.Div(
                    [
                        html.H6("Select Ticker"),
                        dcc.Dropdown(id="available-tickers",
                                    value = defaultTicker
                                    )
                    ],
                    style={"width": "25%","margin": "20px", "font-size": "16px","font-weight": "bold"},
                )

def rangeSlider():
    return html.Div(
                    [
                        html.H6("Available Historical Dates"),
                        dcc.Slider(id="date-slider",
                                    min=0, max=30, step=1,
                                    value=30,
                                    marks=None,
                                    verticalHeight = 1200
                                    )
                    ],
                    style={"margin-left": "100px", "margin-right": "250px", "margin-top": "50px","margin-bottom": "50px"},
                )


def dateDropdown():
    return html.Div(
                [
                    html.H6("Select Historical Date Range"),
                    dcc.DatePickerRange(id="date-select-dropdown",
                        # start_date_placeholder_text="Start Period",
                        # end_date_placeholder_text="End Period",
                        calendar_orientation='vertical',
                        updatemode = "bothdates",
                        min_date_allowed=dte.date(2023, 3, 23),
                        max_date_allowed=dte.datetime.today(),
                        initial_visible_month=dte.datetime.today(),
                        start_date= dte.datetime.today() - dte.timedelta(days=10),
                        end_date=dte.datetime.today(),
                        style = {
                         'background-color': '#13151f',
                         'color': '#13151f'
                        } 
                    )
                ],
                style={"width": "50%","margin": "20px"},
        )

def priceHistory():
    return html.Div([
            html.H6("Price History"),
            dcc.Loading(dcc.Graph(id="timeHistory",style={"margin-top":"-75px", "margin-left":"-75px"}), type="circle")
            ]
        )

def supplementaryPlots():
    return(dbc.Row(
            id="sup-plots",
            children = [
                        priceHistory()
                    ],style={"margin-top": "75px","margin-left": "90px", "margin-right": "25px", "margin-bottom": "25px"}
                )
    )

def userInputs():
    return(dbc.Row(
            id="user-inputs",
            children = [
                        tickerDropdown(),
                        dateDropdown()
                    ],style={"margin-left": "50px", "margin-right": "25px", "margin-bottom": "25px"}
                )
    )

app.layout = html.Div(
    id="big-app-container",
    children=[
        appHeader(),
        html.Div(
            id="app-container",
            children=[
                    userInputs(),
                    plotTitles(),
                    html.Div([dcc.Loading(dcc.Graph(id="option-chain-graph",style={"margin-top":"5px"}), type="circle")]),# "margin-left":"50px","margin-right":"120px"})]),
                    # html.Div(id="date-slider", style={"margin-left": "100px", "margin-right": "250px", "margin-top": "50px","margin-bottom": "50px"},),
                    rangeSlider(),
                    # html.Br(),html.Br(),html.Br(),
                    supplementaryPlots(),
                    html.Div([dcc.Loading(dcc.Graph(id="option-oi-graph",style={"margin-top":"-75px"}), type="circle")]),
                    dcc.Store(id='option-data-subset'),
            ]
        )
    ]
)

@app.callback(
    Output('available-tickers', 'options'),
    Input('date-select-dropdown', 'start_date'),
    Input('date-select-dropdown', 'end_date'))
def createTickerDropdown(start_date, end_date):
        if start_date is not None:
            start_date_object = dte.datetime.fromisoformat(start_date)
        if end_date is not None:
            end_date_object =  dte.datetime.fromisoformat(end_date)
        validTickers = qdb.getTickers(start_date_object,end_date_object)
        if len(validTickers) == 0:
            return(["No available tickers for selected dates"])
        elif validTickers is not None:
            validTickers.sort()
            return validTickers
        else:
            return validTickers
        
          
@app.callback(
    Output('option-data-subset', 'data'),
    Input('available-tickers', 'value'),
    Input('date-select-dropdown', 'start_date'),
    Input('date-select-dropdown', 'end_date'))
def getSubsetData(ticker, start_date, end_date):
    if start_date is not None:
        start_date_object = dte.datetime.fromisoformat(start_date)
    if end_date is not None:
        end_date_object =  dte.datetime.fromisoformat(end_date)
    tickerQuery = ticker#['props']['value']
    [Price,Calls,Puts] = qdb.queryDB(tickerQuery,start_date_object,end_date_object)    
    datasets = {'Price': Price, 'Calls': Calls, 'Puts': Puts}
    return json.dumps(datasets)

# @app.callback(
#     Output('option-data-subset', 'data'),
#     Input('available-tickers', 'options'),
#     Input('date-select-dropdown', 'start_date'),
#     Input('date-select-dropdown', 'end_date'))
# def getSubsetData(ticker, start_date, end_date):
#     if start_date is not None:
#         start_date_object = dte.datetime.fromisoformat(start_date)
#     if end_date is not None:
#         end_date_object =  dte.datetime.fromisoformat(end_date)
#     tickerQuery = ticker#['props']['value']
#     [Price,Calls,Puts] = qdb.queryDB(tickerQuery,start_date_object,end_date_object)    
#     datasets = {'Price': Price, 'Calls': Calls, 'Puts': Puts}
#     return json.dumps(datasets)

@app.callback(Output('date-slider', 'min'),
              Output('date-slider', 'max'),
              Output('date-slider', 'value'),
              Output('date-slider', 'marks'),
              Input('option-data-subset', 'data'))
def update_slider(opData):
    datasets = json.loads(opData)
    if len(list(datasets['Calls'])) != 0:
        validDates  = pd.Series(datasets['Calls'].keys())
        min = validDates.index[0]
        max = validDates.index[-1]
        value=validDates.index[-1]
        marks={day: {"label": validDates[day].split(" ")[0], 
                    "style": {"transform": "rotate(45deg)", "fontSize": "15px", "margin-top": "25px","white-space":"nowrap"}
                                } for day in validDates.index}
        return min, max, value, marks
    else:
        min = 0
        max = 1
        value=1
        marks={0:"No data found", 1:"No data found"}
        return min, max, value, marks

@app.callback(
    Output("option-chain-graph", "figure"),
    Input('option-data-subset', 'data'),
    Input("date-slider", "value"))
def plotCallsPuts(opData,value):
    if value is None:
         value = 0
    datasets = json.loads(opData)
    if len(list(datasets['Calls'])) != 0:
        validDates  = pd.Series(datasets['Calls'].keys())
        plotCalls = pd.read_json(datasets['Calls'][validDates[value]], orient='split')
        plotPuts = pd.read_json(datasets['Puts'][validDates[value]], orient='split')
        curntPrice = datasets['Price'][validDates[value]]
        dateToValC = plotCalls["Expiry"].map(pd.Series(data=np.arange(len(plotCalls)), index=plotCalls["Expiry"].values).to_dict())
        dateToValP = plotPuts["Expiry"].map(pd.Series(data=np.arange(len(plotPuts)), index=plotPuts["Expiry"].values).to_dict())
        # bubSizeC = 10*plotCalls["Open Interest"]/plotCalls["Open Interest"].max()
        # bubSizeP = 10*plotPuts["Open Interest"]/plotPuts["Open Interest"].max()

        fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing = 0.05)#, subplot_titles=["Calls", "Puts"])

        fig.add_trace(go.Scatter(x=plotCalls["Strike"]-curntPrice,y=plotCalls["Ask"], mode = "markers", 
                                        opacity=0.7,
                                        name="Contract",
                                        text=plotCalls.index,
                                        marker = dict(color=dateToValC, 
                                                    size = 18,
                                                    colorscale=px.colors.sequential.dense,
                                                    # colorbar=dict(thickness=25, tickvals=[dateToValC.iloc[0], dateToValC.iloc[-1]], 
                                                    #                             ticktext=[plotCalls["Expiry"].iloc[0], plotCalls["Expiry"].iloc[-1]]),
                                                    line=dict(
                                                            color="white",
                                                            width=1)                                                                                                                                                                      )
                                        ), row = 1, col = 1
                        )
        fig.add_trace(go.Scatter(x=plotPuts["Strike"]-curntPrice,y=plotPuts["Ask"], mode = "markers", 
                                        name="Contract",
                                        text=plotPuts.index,
                                        opacity=0.7,
                                        marker = dict(color=dateToValP, 
                                                    size = 18,
                                                    colorscale=px.colors.sequential.dense, 
                                                    colorbar=dict(title=dict(text="Expiry", side="right"), thickness=25, tickvals=[dateToValP.iloc[0], dateToValP.iloc[-1]], 
                                                                                ticktext=[plotPuts["Expiry"].iloc[0].split("T")[0], plotPuts["Expiry"].iloc[-1].split("T")[0]]),
                                                    line=dict(
                                                            color="white",
                                                            width=1)    
                                                    )
                                        ), row = 1, col = 2
                        )
        fig.update_yaxes(type="log",dtick=1,minor=dict(ticks="inside", ticklen=3, showgrid=True))
        fig.update_yaxes(title_text="Ask", row=1, col=1)
        fig.update_xaxes(title_text="Strike - Stock Price")
        fig.update_layout(transition_duration=500,height=700,
                        # hovermode="x unified",
                        showlegend = False,
                        plot_bgcolor= "#1e2130", 
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Helvetica, sans-serif",
                                    size=14,  
                                    color="white"
                                    )
                        )
        return fig
    else:
        fig = make_subplots(rows=1, cols=1, shared_yaxes=True, horizontal_spacing = 0)#, subplot_titles=["Calls", "Puts"])
        fig.update_yaxes(visible=False)
        fig.update_xaxes(visible=False)
        fig.update_layout(transition_duration=500,height=100,
                        showlegend = False,
                        xaxis={"visible":False},
                        yaxis={"visible":False},
                        title="No Data Found, Please Reselect Date Range",
                        plot_bgcolor= "#1e2130", 
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Helvetica, sans-serif",
                                    size=14,  
                                    color="white"
                                    )
                        )
        return fig

@app.callback(
    Output("option-oi-graph", "figure"),
    Input('option-data-subset', 'data'),
    Input("date-slider", "value"))
def plotOI(opData,value):
    if value is None:
         value = 0
    datasets = json.loads(opData)
    if len(list(datasets['Calls'])) != 0:
        validDates  = pd.Series(datasets['Calls'].keys())
        plotCalls = pd.read_json(datasets['Calls'][validDates[value]], orient='split')
        plotPuts = pd.read_json(datasets['Puts'][validDates[value]], orient='split')
        curntPrice = datasets['Price'][validDates[value]]
        
        plotCalls['HistDate'] = dte.datetime.fromisoformat(validDates[value])
        plotPuts['HistDate'] = dte.datetime.fromisoformat(validDates[value])
        daysToExpiryC = (pd.to_datetime(plotCalls['Expiry']).dt.tz_localize('UTC') - plotCalls['HistDate'].dt.tz_localize('UTC').dt.normalize()).dt.days
        daysToExpiryP = (pd.to_datetime(plotPuts['Expiry']).dt.tz_localize('UTC') -  plotPuts['HistDate'].dt.tz_localize('UTC').dt.normalize()).dt.days

        fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing = 0.05, subplot_titles=["Calls", "Puts"])

        fig.add_trace(go.Heatmap(z=plotCalls["Open Interest"], y = daysToExpiryC.astype(str), x=plotCalls["Strike"]-curntPrice,
                                colorscale=[[0,"rgba(237,248,251, 0)"], [0.25,"rgba(179,205,227,100)"], [0.75,"rgba(140,150,198,175)"], [1.0,"rgba(136,65,157,255)"]],
                                zmin=0, zmax=plotCalls["Open Interest"].max().round(),
                                xperiod = "M",
                                showscale=False
                                ), row = 1, col = 1
        )
        fig.add_trace(go.Heatmap(z=plotPuts["Open Interest"], y =daysToExpiryP.astype(str), x=plotPuts["Strike"]-curntPrice,
                                colorscale=[[0,"rgba(237,248,251, 0)"], [0.25,"rgba(179,205,227,100)"], [0.75,"rgba(140,150,198,175)"], [1.0,"rgba(136,65,157,255)"]],
                                zmin=0, zmax=plotCalls["Open Interest"].max().round(),
                                xperiod = "M",
                                colorbar=dict(title=dict(text="Open Interest", side="right"), thickness=25)
                                ), row = 1, col = 2
        )

        fig.update_xaxes(title_text="Strike - Stock Price")#, showgrid= False)
        fig.update_yaxes(tickvals = daysToExpiryC.unique())#, type="log", dtick=1)#, showgrid= False) 
        fig.update_yaxes(title_text="Days to Expiry", row=1, col=1)
        fig.update_layout(transition_duration=500,height=700,
                        showlegend = False,
                        plot_bgcolor= "#1e2130", 
                        # plot_bgcolor= "rgba(0,0,0,255)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Helvetica, sans-serif",
                                    size=14,  
                                    color="white"
                                    ),                        
                        )
        return fig

@app.callback(
    Output("timeHistory", "figure"), 
    Input('available-tickers', 'value'),
    Input('date-select-dropdown', 'start_date'),
    Input('date-select-dropdown', 'end_date'))
def display_candlestick(ticker, start_date, end_date):
    if start_date is not None:
        start_date_object = dte.datetime.fromisoformat(start_date)
    if end_date is not None:
        end_date_object =  dte.datetime.fromisoformat(end_date)

    df = qyf.getPriceHistory(end_date_object, start_date_object, ticker)
    fig = go.Figure(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close']
    ))

    fig.update_layout(xaxis_rangeslider_visible=False,
                        transition_duration=150, width = 500, height=350,
                        plot_bgcolor= "#1e2130", 
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Helvetica, sans-serif",
                                    size=14,  
                                    color="white"
                                    ),
                        )

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)