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
#from dash.dependencies import Input, Output
import cufflinks as cf
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import copy
import CropNBalFunctions as cnbf
#from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from dash.exceptions import PreventUpdate

from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL

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
# Empty the config files
FieldConfigs = ['FieldName','Location','HWEON','MinN']
FieldConfig = pd.Series(index = FieldConfigs, data = [""]+[None]*3)
FieldConfig.to_pickle("Field_Config.pkl")

PreviousConfig = pd.Series(index = cnbf.CropConfigs,data = [None]*13+[[]])
PreviousConfig.to_pickle("Previous_Config.pkl")

CurrentConfig = pd.Series(index = cnbf.CropConfigs,data = [None]*13+[[]])
CurrentConfig.to_pickle("Current_Config.pkl")

FollowingConfig = pd.Series(index = cnbf.CropConfigs,data = [None]*13+[[]])
FollowingConfig.to_pickle("Following_Config.pkl")

import ast

app = JupyterDash(external_stylesheets=[dbc.themes.SLATE])

def findindex(values):
    ind = None
    for p in range(len(values)):
        if values[p] != None:
            ind = p
    return ind

def posOfCaller(triggered):
    pos = triggered[0]['prop_id'].replace('.value','').split(",")[2].split(":")[1].split("_")[0].replace('"','')+"_"
    if pos== "Previous_":
        baseIndex = 0
    if pos== "Current_":
        baseIndex = 1
    if pos== "Following_":
        baseIndex = 2
    return pos, baseIndex

def makeDF(inputs):
    df = pd.DataFrame.from_dict(inputs,orient='index',columns=['date'])
    df.index = [x.replace(".date","") for x in df.index]
    return df

def makeCropDataDF(outputs):
    Outputs = []
    for o1 in range(len(outputs)):
        for o2 in range(len(outputs[o1])):
            Outputs.append(outputs[o1][o2]['id']['id'])
        df = pd.DataFrame(index=Outputs,data=Outputs,columns=['id']).rename_axis('id')
        for o in Outputs:
            pos,var = o.split("_")
            df.loc[o,"pos"]=pos
            df.loc[o,"var"]=var
        df.set_index(["pos","var"],inplace=True,append=False,drop=False)
    return df


#Planting and Harvest date callback
@app.callback(Output({"Group":"Crop","subGroup":"Event","RetType":"children","id":ALL},'children'), 
              Input({"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), prevent_initial_call=True)
def StateCrop(dates):
    datedf = makeDF(dash.callback_context.inputs)
    for d in datedf.index:
        if datedf.loc[d,'date'] !=None:
            pos, act = ast.literal_eval(d)['id'].split("_")
            cnbf.updateConfig([act[:-3]],[np.datetime64(datedf.loc[d,'date'])],pos+"_Config.pkl")
    return cnbf.UpdateDatePickerOptions()

# Crop type information callback
@app.callback(Output({"Group":"Crop","subGroup":"Catagory","RetType":"children","id":ALL},"children"),
              Output({"Group":"Crop","subGroup":"data","RetType":"children","id":ALL},"children"),
              Input({"Group":"Crop","subGroup":"Catagory","RetType":"value","id":ALL},"value"),
              prevent_initial_call=True)
def ChangeCrop(values):
    outputDF = makeCropDataDF(dash.callback_context.outputs_list)
    outputDF.loc[:,'return'] = ""
    inputDF = makeCropDataDF(dash.callback_context.inputs_list)
    inputDF.loc[:,'values'] = values
    return cnbf.UpdateCropOptions(inputDF,outputDF,CropCoefficients,EndUseCatagoriesDropdown)

# Defoliation callback
@app.callback(Output({"Group":"Crop","subGroup":"defoliation","RetType":"children","id":ALL},"children"),
              Input({"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), 
              prevent_initial_call=True)
def DefoliationOptions(dates):
    datedf = makeDF(dash.callback_context.inputs)
    defDatesAll = []
    for d in datedf.index:
            pos,act = ast.literal_eval(d)['id'].split("_")
            print(pos),print(act)
            if act == "HarvestDate DP":
                
                defDates = dcc.Checklist(id=pos+"_Def Dates",options=[])
                config = pd.read_pickle(pos+"_Config.pkl")
                if (config["EstablishDate"] != None) and (config["HarvestDate"]!= None):
                    cropMonths = pd.date_range(dt.datetime.strptime(str(config["EstablishDate"]).split('T')[0],'%Y-%m-%d'),
                                               dt.datetime.strptime(str(config["HarvestDate"]).split('T')[0],'%Y-%m-%d'),freq='MS')
                    DefCheckMonths = [{'label':MonthIndexs.loc[i.month,'Name'],'value':i} for i in cropMonths]    
                    defDates = dcc.Checklist(id=pos+"_Def Dates", options = DefCheckMonths, value=[])
                defDatesAll.append(defDates)
    return defDatesAll[0], defDatesAll[1], defDatesAll[2]

# Crop yield information callback
@app.callback(Output({"Group":"Crop","subGroup":"data","RetType":"value","id":ALL},'value'),
              Input({"Group":"Crop","subGroup":"data","RetType":"value","id":ALL},'value'), prevent_initial_call=True)
def setInputValue(value):
    #list(dash.callback_context.inputs.keys())[0]
    pos,outp = dash.callback_context.inputs_list[0][0]['id']['id'].split("_")
    print(pos), print(outp)
    cnbf.updateConfig([cnbf.UIConfigMap.loc[outp,"ConfigID"]],[value],pos+"_Config.pkl")
    return value

# Activate Load and Save buttons
@app.callback(Output("LoadButtonRow","children"),Output("SaveButtonRow","children"),
              Input({"id":"FieldName"},'value'), prevent_initial_call=True)
def FieldSet(FieldName):
    print(FieldName)
    loadbutton = html.Button("Load Config",id="LoadButton")
    savebutton = html.Button("Save Config",id="SaveButton")
    return loadbutton, savebutton

# Config load callback
@app.callback(Output("PreviousConfigUI","children"),Output("CurrentConfigUI","children"),
              Output("FollowingConfigUI","children"),Output("FieldUI","children"),
              Output("LLtext","children"),
              Input("LoadButton","n_clicks"),Input({"id":"FieldName"},'value'), prevent_initial_call=True)
def loadConfig(n_clicks, FieldName):
    if n_clicks is None:
        raise PreventUpdate
    else:
        config = pd.read_pickle(FieldName+"_SavedConfig.pkl")
        time = dt.datetime.now()
        config["PreviousVal"].to_pickle("Previous_Config.pkl")
        config["CurrentVal"].to_pickle("Current_Config.pkl")
        config["FollowingVal"].to_pickle("Following_Config.pkl")
        config["FieldVal"].to_pickle("Field_Config.pkl")
    return config["PreviousUI"], config["CurrentUI"], config["FollowingUI"], config["FieldUI"],FieldName+" loaded at "+ str(time)

# Config Save callback
@app.callback(Output("LStext",'children'), Input("SaveButton","n_clicks"), 
              Input("PreviousConfigUI","children"), Input("CurrentConfigUI","children"),
              Input("FollowingConfigUI","children"), Input("FieldUI",'children'),
              Input({"id":"FieldName"},"value"),prevent_initial_call=True)
def SaveConfig(n_clicks,PreviousUI,CurrentUI,FollowingUI,FieldUI,FieldName):
    if n_clicks is None:
        raise PreventUpdate
    else:
        ConfigDF = pd.Series(index=["FieldUI","PreviousUI","CurrentUI","FollowingUI","FieldVal","PreviousVal","CurrentVal","FollowingVal"])
        ConfigDF["PreviousUI"] = PreviousUI
        ConfigDF["CurrentUI"] = CurrentUI
        ConfigDF["FollowingUI"] = FollowingUI
        ConfigDF["PreviousUI"] = PreviousUI
        ConfigDF["FieldUI"] = FieldUI
        ConfigDF["PreviousVal"] = pd.read_pickle("Previous_Config.pkl")
        ConfigDF["CurrentVal"] = pd.read_pickle("Current_Config.pkl")
        ConfigDF["FollowingVal"] = pd.read_pickle("Following_Config.pkl")
        ConfigDF["FieldVal"] = pd.read_pickle("Field_Config.pkl")
        ConfigDF.to_pickle(FieldName+"_SavedConfig.pkl")
        time = dt.datetime.now()
        return "Last Save " + str(time)

# Field data callbacks
@app.callback(Output({"Group":"Field","subGroup":ALL,"RetType":"value","id":ALL},'value'),
              Input({"Group":"Field","subGroup":ALL,"RetType":"value","id":ALL},'value'),
              prevent_initial_call=True)
def setInputValue(values):
    prop_ID = list(dash.callback_context.inputs.keys())[0]
    conf = prop_ID.split(".")[0]
    cnbf.updateConfig([conf],[value],"Field_Config.pkl")
    return value

# Validate config callback to activate "Update NBalance" button for running the model
@app.callback(Output("RefreshButtonRow",'children'),
              Input({"Group":ALL,"subGroup":ALL,"RetType":"value","id":ALL},'value'), 
              Input({"Group":ALL,"subGroup":ALL,"RetType":"date","id":ALL},'date'),
              prevent_initial_call=True)
def checkConfigAndEnableUpdate(values,dates):
    return cnbf.validateConfigs()

@app.callback(
    Output('CropUptakeGraph','figure'),
    #Output('MineralNGraph','figure'),
    #Output('NInputsGraph','figure'),
    Input('RefreshButton','n_clicks'), prevent_initial_call=True)
def RefreshGraphs(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        PreviousConfig = pd.read_pickle("Previous_Config.pkl")
        CurrentConfig = pd.read_pickle("Current_Config.pkl")
        FollowingConfig = pd.read_pickle("Following_Config.pkl")
        Tt = cnbf.CalculateMedianTt(PreviousConfig["EstablishDate"].astype(dt.datetime),FollowingConfig["HarvestDate"].astype(dt.datetime),metFiles[PreviousConfig["Location"]])
        PreviousCropN, PreviousCropWater, PreviousNComponentColors = cnbf.CalculateCropOutputs(Tt[PreviousConfig["EstablishDate"]:PreviousConfig["HarvestDate"]],
                                                                                               PreviousConfig,CropCoefficients)
        CurrentCropN, CurrentCropWater, CurrentNComponentColors = cnbf.CalculateCropOutputs(Tt[CurrentConfig["EstablishDate"]:CurrentConfig["HarvestDate"]],
                                                                                               CurrentConfig,CropCoefficients)
        FollowingCropN, FollowingCropWater, FollowingNComponentColors = cnbf.CalculateCropOutputs(Tt[FollowingConfig["EstablishDate"]:FollowingConfig["HarvestDate"]],
                                                                                               FollowingConfig,CropCoefficients)
        BiomassComponents = ['Root','+ Stover','+ FieldLoss','+ DressingLoss','TotalCrop']
        CropN = pd.DataFrame(index = pd.MultiIndex.from_product([BiomassComponents,Tt.index],
                                                                names=['Component','Date']),columns=['Values'])
        CropN.update(PreviousCropN)
        CropN.update(CurrentCropN)
        CropN.update(FollowingCropN)
        return CropNGraph(CropN, FollowingNComponentColors)

app.layout = html.Div([
                dbc.Row([
                    dbc.Col([dbc.Row(dbc.Card(cnbf.CropInputs('Previous_',EndUseCatagoriesDropdown,False,'Select Planting Date','Set Planting Date first')),id="PreviousConfigUI"),
                             dbc.Row(dbc.Card(cnbf.CropInputs('Current_',EndUseCatagoriesDropdown,True, 'Set Prior Crop dates first','Set Prior Crop dates first')),id="CurrentConfigUI"),
                             dbc.Row(dbc.Card(cnbf.CropInputs('Following_',EndUseCatagoriesDropdown,True, 'Set Prior Crop dates first','Set Prior Crop dates first')),id="FollowingConfigUI")
                            ]),
                    dbc.Col([dbc.Row(html.H1("Field Name", id="FNtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(dcc.Input(type="text", placeholder='Type field Name',min=0,id={"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldName"})),
                             dbc.Row(html.Button("Load Config",id="LoadButton",disabled=True),id="LoadButtonRow"),
                             dbc.Row(html.Div("Last Load", id="LLtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(html.Button("Save Config",id="SaveButton",disabled=True),id="SaveButtonRow"),
                             dbc.Row(html.Div("Last Save", id="LStext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(html.H1("Field Location")),
                             dbc.Row(dcc.Dropdown(id={"Group":"Field","subGroup":"Place","RetType":"value","id":"Location"},options = MetDropDown,placeholder='Select closest location')),
                             dbc.Row(html.H1("Soil Test Values")),
                             dbc.Row(html.Div("HWEON test value", id="HWEONtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(dcc.Input(type="number", placeholder='Enter test value',min=0,id={"Group":"Field","subGroup":"Soil","RetType":"value","id":"HWEON"})),
                             dbc.Row(html.Div("MinN test value", id="MinNtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(dcc.Input(type="number", placeholder='Enter test value',min=0,id={"Group":"Field","subGroup":"Soil","RetType":"value","id":"MinN"})),
                             dbc.Row(html.Button("Update NBalance",id="RefreshButton",disabled=True),id="RefreshButtonRow"),
                             dbc.Row(html.H1(""))
                            ],width = 2,id="FieldUI"),
                    dbc.Col([dbc.Row(dbc.Card(dcc.Graph(id='CropUptakeGraph'))),
                             dbc.Row(dbc.Card(dcc.Graph(id='MineralNGraph'))),
                             dbc.Row(dbc.Card(dcc.Graph(id='NInputsGraph')))
                            ])
                        ])
                     ])
# Run app and display result inline in the notebook
app.run_server(mode='external')
