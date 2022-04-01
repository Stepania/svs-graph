# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

import dash
from dash import dash_table
from dash import html
from dash import dcc
import plotly.graph_objects as go
import plotly.express as px
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bisect import bisect_left, bisect_right
from jupyter_dash import JupyterDash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import cufflinks as cf
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import copy
import CropNBalFunctions as cnbf

# ## General components

CropCoefficients, EndUseCatagoriesDropdown, metFiles, MetDropDown, MonthIndexs = cnbf.Generalcomponents()

# ## Core crop model components

# +
Scallers = cnbf.Scallers 
StagePropns = cnbf.StagePropns

# Graphs scallers over thermal time series
Graph = plt.figure()
plt.plot(Scallers.loc[:,'scaller'])
plt.plot(Scallers.loc[:,'cover'])
plt.plot(Scallers.loc[:,'rootDepth'])
T_mat = 100
for p in StagePropns.index:
    plt.plot(StagePropns.loc[p,'PrpnTt']*T_mat,StagePropns.loc[p,'PrpnMaxDM'],'o',color='k')
    plt.text(StagePropns.loc[p,'PrpnTt']*T_mat+3,StagePropns.loc[p,'PrpnMaxDM'],p,verticalalignment='top')
    plt.plot([StagePropns.loc[p,'PrpnTt']*T_mat]*2,[0,Scallers.loc[round(StagePropns.loc[p,'PrpnTt'] * T_mat),'max']],'--',color='k',lw=1)
plt.ylabel('Relative DM accumulation')
plt.xlabel('Temperature accumulation')

# -

# ## Declair Global properties

CurrentConfig = cnbf.setCropConfig(["Lincoln","","","","",0,1,0,0,0,
                                dt.datetime.strptime('01-01-1900','%d-%m-%Y'),"Seed",
                                dt.datetime.strptime('01-02-1900','%d-%m-%Y'),"EarlyReproductive",[]])
CurrentConfig.to_pickle("CurrentConfig.pkl")
# Tt = pd.DataFrame()

# ## Graph constructors

# +
def CropNGraph(cropN,NComponentColors):
    NData = cropN.reset_index()
    fig = px.line(data_frame=NData,x='Date',y='Values',color='Component',color_discrete_sequence=NComponentColors,
                 )#range_x = [c['EstablishDate']-dt.timedelta(days=7),c['HarvestDate']+dt.timedelta(days=7)])
    fig.update_layout(title_text="Crop N", title_font_size = 30, title_x = 0.5, title_xanchor = 'center')
    fig.update_yaxes(title_text="Nitrogen (kg/ha)", title_font_size = 20)
    fig.update_xaxes(title_text=None)
    return fig

def CropWaterGraph(cropWater):
    NData = cropWater.reset_index()
    fig = px.line(data_frame=NData,x='Date',y='Values',color='Component',color_discrete_sequence=['brown','orange','red','green'],
                 )#range_x = [c['EstablishDate']-dt.timedelta(days=7),c['HarvestDate']+dt.timedelta(days=7)])
    fig.update_layout(title_text="Cover and Root Depth", title_font_size = 30, title_x = 0.5, title_xanchor = 'center')
    fig.update_yaxes(title_text="Cover (m2/m2) and depth (m)", title_font_size = 20)
    fig.update_xaxes(title_text=None)
    return fig


# -

# ## App layout and callbacks

# +
app = JupyterDash(external_stylesheets=[dbc.themes.SLATE])


app.layout = html.Div([
    dbc.Row([dbc.Col(html.H1("Field Location"), width=2 ,align='center'),
             dbc.Col(dcc.Dropdown(id="Location",options = MetDropDown,value='Lincoln'), width=3 ,align='center')]),
    dbc.Row([dbc.Col(dbc.Card(cnbf.CropInputs('Current',EndUseCatagoriesDropdown))),dbc.Col(dbc.Card())]),
    html.Br(),
    dbc.Row([dbc.Col(html.Button("Refresh",id="RefreshButton"),width=2,align='center')             ]),
    dbc.Row([dbc.Col(dbc.Card(dcc.Graph(id='CropUptakeGraph')),width=4),
             dbc.Col(dbc.Card(dcc.Graph(id='CropWaterGraph')),width=4)])
    ])

@app.callback(Output("Location",'value'),Input("Location",'value'))
def StateCrop(Location):
    cnbf.updateConfig(["Location"],[Location],"CurrentConfig.pkl")
    return Location

pos = 'Current'
@app.callback(Output(pos+"Group","children"),Output(pos+"Crop","children"),Output(pos+"Type","children"),Output(pos+"SaleableYield",'children'),
              Output(pos+"Units",'children'),Output(pos+"Product Type","children"), Output(pos+"FieldLoss","children"),Output(pos+"DressingLoss","children"),
              Output(pos+"MoistureContent","children"),Output(pos+"EstablishDate","children"), Output(pos+"EstablishStage",'children'),
              Output(pos+"HarvestDate", "children"),Output(pos+"HarvestStage",'children'),
              Input(pos+"End use DD","value"),Input(pos+"Group DD","value"),Input(pos+"Crop DD","value"), Input(pos+"Type DD","value"))
def ChangeCrop(EndUseValue, GroupValue, CropValue, TypeValue):
    return cnbf.UpdateCropOptions(EndUseValue, GroupValue, CropValue, TypeValue, CropCoefficients,pos)
    
@app.callback(Output(pos+"Defoliation Dates","children"), Input(pos+"EstablishDate DP",'date'), Input(pos+"HarvestDate DP",'date'), prevent_initial_call=True)
def DefoliationOptions(Edate, Hdate):
    defDates = dcc.Checklist(id=pos+"Def Dates",options=[])
    if (Edate != None) and (Hdate!= None):
        cropMonths = pd.date_range(dt.datetime.strptime(str(Edate).split('T')[0],'%Y-%m-%d'),
                                   dt.datetime.strptime(str(Hdate).split('T')[0],'%Y-%m-%d'),freq='MS')
        DefCheckMonths = [{'label':MonthIndexs.loc[i.month,'Name'],'value':i} for i in cropMonths]    
        defDates = dcc.Checklist(id=pos+"Def Dates", options = DefCheckMonths, value=[])
    return defDates

@app.callback(Output(pos+"EstablishDate DP",'date'),Input(pos+"EstablishDate DP",'date'), prevent_initial_call=True)
def StateCrop(EstablishDate):
    cnbf.updateConfig(["EstablishDate"],[dt.datetime.strptime(str(EstablishDate).split('T')[0],'%Y-%m-%d')],pos+"Config.pkl")
    return EstablishDate
@app.callback(Output(pos+"HarvestDate DP",'date'),Input(pos+"HarvestDate DP",'date'), prevent_initial_call=True)
def StateCrop(HarvestDate):
    cnbf.updateConfig(["HarvestDate"],[dt.datetime.strptime(str(HarvestDate).split('T')[0],'%Y-%m-%d')],pos+"Config.pkl")
    return HarvestDate
@app.callback(Output(pos+"SYInput",'value'),Input(pos+"SYInput",'value'), prevent_initial_call=True)
def StateCrop(SaleableYield):
    cnbf.updateConfig(["SaleableYield"],[SaleableYield],pos+"Config.pkl")
    return SaleableYield
@app.callback(Output(pos+"Units DD",'value'),Input(pos+"Units DD",'value'), prevent_initial_call=True)
def StateCrop(Units):
    cnbf.updateConfig(["UnitConverter"],[Units],pos+"Config.pkl")
    return Units
@app.callback(Output(pos+"FLInput",'value'),Input(pos+"FLInput",'value'), prevent_initial_call=True)
def StateCrop(FieldLoss):
    cnbf.updateConfig(["FieldLoss"],[FieldLoss],pos+"Config.pkl")
    return FieldLoss
@app.callback(Output(pos+"DLInput",'value'),Input(pos+"DLInput",'value'), prevent_initial_call=True)
def StateCrop(DressingLoss):
    cnbf.updateConfig(["DressingLoss"],[DressingLoss],pos+"Config.pkl")
    return DressingLoss
@app.callback(Output(pos+"MCInput",'value'),Input(pos+"MCInput",'value'), prevent_initial_call=True)
def StateCrop(MoistureContent):
    cnbf.updateConfig(["MoistureContent"],[MoistureContent],pos+"Config.pkl")
    return MoistureContent
@app.callback(Output(pos+"EstablishStage DD",'value'),Input(pos+"EstablishStage DD",'value'), prevent_initial_call=True)
def StateCrop(EstablishStage):
    cnbf.updateConfig(["EstablishStage"],[EstablishStage],pos+"Config.pkl")
    return EstablishStage
@app.callback(Output(pos+"HarvestStage DD",'value'),Input(pos+"HarvestStage DD",'value'), prevent_initial_call=True)
def StateCrop(HarvestStage):
    cnbf.updateConfig(["HarvestStage"],[HarvestStage],pos+"Config.pkl")
    return HarvestStage
@app.callback(Output(pos+'Def Dates', 'value'),Input(pos+'Def Dates','value'))
def setDefoliationDates(months):
    cnbf.updateConfig(["DefoliationDates"],[months],pos+"Config.pkl")
    return months

@app.callback(
    Output('CropUptakeGraph','figure'),
    Output('CropWaterGraph','figure'),
    Input('RefreshButton','n_clicks'), prevent_initial_call=True)
def RefreshGraphs(n_clicks):
    Config = pd.read_pickle(pos+"Config.pkl")
    Tt = cnbf.CalculateMedianTt(Config["EstablishDate"],Config["HarvestDate"],metFiles[Config["Location"]])
    CropN, CropWater, NComponentColors = cnbf.CalculateCropOutputs(Tt,Config,CropCoefficients)
    return CropNGraph(CropN, NComponentColors), CropWaterGraph(CropWater)

# Run app and display result inline in the notebook
app.run_server(mode='inline')
