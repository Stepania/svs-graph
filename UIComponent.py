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

# ## General components

# +
# %%writefile C:\Anaconda\Lib\CropNBalUICompenents.py

import dash
from dash import dash_table
from dash import html
from dash import dcc
import plotly.graph_objects as go
import plotly.express as px
import datetime as dt
import pandas as pd
import numpy as np
from bisect import bisect_left, bisect_right
from jupyter_dash import JupyterDash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import cufflinks as cf
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import copy
import ast

Positions = ['Previous_','Current_','Following_']
Actions = ["EstablishDate", "HarvestDate"]

CropParams = ['EndUse', 'Group','Colloquial Name', 'Type', 'Family', 'Genus', 'Specific epithet', 'Sub species',
       'Typical Establish Stage', 'Typical Establish month', 'Typical Harvest Stage',
       'Typical Harvest month', 'Typical Yield', 'Typical Yield Units',
       'Yield type', 'Typical HI', 'HI Range',
       'Moisture %', 'Typical Dressing Loss %', 'Typical Field Loss %', 'P Root', 'Max RD', 'A cover', 'rCover', 'k_ME',
       'Nfixation', 'Root [N]', 'Stover [N]', 'Product [N]','Product [P]', 'Product [K]', 'Product [S]',
       'Product [Ca]', 'Product [Mg]', 'Product [Na]', 'Product [Cl]',
       'Stover [P]', 'Stover [K]', 'Stover [S]', 'Stover [Ca]', 'Stover [Mg]','Stover [Na]', 'Stover [Cl]']

CropConfigs = ["EndUse","Group","Crop","Type","SaleableYield","Units","FieldLoss","DressingLoss",
               "MoistureContent","EstablishDate","EstablishStage","HarvestDate","HarvestStage","ResidueTreatment","DefoliationDates"]

Units = pd.DataFrame(index = ['t/ha','kg/ha'],data=[1000,1],columns=['toKG/ha'])
UnitsDropDown = [{'label':i,'value':Units.loc[i,'toKG/ha']} for i in Units.index]

Methods = ['Seed','Seedling','Vegetative','EarlyReproductive','MidReproductive','LateReproductive','Maturity','Late']
EstablishStageDropdown = [{'label':i,'value':i} for i in Methods[:2]]
HarvestStageDropdown = [{'label':i,'value':i} for i in Methods[2:]]

ResTreats = pd.DataFrame(index = ["None","Baled","Burnt","Grazed","Incorporated"],
                                 data = [1.0,0.2,0.1,0.6,1.0], columns = ['propn'])
ResidueTreatDropdown = [{'label':i,'value':ResTreats.loc[i,'propn']} for i in ResTreats.index]

def splitprops(prop_ID,propExt):
    prop_ID = prop_ID.replace(propExt,'')
    return prop_ID.split('_')[0]+'_', prop_ID.split('_')[1]

def Generalcomponents():
    # Read in Crop coefficients table and filter out nasty ones
    CropCoefficients = pd.read_excel('C:\\GitHubRepos\\Overseer-testing\\CropCoefficients\\CropCoefficientTable.xlsx',skiprows=2, engine='openpyxl')

    # Make lists of EndUse options
    EndUseCatagories = CropCoefficients.loc[:,'EndUse'].drop_duplicates().dropna().values
    EndUseCatagories.sort()

    # Make some drop down lists
    EndUseCatagoriesDropdown = [{'label':i,'value':i} for i in EndUseCatagories]
    CropDropDown = [{'label':i,'value':i} for i in CropCoefficients.index]



    # Read in weather data files
    LincolnMet = pd.read_csv('C:\GitHubRepos\Weather\Broadfields\LincolnClean.met',delimiter = '\t')
    LincolnMet.name = 'Lincoln'
    GoreMet = pd.read_csv('C:\GitHubRepos\Weather\OtherLocations\GoreClean.met',delimiter = '\t')
    GoreMet.name = 'Gore'
    WhatatuMet = pd.read_csv('C:\GitHubRepos\Weather\OtherLocations\WhatatuClean.met',delimiter = '\t')
    WhatatuMet.name = 'Napier'
    PukekoheMet = pd.read_csv('C:\GitHubRepos\Weather\OtherLocations\PukekoheClean.met',delimiter = '\t')
    PukekoheMet.name = 'Pukekohe'

    #Load met files into dictionary 
    metFiles ={'Pukekohe':PukekoheMet,'Whatatu':WhatatuMet,'Lincoln':LincolnMet,'Gore':GoreMet}

    ## Function to calculate thermal time from temperature
    def tt(x,b):
        return max(0,x-b)

    # Calculate thermal time for each met file and get date in correct format
    for f in metFiles.keys():
        metFiles[f].loc[:,'Date'] = pd.to_datetime(metFiles[f].loc[:,'Date'])
        metFiles[f].loc[:,'tt'] = [tt(x,0) for x in metFiles[f].Temp]
        metFiles[f].set_index('Date',inplace=True)

    # Make a drop down list with met file options
    MetDropDown = [{'label':i,'value':i} for i in metFiles.keys()]

    MonthIndexs = pd.DataFrame(index = range(1,13),columns=['Name'],data=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
    
    return CropCoefficients, EndUseCatagoriesDropdown, metFiles, MetDropDown, MonthIndexs

def validateConfigs():
    NotSet = 0
    for pos in Positions+['field_']:
        config=pd.read_pickle(pos+"Config.pkl")
        NotSet += Config.isnull().sum()
    if NotSet > 0: 
        return html.Button("Update NBalance",id="RefreshButton")
    else: 
        return html.Button("Update NBalance",id="RefreshButton",disabled=True)

def updateConfig(keys,values,ConfigAddress):
    Config = pd.read_pickle(ConfigAddress)
    its = range(len(keys))
    for i in its:
        Config[keys[i]] = values[i]
    Config.to_pickle(ConfigAddress)

def UpdateCropOptions(pos, inputDF, outputDF, CropCoefficients, EndUseCatagoriesDropdown):
    c = pd.read_pickle(pos+"Config.pkl")
    PopulateDefaults = False
    DropDownMembers = pd.Series(index = ['Group','Crop','Type'],dtype=object)
    DropDownOptions = pd.Series(index = ['EndUse','Group','Crop','Type'],dtype=object)
    
    #Set up values series
    Values = pd.Series(index = ['EndUse','Group','Crop','Type'],data=[None]*4)
    Values['EndUse'] = inputDF['EndUse']
    if (Values['EndUse']!=None):
        Values['Group'] = inputDF['Group']
        if (Values['Group']!= None):
            Values['Crop'] = inputDF['Crop']
            if (Values['Crop'] != None):
                Values['Type'] = inputDF['Type']
    # Default drop down configs
    outputDF['EndUse'] = dcc.Dropdown(value = Values['EndUse'], options = EndUseCatagoriesDropdown,placeholder=' Select crop EndUse',id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"EndUse"})
    outputDF['Group'] = dcc.Dropdown(options = [], disabled = True,style={"--bs-body-color": "#e83e8c"}, placeholder='Choose "EndUse" first', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group"})
    outputDF['Crop'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Group" first', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop"})
    outputDF['Type'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type"})
    
    # Set drop down configs based on selected values
    if Values['EndUse'] != None:
        Values, DropDownOptions = checkGroupOptions(Values, DropDownOptions, CropCoefficients,pos) 
        outputDF['Group'] = dcc.Dropdown(options = DropDownOptions['Group'],placeholder = 'Select Group', value = Values['Group'],id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group"})
        if Values['Group'] != None:
            Values, DropDownOptions = checkCropOptions(Values,DropDownOptions,CropCoefficients,pos)
            outputDF['Crop'] = dcc.Dropdown(options = DropDownOptions['Crop'],placeholder = 'Select Crop', value = Values['Crop'], id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop"})        
            if Values['Crop'] != None:
                Values, DropDownOptions = checkTypeOptions(Values,DropDownOptions,CropCoefficients,pos)
                outputDF['Type'] = dcc.Dropdown(options = DropDownOptions['Type'],placeholder = 'Select Type', value = Values['Type'], id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type"})
        
    #Enable Crop data fields and populate with default values if all crop selection catagories are made
    PopulateDefaults = (Values["EndUse"]!=None) & (Values["Group"]!=None) & (Values["Crop"]!=None) & (Values["Type"]!=None)
    if (PopulateDefaults == True):
        CropFilter = (CropCoefficients.loc[:,'EndUse'] == Values["EndUse"])&(CropCoefficients.loc[:,'Group'] == Values["Group"])\
                     &(CropCoefficients.loc[:,'Colloquial Name'] == Values["Crop"])&(CropCoefficients.loc[:,'Type'] == Values["Type"])
        Params = pd.Series(index=CropCoefficients.loc[CropFilter,CropParams].columns, data = CropCoefficients.loc[CropFilter,CropParams].values[0])
        outputDF['SaleableYield'] = dcc.Input(type="number",disabled = False, value = Params["Typical Yield"],min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SaleableYield"})
        outputDF['Units'] = dcc.Dropdown(options = UnitsDropDown, disabled = False, value =Units.loc[Params["Typical Yield Units"],"toKG/ha"], id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units"})
        outputDF['ProductType'] = html.Div(Params['Yield type'] + " yield", id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"ProductType"},style=dict(display='flex', justifyContent='right'))
        outputDF['FieldLoss'] = dcc.Input(type="number",disabled = False, value = Params["Typical Field Loss %"],min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "FieldLoss"})
        outputDF['DressingLoss'] = dcc.Input(type="number",disabled = False, value = Params["Typical Dressing Loss %"],min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "DressingLoss"})
        outputDF['MoistureContent'] = dcc.Input(type="number",disabled = False, value = (round(Params["Moisture %"],0)),min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "MoistureContent"},style={"width": "100%"})
        outputDF['EstablishStage'] = dcc.Dropdown(options = EstablishStageDropdown, disabled = False, value =Params["Typical Establish Stage"], id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage"})
        outputDF['HarvestStage'] = dcc.Dropdown(options = HarvestStageDropdown, disabled = False, value =Params["Typical Harvest Stage"], id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage"})
        outputDF["ResidueTreatment"] = dcc.Dropdown(options = ResidueTreatDropdown, disabled = False, value = "Incorporated", id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"ResidueTreatment"})
        updateConfig(["SaleableYield","Units","FieldLoss","DressingLoss","MoistureContent","EstablishStage","HarvestStage","ResidueTreatment"],
                     [Params["Typical Yield"],Units.loc[Params["Typical Yield Units"],"toKG/ha"],Params["Typical Field Loss %"],
                      Params["Typical Dressing Loss %"],Params["Moisture %"],Params["Typical Establish Stage"],Params["Typical Harvest Stage"],1.0],
                     pos+"Config.pkl")
        updateConfig(["EndUse","Group","Crop","Type"],Values.values,pos+"Config.pkl")
    else:
        outputDF['SaleableYield'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SaleableYield"})
        outputDF['Units'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units"})
        outputDF['ProductType'] = html.Div("Yield Data", id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"ProductType"} ,style=dict(display='flex', justifyContent='right'))
        outputDF['FieldLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "FieldLoss"})
        outputDF['DressingLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "DressingLoss"})
        outputDF['MoistureContent'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "MoistureContent"},style={"width": "100%"})
        outputDF['EstablishStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage"})
        outputDF['HarvestStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage"})
        outputDF["ResidueTreatment"] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"ResidueTreatment"})
        updateConfig(["SaleableYield","Units","FieldLoss","DressingLoss","MoistureContent",
                      "EstablishStage","HarvestStage","ResidueTreatment"],
                     [0.0,1.0,0.0,0.0,0.0,"Seed","EarlyReproductive",1.0],
                     pos+"Config.pkl")
        updateConfig(["EndUse","Group","Crop","Type"],[None,None,None,None],pos+"Config.pkl")
    return list(outputDF[0:4]), list(outputDF[4:13])

def checkGroupOptions(Values,DropDownOptions,CropCoefficients,pos):
    GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'EndUse'] == Values['EndUse'],"Group"].drop_duplicates().dropna().values
    GroupSelections.sort()
    if len(GroupSelections)<=1:
        DropDownOptions['Group'] = [{'label':"No Groups for " +Values['EndUse']+" EndUse",'value': GroupSelections[0]}]
        Values['Group'] = GroupSelections[0]
        Values, DropDownOptions = checkCropOptions(Values,DropDownOptions,CropCoefficients,pos)
    else:
        DropDownOptions['Group'] = [{'label':i,'value':i} for i in GroupSelections]
        DropDownOptions['Crop'] = []
        DropDownOptions['Type'] = []
    return Values, DropDownOptions

def checkCropOptions(Values,DropDownOptions,CropCoefficients,pos):
    GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'EndUse'] == Values['EndUse'],"Group"].drop_duplicates().dropna().values
    GroupSelections.sort()
    DropDownOptions['Group'] = [{'label':i,'value':i} for i in GroupSelections] 
    CropSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'EndUse'] == Values['EndUse'])&(CropCoefficients.loc[:,'Group'] == Values['Group']),"Colloquial Name"].drop_duplicates().dropna().values
    CropSelections.sort()
    if len(CropSelections) <= 1:
            DropDownOptions['Crop'] = [{'label':CropSelections[0]+" is the only " + Values['EndUse']+" crop",'value': CropSelections[0]}]
            Values['Crop'] = CropSelections[0]
            Values, DropDownOptions = checkTypeOptions(Values, DropDownOptions,CropCoefficients,pos)
    else:
        DropDownOptions['Crop'] = [{'label':i,'value':i} for i in CropSelections]
        DropDownOptions['Type'] = []
    return Values, DropDownOptions

def checkTypeOptions(Values,DropDownOptions,CropCoefficients,pos):
    GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'EndUse'] == Values['EndUse'],"Group"].drop_duplicates().dropna().values
    GroupSelections.sort()
    DropDownOptions['Group'] = [{'label':i,'value':i} for i in GroupSelections] 
    CropSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'EndUse'] == Values['EndUse'])&(CropCoefficients.loc[:,'Group'] == Values['Group']),"Colloquial Name"].drop_duplicates().dropna().values
    CropSelections.sort()
    DropDownOptions['Crop'] = [{'label':i,'value':i} for i in CropSelections]
    TypeSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'EndUse'] == Values['EndUse'])&(CropCoefficients.loc[:,'Group'] == Values['Group'])&(CropCoefficients.loc[:,'Colloquial Name'] == Values['Crop']),"Type"].drop_duplicates().dropna().values
    if len(TypeSelections) <= 1:
            DropDownOptions['Type'] = [{'label':Values['Crop']+" has no Type options",'value': TypeSelections[0]}]
            Values['Type'] = TypeSelections[0]
    else:
        DropDownOptions['Type'] = [{'label':i,'value':i} for i in TypeSelections]
    return Values, DropDownOptions

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
        updateConfig([act],[np.datetime64(datedf.loc[d,'date'])],pos+"Config.pkl")
    
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

def makeDataSeries(names,values):
    Names = []
    for n1 in range(len(names)):
        for n2 in range(len(names[n1])):
            Names.append(names[n1][n2]['id']['id'])
    df = pd.Series(index=Names,data=values)
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

def CropInputs(pos,EndUseCatagoriesDropdown,disableDates,EDatePHtext,HDatePHtext):
    return dbc.CardBody([
    dbc.Row([dbc.Col([html.Div('EndUse')], width=3, align='center'),
             dbc.Col([html.Div('Group')], width=3, align='center'),
             dbc.Col([html.Div('Crop')], width=3, align='center'),
             dbc.Col([html.Div('Type')], width=3, align='center')]), 
    dbc.Row([dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"EndUse"},options = EndUseCatagoriesDropdown,placeholder=' Select crop EndUse')],
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"EndUse"}, width=3 ,align='center'),
             dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group"},options = [],style={"--bs-body-color": "#e83e8c"}, placeholder=' Select "EndUse" first' )], 
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"Group"}, width=3 ,align='center'),
             dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop"},options = [], placeholder=' Select "Group" first')], 
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"Crop"}, width=3 ,align='center'),
             dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type"},options = [], placeholder='')], 
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"Type"}, width=3 ,align='center')]),
    dbc.Row([dbc.Col([html.Div('Yield Data', id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"ProductType"},style=dict(display='flex', justifyContent='right'))],
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"Product Type"}, width=2, align='center'),
             dbc.Col([dcc.Input(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SaleableYield"}, type="number",placeholder = "Enter Expected Yield",min=0,style={"width": "100%"})],
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"SaleableYield"}, width=3, align='center'),
             dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units"},options = [], placeholder = "")], 
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"Units"},width=2, align='center'),
             dbc.Col([html.Div('at',style=dict(display='flex', justifyContent='center'))], width = 1, align='center'),
             dbc.Col([dcc.Input(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"MoistureContent"}, type="number",min=0,max=96,style={"width": "100%"})],
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"MoistureContent"}, align='center', width=1),
             dbc.Col([html.Div('% Moisture',style=dict(display='flex', justifyContent='left'))], width=2, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Field Loss (%)',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.Input(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"FieldLoss"}, type="number",min=0,max=100)],
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"FieldLoss"}, width=3, align='center'),
             dbc.Col([html.Div('Dressing loss (%)',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.Input(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"DressingLoss"}, type="number",min=0,max=100)],
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"DressingLoss"}, width=3, align='center')]), 
    dbc.Row([
             ]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Planting Date',style=dict(display='flex', justifyContent='right'))], width=2, align='center'),
             dbc.Col([dcc.DatePickerSingle(id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"date","id":"EstablishDate"}, min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2025, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            placeholder = EDatePHtext, display_format='D-MMM-YYYY',disabled = disableDates)], 
                     id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"children","id":"EstablishDate"},width=2, align='center'),
             dbc.Col([html.Div('Planting method',style=dict(display='flex', justifyContent='right'))], width=2, align='center'),
             dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage"},options =[], placeholder='')],
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"EstablishStage"}, width=2, align='center'),
             dbc.Col([html.Div()],width=2, align='center'),
             dbc.Col([html.Div()],width=2, align='center')
            ]), 
    dbc.Row([dbc.Col([html.Div('Defoliatoin Dates')], width=3, align='center'),
            dbc.Col([dcc.Checklist(id={"pos":pos,"Group":"Crop","subGroup":"defoliation","RetType":"value","id":"DefoliationDates"},options=[])],
                    id={"pos":pos,"Group":"Crop","subGroup":"defoliation","RetType":"children","id":"DefoliationDates"})
            ]),
    dbc.Row([dbc.Col([html.Div('Harvest Date',style=dict(display='flex', justifyContent='right'))], width=2, align='center'),
             dbc.Col([dcc.DatePickerSingle(id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"date","id":"HarvestDate"}, min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2025, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            placeholder = HDatePHtext,display_format='D-MMM-YYYY',disabled=True)], 
                     id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"children","id":"HarvestDate"}, width=2, align='center'), 
             dbc.Col([html.Div('Harvest Stage',style=dict(display='flex', justifyContent='right'))], width=2, align='center'),
             dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage"},options = [],placeholder='')], 
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"HarvestStage"}, width=2, align='center'),
             dbc.Col([html.Div('Residue Treatment',style=dict(display='flex', justifyContent='right'))], width=2, align='center'),
             dbc.Col([dcc.Dropdown(id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"ResidueTreatment"},options =[], placeholder='')],
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"ResidueTreatment"}, width=2, align='center')
            ]), 
    # html.Br(),
    ])
# -


