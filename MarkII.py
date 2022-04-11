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


# +
def UpdateCropOptions(pos, inputDF, outputDF, CropCoefficients, EndUseCatagoriesDropdown):
    c = pd.read_pickle(pos+"Config.pkl")
    PopulateDefaults = False
    DropDownMembers = pd.Series(index = ['Group','Crop','Type'])
    DropDownOptions = pd.Series(index = ['End use','Group','Crop','Type'])
    Values = pd.Series(index = ['End use','Group','Crop','Type'],data=[None]*4)
    Values['End use'] = inputDF['End use DD']
    if (Values['End use']!=None):
        Values['Group'] = inputDF['Group DD']
        if (Values['Group']!= None):
            Values['Crop'] = inputDF['Crop DD']
            if (Values['Crop'] != None):
                Values['Type'] = inputDF['Type DD']
    outputDF['End use'] = dcc.Dropdown(value = Values['End use'], options = EndUseCatagoriesDropdown,placeholder=' Select crop End use',id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"End use DD"})
    outputDF['Group'] = dcc.Dropdown(options = [], disabled = True,style={"--bs-body-color": "#e83e8c"}, placeholder='Choose "End use" first', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group DD"})
    outputDF['Crop'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "End use" first', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop DD"})
    outputDF['Type'] = dcc.Dropdown(options = [], disabled = True, placeholder='No Type Choices', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type DD"})
    outputDF['SaleableYield'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SYInput"})
    outputDF['Units'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units DD"})
    outputDF['Product Type'] = html.Div("Yield Data", id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"PTtext"} ,style=dict(display='flex', justifyContent='right'))
    outputDF['FieldLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "FLInput"})
    outputDF['DressingLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "DLInput"})
    outputDF['MoistureContent'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "MCInput"},style={"width": "100%"})
    outputDF['EstablishStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage DD"})
    outputDF['HarvestStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage DD"})

    ctx = dash.callback_context
    caller = ast.literal_eval(ctx.triggered[0]['prop_id'].replace(".value",""))['id']
    print(caller)
    print(Values['End use'])
    print(Values['Group'])
    print(Values['Crop'])
    print(Values['Type'])
    if (caller == 'End use DD') and (Values['End use'] != None):
        Values, DropDownOptions = checkGroupOptions(Values, DropDownOptions, CropCoefficients,pos) 
    if (caller == 'Group DD') & (Values['Group'] != None):
        Values, DropDownOptions = checkCropOptions(Values,DropDownOptions,CropCoefficients,pos)
    if (caller == 'Crop DD') & (Values['Crop'] != None):
        Values, DropDownOptions = checkTypeOptions(Values,DropDownOptions,CropCoefficients,pos)

    if Values['End use'] != None:
        outputDF['Group'] = dcc.Dropdown(options = DropDownOptions['Group'], value = Values['Group'],id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group DD"})
    if Values['Group'] != None:
        outputDF['Crop'] = dcc.Dropdown(options = DropDownOptions['Crop'], value = Values['Crop'], id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop DD"})        
    if Values['Crop'] != None:
        outputDF['Type'] = dcc.Dropdown(options = DropDownOptions['Type'], value = Values['Type'], id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type DD"})
    
    print('End use')
    print(outputDF['End use'])
    print('Group')
    print(outputDF['Group'])
    print('Crop')
    print(outputDF['Crop'])
    print('Type')
    print(outputDF['Type'])
    print(Values['End use'])
    print(Values['Group'])
    print(Values['Crop'])
    print(Values['Type'])

    PopulateDefaults = (Values["End use"]!=None) & (Values["Group"]!=None) & (Values["Crop"]!=None) & (Values["Type"]!=None)
    if (PopulateDefaults == True):
        CropFilter = (CropCoefficients.loc[:,'End use'] == Values["End use"])&(CropCoefficients.loc[:,'Group'] == Values["Group"])\
                     &(CropCoefficients.loc[:,'Colloquial Name'] == Values["Crop"])&(CropCoefficients.loc[:,'Type'] == Values["Type"])
        Params = pd.Series(index=CropCoefficients.loc[CropFilter,CropParams].columns, data = CropCoefficients.loc[CropFilter,CropParams].values[0])
        outputDF['SaleableYield'] = dcc.Input(type="number",disabled = False, value = Params["Typical Yield"],min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SYInput"})
        outputDF['Units'] = dcc.Dropdown(options = UnitsDropDown, disabled = False, value =Units.loc[Params["Typical Yield Units"],"toKG/ha"], id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units DD"})
        outputDF['Product Type'] = html.Div(Params['Yield type'] + " yield", id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"PTtext"},style=dict(display='flex', justifyContent='right'))
        outputDF['FieldLoss'] = dcc.Input(type="number",disabled = False, value = Params["Typical Field Loss %"],min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "FLInput"})
        outputDF['DressingLoss'] = dcc.Input(type="number",disabled = False, value = Params["Typical Dressing Loss %"],min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "DLInput"})
        outputDF['MoistureContent'] = dcc.Input(type="number",disabled = False, value = (round(Params["Moisture %"],0)),min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "MCInput"},style={"width": "100%"})
        outputDF['EstablishStage'] = dcc.Dropdown(options = EstablishStageDropdown, disabled = False, value =Params["Typical Establish Stage"], id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage DD"})
        outputDF['HarvestStage'] = dcc.Dropdown(options = HarvestStageDropdown, disabled = False, value =Params["Typical Harvest Stage"], id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage DD"})
        cnbf.updateConfig(["SaleableYield","UnitConverter","FieldLoss","DressingLoss","MoistureContent","EstablishStage","HarvestStage"],
                     [Params["Typical Yield"],Units.loc[Params["Typical Yield Units"],"toKG/ha"],Params["Typical Field Loss %"],
                      Params["Typical Dressing Loss %"],Params["Moisture %"],Params["Typical Establish Stage"],Params["Typical Harvest Stage"]],pos+"Config.pkl")
        cnbf.updateConfig(["End use","Group","Crop","Type"],Values.values,pos+"Config.pkl")
    else:
        cnbf.updateConfig(["SaleableYield","UnitConverter","FieldLoss","DressingLoss","MoistureContent",
                      "EstablishDate","EstablishStage","HarvestDate","HarvestStage"],
                     [0,1,0,0,0,np.datetime64("NaT"),"Seed",np.datetime64("NaT"),"EarlyReproductive"],
                     pos+"Config.pkl")
    return list(outputDF[0:4]), list(outputDF[4:12])

Positions = ['Previous_','Current_','Following_']




def checkGroupOptions(Values,DropDownOptions,CropCoefficients,pos):
    GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'End use'] == Values['End use'],"Group"].drop_duplicates().dropna().values
    GroupSelections.sort()
    if len(GroupSelections)==1:
        DropDownOptions['Group'] = [{'label':"No Groups for " +Values['End use']+" end use",'value': GroupSelections[0]}]
        Values['Group'] = GroupSelections[0]
        Values, DropDownOptions = checkCropOptions(Values,DropDownOptions,CropCoefficients,pos)
    else:
        DropDownOptions['Group'] = [{'label':i,'value':i} for i in GroupSelections]
        DropDownOptions['Crop'] = []
        DropDownOptions['Type'] = []
        Values['Group'] = None
        Values['Crop'] = None
        Values['Type'] = None
    return Values, DropDownOptions

def checkCropOptions(Values,DropDownOptions,CropCoefficients,pos):
    GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'End use'] == Values['End use'],"Group"].drop_duplicates().dropna().values
    GroupSelections.sort()
    DropDownOptions['Group'] = [{'label':i,'value':i} for i in GroupSelections] 
    CropSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'End use'] == Values['End use'])&(CropCoefficients.loc[:,'Group'] == Values['Group']),"Colloquial Name"].drop_duplicates().dropna().values
    CropSelections.sort()
    if len(CropSelections) <= 1:
            DropDownOptions['Crop'] = [{'label':CropSelections[0]+" is the only " + Values['End use']+" crop",'value': CropSelections[0]}]
            Values['Crop'] = CropSelections[0]
            Values, DropDownOptions = checkTypeOptions(Values, DropDownOptions,CropCoefficients,pos)
    else:
        DropDownOptions['Crop'] = [{'label':i,'value':i} for i in CropSelections]
        DropDownOptions['Type'] = []
        Values['Crop'] = None
        Values['Type'] = None
    return Values, DropDownOptions

def checkTypeOptions(Values, DropDownOptions,CropCoefficients,pos):
    GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'End use'] == Values['End use'],"Group"].drop_duplicates().dropna().values
    GroupSelections.sort()
    DropDownOptions['Group'] = [{'label':i,'value':i} for i in GroupSelections] 
    CropSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'End use'] == Values['End use'])&(CropCoefficients.loc[:,'Group'] == Values['Group']),"Colloquial Name"].drop_duplicates().dropna().values
    CropSelections.sort()
    DropDownOptions['Crop'] = [{'label':i,'value':i} for i in CropSelections]
    TypeSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'End use'] == Values['End use'])&(CropCoefficients.loc[:,'Group'] == Values['Group'])&(CropCoefficients.loc[:,'Colloquial Name'] == Values['Crop']),"Type"].drop_duplicates().dropna().values
    if len(TypeSelections) <= 1:
            DropDownOptions['Type'] = [{'label':Values['Crop']+" has no Type options",'value': "General"}]
            Values['Type'] = TypeSelections[0]
    else:
        DropDownOptions['Type'] = [{'label':i,'value':i} for i in TypeSelections]
        Values['Type'] = None
    return Values, DropDownOptions

CropParams = ['End use', 'Group','Colloquial Name', 'Type', 'Family', 'Genus', 'Specific epithet', 'Sub species',
           'Typical Establish Stage', 'Typical Establish month', 'Typical Harvest Stage',
           'Typical Harvest month', 'Typical Yield', 'Typical Yield Units',
           'Yield type', 'Typical HI', 'HI Range',
           'Moisture %', 'Typical Dressing Loss %', 'Typical Field Loss %', 'P Root', 'Max RD', 'A cover', 'rCover', 'k_ME',
           'Nfixation', 'Root [N]', 'Stover [N]', 'Product [N]','Product [P]', 'Product [K]', 'Product [S]',
           'Product [Ca]', 'Product [Mg]', 'Product [Na]', 'Product [Cl]',
           'Stover [P]', 'Stover [K]', 'Stover [S]', 'Stover [Ca]', 'Stover [Mg]','Stover [Na]', 'Stover [Cl]']
Units = pd.DataFrame(index = ['t/ha','kg/ha'],data=[1000,1],columns=['toKG/ha'])
UnitsDropDown = [{'label':i,'value':Units.loc[i,'toKG/ha']} for i in Units.index]
Methods = ['Seed','Seedling','Vegetative','EarlyReproductive','MidReproductive','LateReproductive','Maturity','Late']
EstablishStageDropdown = [{'label':i,'value':i} for i in Methods[:2]]
HarvestStageDropdown = [{'label':i,'value':i} for i in Methods[2:]]
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

def makeCropDataDF(names,values):
    Names = []
    for n1 in range(len(names)):
        for n2 in range(len(names[n1])):
            Names.append(names[n1][n2]['id']['id'])
    df = pd.Series(index=Names,data=values)
    return df

def makeFieldDataDF(names,values):
    Names = []
    for o1 in range(len(names)):
        for o2 in range(len(names[o1])):
            Names.append(names[o1][o2]['id']['id'])
    df = pd.DataFrame(index=Names,data=values,columns=['values']).rename_axis('id')
    return df

#Planting and Harvest date callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"Event","RetType":"children","id":ALL},'children'), 
              Input({"pos":MATCH,"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), prevent_initial_call=True)
def StateCrop(dates):
    datedf = makeDF(dash.callback_context.inputs)
    for d in datedf.index:
        if datedf.loc[d,'date'] !=None:
            pos, act = ast.literal_eval(d)['id'].split("_")
            cnbf.updateConfig([act[:-3]],[np.datetime64(datedf.loc[d,'date'])],pos+"_Config.pkl")
    return cnbf.UpdateDatePickerOptions()

# Crop type information callback
@app.callback(Output({"pos":"Previous_","Group":"Crop","subGroup":"Catagory","RetType":"children","id":ALL},"children"),
              Output({"pos":"Previous_","Group":"Crop","subGroup":"data","RetType":"children","id":ALL},"children"),
              Input({"pos":"Previous_","Group":"Crop","subGroup":"Catagory","RetType":"value","id":ALL},"value"),
              prevent_initial_call=True)
def ChangeCrop(values):
    if not any(values):
        raise PreventUpdate
    inputDF = makeCropDataDF(dash.callback_context.inputs_list,values)
    outputDF = makeCropDataDF(dash.callback_context.outputs_list,[""]*12)
    return UpdateCropOptions("Previous_",inputDF,outputDF,CropCoefficients,EndUseCatagoriesDropdown)

# Defoliation callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"defoliation","RetType":"children","id":ALL},"children"),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), 
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
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"value","id":MATCH},'value'),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"value","id":MATCH},'value'), prevent_initial_call=True)
def setInputValue(value):
    pos,outp = dash.callback_context.inputs_list[0][0]['id']['id'].split("_")
    cnbf.updateConfig([cnbf.UIConfigMap.loc[outp,"ConfigID"]],[value],pos+"_Config.pkl")
    return value

# Activate Load and Save buttons
@app.callback(Output({"Group":"Field","subGroup":"FileButton","RetType":"children","id":ALL},"children"),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldName"},'value'), 
              prevent_initial_call=True)
def FieldSet(FieldName):
    print(FieldName)
    loadbutton = html.Button("Load Config",id="LoadButton")
    savebutton = html.Button("Save Config",id="SaveButton")
    return loadbutton, savebutton

# Config load callback
@app.callback(Output({"Group":"UI","id":ALL},"children"),
              Output("LLtext","children"),
              Input("LoadButton","n_clicks"),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldName"},'value'), 
              prevent_initial_call=True)
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
    return (config["PreviousUI"], config["CurrentUI"], config["FollowingUI"], config["FieldUI"]), FieldName+" loaded at "+ str(time)

# Config Save callback
@app.callback(Output("LStext",'children'), Input("SaveButton","n_clicks"), 
              Input({"Group":"UI","id":ALL},"children"),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldName"},"value"),
              prevent_initial_call=True)
def SaveConfig(n_clicks,UIs,FieldName):
    if n_clicks is None:
        raise PreventUpdate
    else:
        ConfigDF = pd.Series(index=["FieldUI","PreviousUI","CurrentUI","FollowingUI","FieldVal","PreviousVal","CurrentVal","FollowingVal"])
        ConfigDF["PreviousUI"] = UIs[0]
        ConfigDF["CurrentUI"] = UIs[1]
        ConfigDF["FollowingUI"] = UIs[2]
        ConfigDF["PreviousUI"] = UIs[0]
        ConfigDF["FieldUI"] = UIs[3]
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
    #print(dash.callback_context.inputs_list)
    inputDF = makeFieldDataDF(dash.callback_context.inputs_list,values)
    for v in inputDF.index:
        if inputDF.loc[v,'values'] != None:
            cnbf.updateConfig([v],[inputDF.loc[v,'values']],"Field_Config.pkl")
    return list(inputDF.loc[:,"values"].values)

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
                    dbc.Col([dbc.Row(dbc.Card(cnbf.CropInputs('Previous_',EndUseCatagoriesDropdown,False,'Select Planting Date','Set Planting Date first')),
                                     id={"Group":"UI","id":"PreviousConfigUI"}),
                             dbc.Row(dbc.Card(cnbf.CropInputs('Current_',EndUseCatagoriesDropdown,True, 'Set Prior Crop dates first','Set Prior Crop dates first')),
                                     id={"Group":"UI","id":"CurrentConfigUI"}),
                             dbc.Row(dbc.Card(cnbf.CropInputs('Following_',EndUseCatagoriesDropdown,True, 'Set Prior Crop dates first','Set Prior Crop dates first')),
                                     id={"Group":"UI","id":"FollowingConfigUI"})
                            ]),
                    dbc.Col([dbc.Row(html.H1("Field Name", id="FNtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(dcc.Input(type="text", placeholder='Type field Name',min=0,id={"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldName"})),
                             dbc.Row(html.Button("Load Config", id="LoadButton", disabled=True),id={"Group":"Field","subGroup":"FileButton","RetType":"children","id":"LoadButtonRow"}),
                             dbc.Row(html.Div("Last Load", id="LLtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(html.Button("Save Config",id="SaveButton",disabled=True),id={"Group":"Field","subGroup":"FileButton","RetType":"children","id":"SaveButtonRow"}),
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
                            ],width = 2,id={"Group":"UI","id":"FieldUI"}),
                    dbc.Col([dbc.Row(dbc.Card(dcc.Graph(id='CropUptakeGraph'))),
                             dbc.Row(dbc.Card(dcc.Graph(id='MineralNGraph'))),
                             dbc.Row(dbc.Card(dcc.Graph(id='NInputsGraph')))
                            ])
                        ])
                     ])
# Run app and display result inline in the notebook
app.run_server(mode='external')
