from dash import Dash, html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
px.defaults.template = "ggplot2"

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

import json 
import pandas as pd
import numpy as np
import QueryOptionsDB as qdb
import QueryYF as qyf
import datetime as dte

external_stylesheets = [dbc.themes.BOOTSTRAP, "assets/optionExplorer_dashStyles.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets,  meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],)
# app = Dash(__name__)

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
                            html.H6("Look Smart While You Gamble Your Life Savings"),
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

# currentTime = dte.datetime.utcnow()
# currentTime = dte.datetime(2021,3,15,10,0)
# origTime = dte.datetime(2021,3,1,15,0)
# currentTime = dte.datetime(2022,4,15,0,0)
# origTime = dte.datetime(2022,1,1,0,0)
# availTickers = qdb.getTickers(origTime,currentTime)
# ticker = "MSFT"
# [Price,Calls,Puts] = qdb.queryDB(ticker,origTime,currentTime)

def plotTitles():
    return(dbc.Row(
            id="plot-titles",
            children = [dbc.Col(
                            [
                                html.H5("Calls",style={'textAlign': 'center',"font-weight": "bold"})
                            ],
                            width = 6, align="center"
                        ),
                        dbc.Col(
                            [
                                html.H5("Puts",style={'textAlign': 'center', "font-weight": "bold"})
                            ],
                            width = 6, align="center"
                        ),
                    ],style={"margin-left": "50px", "margin-right": "200px", "margin-bottom": "-100px"}
                )
    )
    
def tickerDropdown():
    return html.Div(id="available-tickers",style={"width": "25%","margin": "25px", "font-size": "20px","font-weight": "bold"},)

def rangeSlider():
    return html.Div(id="date-slider", style={"margin-left": "100px", "margin-right": "250px", "margin-top": "50px","margin-bottom": "50px"},)

def dateDropdown():
    return html.Div(
                [
                    dcc.DatePickerRange(id="date-select-dropdown",
                        # start_date_placeholder_text="Start Period",
                        # end_date_placeholder_text="End Period",
                        calendar_orientation='vertical',
                        updatemode = "bothdates",
                        min_date_allowed=dte.date(2021, 1, 1),
                        max_date_allowed=dte.datetime.today(),
                        initial_visible_month=dte.date(2021, 1, 1),
                        start_date = dte.date(2021, 2, 1),
                        end_date=dte.date(2021, 4, 1),
                    )
                ],
                style={"width": "50%","margin": "25px"},
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
                    html.Div([dcc.Graph(id="option-chain-graph",style={"margin-top":"5px"})]),# "margin-left":"50px","margin-right":"120px"})]),
                    rangeSlider(),
                    html.Br(),html.Br(),html.Br(),
                    dcc.Store(id='option-data-subset')
            ]
        )
    ]
)

@app.callback(
    Output('available-tickers', 'children'),
    Input('date-select-dropdown', 'start_date'),
    Input('date-select-dropdown', 'end_date'))
def createTickerDropdown(start_date, end_date):
        if start_date is not None:
            start_date_object = dte.datetime.fromisoformat(start_date)
        if end_date is not None:
            end_date_object =  dte.datetime.fromisoformat(end_date)
        validTickers = qdb.getTickers(start_date_object,end_date_object)
        return(dcc.Dropdown(
                                options = validTickers,
                                value = "SPY"
                        ),
        )
          
@app.callback(
    Output('option-data-subset', 'data'),
    Input('available-tickers', 'children'),
    Input('date-select-dropdown', 'start_date'),
    Input('date-select-dropdown', 'end_date'))
def getSubsetData(ticker, start_date, end_date):
    if start_date is not None:
        start_date_object = dte.datetime.fromisoformat(start_date)
    if end_date is not None:
        end_date_object =  dte.datetime.fromisoformat(end_date)
    tickerQuery = ticker[0]['props']['value']
    [Price,Calls,Puts] = qdb.queryDB(tickerQuery,start_date_object,end_date_object)
    datasets = {'Price': Price, 'Calls': Calls, 'Puts': Puts}
    
    return datasets

@app.callback(
    Output('date-slider', 'children'),
    Input('option-data-subset', 'data'))
def createDateSlider(opData):
        validDates  = pd.Series(opData['Calls'].keys())
        return(dcc.Slider(
                validDates.index[0], validDates.index[-1], step=1,
                value=validDates.index[-1],
                marks={day: {"label": str(str(validDates[day].day) + "-" + str(validDates[day].month) + "-" +  str(validDates[day].year)
                                          ), "style": {"transform": "rotate(45deg)", "fontSize": "20px", "margin-top": "25px"}
                                          } for day in validDates.index},
                verticalHeight = 1200,
                id="date-slider"
                )
        )

@app.callback(
    Output("option-chain-graph", "figure"),
    Input('option-data-subset', 'data'),
    Input("date-slider", "children"))
def plotCallsPuts(opData,value):
    validDates  = pd.Series(opData['Calls'].keys())

    plotCalls = opData['Calls'][validDates[value]]
    plotPuts = opData['Puts'][validDates[value]]
    price = opData['Price']

    dateToValC = plotCalls["Expiry"].map(pd.Series(data=np.arange(len(plotCalls)), index=plotCalls["Expiry"].values).to_dict())
    dateToValP = plotPuts["Expiry"].map(pd.Series(data=np.arange(len(plotPuts)), index=plotPuts["Expiry"].values).to_dict())
    # bubSizeC = 10*plotCalls["Open Interest"]/plotCalls["Open Interest"].max()
    # bubSizeP = 10*plotPuts["Open Interest"]/plotPuts["Open Interest"].max()

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing = 0)#, subplot_titles=["Calls", "Puts"])
    fig.add_trace(go.Scatter(x=plotCalls["Strike"]-price[validDates[value]],y=plotCalls["Ask"], mode = "markers", 
                                    text = plotCalls["Open Interest"],
                                    opacity=0.7,
                                    marker = dict(color=dateToValC, 
                                                size = 18,
                                                colorscale=px.colors.sequential.Sunset,
                                                # colorbar=dict(thickness=25, tickvals=[dateToValC.iloc[0], dateToValC.iloc[-1]], 
                                                #                             ticktext=[plotCalls["Expiry"].iloc[0], plotCalls["Expiry"].iloc[-1]]),
                                                line=dict(
                                                        color="white",
                                                        width=1)                                                                                                                                                                      )
                                    ), row = 1, col = 1
                    )
    fig.add_trace(go.Scatter(x=plotPuts["Strike"]-price[validDates[value]],y=plotPuts["Ask"], mode = "markers", 
                                    text = plotPuts["Open Interest"],
                                    opacity=0.7,
                                    marker = dict(color=dateToValP, 
                                                size = 18,
                                                colorbar_title = "Expiry",
                                                colorscale=px.colors.sequential.Sunset, 
                                                colorbar=dict(thickness=25, tickvals=[dateToValP.iloc[0], dateToValP.iloc[-1]], 
                                                                            ticktext=[plotPuts["Expiry"].iloc[0], plotPuts["Expiry"].iloc[-1]]),
                                                line=dict(
                                                        color="white",
                                                        width=1)    
                                                )
                                    ), row = 1, col = 2
                    )
    fig.update_yaxes(type="log",dtick=1,minor=dict(ticks="inside", ticklen=3, showgrid=True), title_text="Ask")
    fig.update_xaxes(title_text="Strike - Stock Price")
    fig.update_layout(transition_duration=500,height=1000,
                      showlegend = False,
                      plot_bgcolor= "#1e2130", 
                      paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Helvetica, sans-serif",
                                size=18,  
                                color="white"
                                )
                      )
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)