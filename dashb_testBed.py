import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import mysql.connector
import numpy as np
import time
from datetime import datetime
from datetime import timedelta
import os
import csv
import classes

app = dash.Dash(__name__, title='Core Network Dashboard')
server = app.server

# DB Connection Parameters
dbPara = classes.coreDbCredentials()

graphTitleFontSize = 18
tabbedMenuStyle = {'background-color': 'black', 'color': 'white', 'border-bottom-color': 'black'}
tabbedMenuSelectedStyle = {'background-color': 'grey', 'color': 'white', 'border-bottom-color': 'black', 'border-top-color': 'white'}

app.layout = html.Div(
    children=[
        # Header & tabbed menu
        html.Div(
            className = 'titleHeaderContainer',
            children = [
                html.H1(
                    id = 'dashboardTitle',
                    children = 'MME Logs'
                ),
                dcc.Tabs(
                    id = 'tabsContainer',
                    value = 'Engineering Dashboard',
                    style = {'height':'45px'},
                    children = [
                        dcc.Tab(
                            label = 'Engineering Dashboard', 
                            value = 'Engineering Dashboard', 
                            style = tabbedMenuStyle,
                            selected_style = tabbedMenuSelectedStyle
                        ),
                        dcc.Tab(
                            label = 'Top Worst Reports', 
                            value = 'Top Worst Reports', 
                            style = tabbedMenuStyle,
                            selected_style = tabbedMenuSelectedStyle
                        ),
                        dcc.Tab(
                            label = 'Network Check', 
                            value = 'Network Check', 
                            style = tabbedMenuStyle,
                            selected_style = tabbedMenuSelectedStyle
                        ),
                        dcc.Tab(
                            label = 'Graph Insight', 
                            value = 'Graph Insight', 
                            style = tabbedMenuStyle,
                            selected_style = tabbedMenuSelectedStyle
                        )
                    ]
                )
            ]
        ),
        # Engineering Dashboard Tab
        html.Div(
            id = 'graphGridContainer',
            children = [
                html.Div(
                    id = 'dataTypeDropdownGridElement',
                    children = [
                        dcc.Dropdown(
                            id = 'dataTypeDropdown',
                            options = [
                                {'label':'CS Call Setup Success Rate', 'value':'CS Call Setup Success Rate'}, 
                                {'label':'PS Call Setup Success Rate', 'value':'PS Call Setup Success Rate'}, 
                                {'label':'CS Drop Call Rate', 'value':'CS Drop Call Rate'}, 
                                {'label':'PS Drop Call Rate', 'value':'PS Drop Call Rate'}, 
                                {'label':'Assignment Success Rate', 'value':'Assignment Success Rate'}, 
                                {'label':'Location Update Success Rate', 'value':'Location Update Success Rate'}
                            ],
                            value = 'PS Drop Call Rate',
                            style = {
                                'width': '100%', 
                                'font-size': str(graphTitleFontSize) + 'px', 
                                'text-align': 'center'
                            }
                        )
                    ]
                ),
                html.Div(
                    id = 'timeFrameDropdownGridElement',
                    children = [
                        dcc.Dropdown(
                            id='timeFrameDropdown',
                            options=[
                                {'label':'1 Hour', 'value':'1'}, 
                                {'label':'3 Hours', 'value':'3'}, 
                                {'label':'8 Hours', 'value':'8'}, 
                                {'label':'24 Hours', 'value':'24'}
                            ],
                            # value var is the default value for the drop down.
                            value='1',
                            style={
                                'width': '100%', 
                                'font-size': str(graphTitleFontSize) + 'px', 
                                'text-align': 'center'
                            }
                        )
                    ]
                ),
                # Graphs
                html.Div(
                    className = 'gridElement',
                    id = 'mmePieGraphGridContainer',
                    children = [
                        'MME Logs',
                        dcc.Graph(
                            id = 'mmeSessionEventsPie'
                        )
                    ]
                )
            ]
        ),
        # Top Worst Reports Tab
        html.Div(
            id = 'datatableGridContainer'
        ),
        # Network Check Tab
        html.Div(
            id = 'networkCheckGridContainer'
        ),
        # Graph Insight Tab (WIP)
        html.Div(
            id = 'graphInsightContainer'
        ),
        dcc.Interval(
            id='graphUpateInterval',
            # interval is expressed in milliseconds
            interval=120000, 
            n_intervals=0
        )
    ]
)

# We pass value from the time frame dropdown because it gets updated everytime you change the seleccion on the drop down.
@app.callback(
        Output('mmeSessionEventsPie', 'figure')
    , 
    [
        # We use the update interval function and tabbed menu to trigger callback
        Input('graphUpateInterval', 'n_intervals'), 
        Input('tabsContainer', 'value'), 
        Input('timeFrameDropdown', 'value'), 
        Input('dataTypeDropdown', 'value')
    ]
)
def updateGraphData_bsc(currentInterval, selectedTab, timeFrameDropdown, dataTypeDropdown):
    #gsmGraphValueConversionDict = {'CS Call Setup Success Rate':'cssr', 'PS Call Setup Success Rate':'edgedlssr', 'CS Drop Call Rate':'dcr', 'PS Drop Call Rate':'edgedldcr', 'Assignment Success Rate':'assignmentsuccessrate', 'Location Update Success Rate':'luupdatesr'}
    #umtsGraphValueConversionDict = {'CS Call Setup Success Rate':'csconnectionsuccessrate', 'PS Call Setup Success Rate':'psrtsuccessrate', 'CS Drop Call Rate':'csdropcallrate', 'PS Drop Call Rate':'psdropcallrate', 'Assignment Success Rate':'rrcconnectionsuccessrate', 'Location Update Success Rate':'pagingsuccessrate'}
    hoursDelta = int(timeFrameDropdown)
    # starttime is the current date/time - daysdelta
    startTime = (datetime.now() - timedelta(hours=hoursDelta)).strftime("%Y/%m/%d %H:%M:%S")
    # Connect to DB
    connectr = mysql.connector.connect(user=dbPara.dbUsername, password=dbPara.dbPassword, host=dbPara.dbServerIp, database=dbPara.schema)
    # Connection must be buffered when executing multiple querys on DB before closing connection.
    pointer = connectr.cursor(buffered=True)
    pointer.execute('select Times,Details from mme_logs.session_event where Times > \'' + str(startTime) + '\';')
    #pointer.execute('select Times,Details from mme_logs.session_event;')
    queryRaw = pointer.fetchall()
    queryPayload = np.array(queryRaw)
    mmeSessionEventsDataframe = pd.DataFrame(queryPayload, columns = ['Times', 'Details'])
    mmeSessionEventsDataframe = mmeSessionEventsDataframe.groupby().count()


    mmeSessionEventsPie = px.pie(mmeSessionEventsDataframe, names = 'Times', values = 'reasonQty')
    mmeSessionEventsPie.update_layout(
        plot_bgcolor='#000000', 
        paper_bgcolor='#000000', 
        font_color='#FFFFFF',
        title_font_size=graphTitleFontSize,
        font_size=graphTitleFontSize, 
        title='NE Out of Service'
    )
    mmeSessionEventsPie.update_traces(textinfo='value')
    # Close DB connection
    pointer.close()
    connectr.close()
    return mmeSessionEventsPie

# Callback to hide/display selected tab
@app.callback([
    Output('graphGridContainer', 'style'),
    Output('datatableGridContainer', 'style'), 
    Output('networkCheckGridContainer', 'style'),
    Output('graphInsightContainer', 'style')
    ], 
    Input('tabsContainer', 'value')
)
def showTabContent(currentTab):
    if currentTab == 'Engineering Dashboard':
        return {'display':'grid'}, {'display':'none'}, {'display':'none'}, {'display':'none'}
    elif currentTab == 'Top Worst Reports':
        return {'display':'none'}, {'display':'grid'}, {'display':'none'}, {'display':'none'}
    elif currentTab == 'Network Check':
        return {'display':'none'}, {'display':'none'}, {'display':'grid'}, {'display':'none'}
    else:
        return {'display':'none'}, {'display':'none'}, {'display':'none'}, {'display':'inline'}

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port='5010')
