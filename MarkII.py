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
Positions = ['Previous_','Current_','Following_']
def UpdateCropOptions(pos, inputDF, outputDF, CropCoefficients, EndUseCatagoriesDropdown):
    c = pd.read_pickle(pos+"Config.pkl")
    PopulateDefaults = False
    DropDownMembers = pd.Series(index = ['Group','Crop','Type'],dtype=object)
    DropDownOptions = pd.Series(index = ['End use','Group','Crop','Type'],dtype=object)
    
    #Set up values series
    Values = pd.Series(index = ['End use','Group','Crop','Type'],data=[None]*4)
    Values['End use'] = inputDF['End use DD']
    if (Values['End use']!=None):
        Values['Group'] = inputDF['Group DD']
        if (Values['Group']!= None):
            Values['Crop'] = inputDF['Crop DD']
            if (Values['Crop'] != None):
                Values['Type'] = inputDF['Type DD']

    # Default drop down configs
    outputDF['End use'] = dcc.Dropdown(value = Values['End use'], options = EndUseCatagoriesDropdown,placeholder=' Select crop End use',id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"End use DD"})
    outputDF['Group'] = dcc.Dropdown(options = [], disabled = True,style={"--bs-body-color": "#e83e8c"}, placeholder='Choose "End use" first', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group DD"})
    outputDF['Crop'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "End use" first', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop DD"})
    outputDF['Type'] = dcc.Dropdown(options = [], disabled = True, placeholder='No Type Choices', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type DD"})
    
    # Set drop down configs based on selected values
    if Values['End use'] != None:
        Values, DropDownOptions = checkGroupOptions(Values, DropDownOptions, CropCoefficients,pos) 
        outputDF['Group'] = dcc.Dropdown(options = DropDownOptions['Group'], value = Values['Group'],id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group DD"})
        print('g set')
        print(Values['Group'] != None)
        if Values['Group'] != None:
            Values, DropDownOptions = checkCropOptions(Values,DropDownOptions,CropCoefficients,pos)
            outputDF['Crop'] = dcc.Dropdown(options = DropDownOptions['Crop'], value = Values['Crop'], id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop DD"})        
            print('c set')
            if Values['Crop'] != None:
                Values, DropDownOptions = checkTypeOptions(Values,DropDownOptions,CropCoefficients,pos)
                outputDF['Type'] = dcc.Dropdown(options = DropDownOptions['Type'], value = Values['Type'], id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type DD"})
                print('t set')

    #Enable Crop data fields and populate with default values if all crop selection catagories are made
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
        outputDF['SaleableYield'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SYInput"})
        outputDF['Units'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units DD"})
        outputDF['Product Type'] = html.Div("Yield Data", id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"PTtext"} ,style=dict(display='flex', justifyContent='right'))
        outputDF['FieldLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "FLInput"})
        outputDF['DressingLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "DLInput"})
        outputDF['MoistureContent'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "MCInput"},style={"width": "100%"})
        outputDF['EstablishStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage DD"})
        outputDF['HarvestStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage DD"})
        cnbf.updateConfig(["SaleableYield","UnitConverter","FieldLoss","DressingLoss","MoistureContent",
                      "EstablishStage","HarvestStage"],
                     [0,1,0,0,0,"Seed","EarlyReproductive"],
                     pos+"Config.pkl")
    return list(outputDF[0:4]), list(outputDF[4:12])

def checkGroupOptions(Values,DropDownOptions,CropCoefficients,pos):
    GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'End use'] == Values['End use'],"Group"].drop_duplicates().dropna().values
    GroupSelections.sort()
    if len(GroupSelections)<=1:
        DropDownOptions['Group'] = [{'label':"No Groups for " +Values['End use']+" end use",'value': GroupSelections[0]}]
        Values['Group'] = GroupSelections[0]
        Values, DropDownOptions = checkCropOptions(Values,DropDownOptions,CropCoefficients,pos)
    else:
        DropDownOptions['Group'] = [{'label':i,'value':i} for i in GroupSelections]
        DropDownOptions['Crop'] = []
        DropDownOptions['Type'] = []
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
    return Values, DropDownOptions

def checkTypeOptions(Values,DropDownOptions,CropCoefficients,pos):
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

# +
Actions = ["EstablishDate", "HarvestDate"]
def SetDatePicker(pos,act,PHtext,minDate,selDate,isEnabled):
    if isEnabled:
        DateP = dcc.DatePickerSingle(id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"date","id":act}, date = selDate, placeholder = PHtext,
                                          min_date_allowed=minDate, max_date_allowed=dt.date(2025, 12, 31), 
                                          initial_visible_month = selDate, display_format='D-MMM-YYYY')     
    else:
        DateP = dcc.DatePickerSingle(id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"date","id":act}, placeholder = PHtext, disabled = True)
    return DateP

def UpdateDatePickerOptions(datedf):
    for d in datedf.index:
        pos = d[0]
        act = d[1]
        cnbf.updateConfig([act],[np.datetime64(datedf.loc[d,'date'])],pos+"Config.pkl")
    
    posc=0
    for pos in Positions:
        for act in Actions:
            if (pos == "Previous_") and (act == "EstablishDate"):
                minDate = dt.date(2020,1,1)
                isEnabled = datedf.loc[(pos,act),'date']!=None
                selDate = datedf.loc[(pos,act),'date']#.astype(dt.datetime)
                PHtext = 'Select Establish Date'
            else:
                isEnabled = datedf.iloc[posc-1,0]!=None
                if isEnabled:
                    minDate = datedf.iloc[posc-1,0]#.astype(dt.datetime)
                else:
                    minDate = dt.date(2020,1,1)
                if datedf.iloc[posc,0]==None:
                    selDate = None
                else:    
                    selDate = datedf.iloc[posc,0]#.astype(dt.datetime)
                if act == 'HarvestDate':
                    if isEnabled:
                        PHtext = 'Select Harvest Date'
                    else:
                        PHtext = 'Set Prior Crop dates first'
                if act == 'EstablishDate':
                    if isEnabled:
                        PHtext = 'Select Planting Date'
                    else:
                        PHtext = 'Set Prior Crop dates first'
            globals()[pos+act] = SetDatePicker(pos,act,PHtext,minDate,selDate,isEnabled)
            posc +=1
    
    return Previous_EstablishDate, Previous_HarvestDate, Current_EstablishDate, Current_HarvestDate, Following_EstablishDate, Following_HarvestDate



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

def makeDateDataDF(names,dates):
    p=0
    df = pd.DataFrame(index = range(0,6), columns=['pos','act','date'])
    for n1 in range(len(names)):
        for n2 in range(len(names[n1])):
            df.loc[p,'pos'] = names[n1][n2]['id']['pos']
            df.loc[p,'act'] = names[n1][n2]['id']['id']
            df.loc[p,'date'] = dates[p]
            p+=1
    df.set_index(['pos','act'],inplace=True)
    return df

#Planting and Harvest date callback
@app.callback(Output({"pos":ALL,"Group":"Crop","subGroup":"Event","RetType":"children","id":ALL},'children'), 
              Input({"pos":ALL,"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), prevent_initial_call=True)
def StateCrop(dates):
    datedf = makeDateDataDF(dash.callback_context.inputs_list,dates)
    return UpdateDatePickerOptions(datedf)

# Crop type information callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":ALL},"children"),
              Output({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"children","id":ALL},"children"),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":ALL},"value"),
              prevent_initial_call=True)
def ChangeCrop(values):
    if not any(values):
        raise PreventUpdate
    inputDF = makeCropDataDF(dash.callback_context.inputs_list,values)
    outputDF = makeCropDataDF(dash.callback_context.outputs_list,[""]*12)
    pos = dash.callback_context.outputs_list[0][0]['id']['pos']
    return UpdateCropOptions(pos,inputDF,outputDF,CropCoefficients,EndUseCatagoriesDropdown)

# # Defoliation callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"defoliation","RetType":"children","id":"Defoliation Dates"},"children"),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), 
              prevent_initial_call=True)
def DefoliationOptions(dates):
    datedf = makeDF(dash.callback_context.inputs)
    pos = dash.callback_context.outputs_list['id']['pos']
    if (datedf.iloc[0,0] != None) and (datedf.iloc[1,0] != None):
        cropMonths = pd.date_range(dt.datetime.strptime(str(datedf.iloc[0,0]),'%Y-%m-%d'),
                                   dt.datetime.strptime(str(datedf.iloc[1,0]),'%Y-%m-%d'),freq='MS')
        DefCheckMonths = [{'label':MonthIndexs.loc[i.month,'Name'],'value':i} for i in cropMonths]    
    else:
        DefCheckMonths = []
    print(DefCheckMonths)
    return dcc.Checklist(id={"pos":pos,"Group":"Crop","subGroup":"defoliation","RetType":"children","id":"Def Dates"}, options = DefCheckMonths, value=[])

# Crop yield information callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"value","id":MATCH},'value'),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"value","id":MATCH},'value'), prevent_initial_call=True)
def setInputValue(value):
    pos = dash.callback_context.inputs_list[0]['id']['pos']
    outp = dash.callback_context.inputs_list[0]['id']['id']
    cnbf.updateConfig([cnbf.UIConfigMap.loc[outp,"ConfigID"]],[value],pos+"Config.pkl")
    return value

# Activate Load and Save buttons
@app.callback(Output({"Group":"Field","subGroup":"FileButton","RetType":"children","id":ALL},"children"),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldName"},'value'), 
              prevent_initial_call=True)
def FieldSet(FieldName):
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
# -
{"Group":"Crop","RetType":"date","id":"EstablishDate","pos":"Following_","subGroup":"Event"}["pos"]

pd.read_pickle('Previous_Config.pkl')
