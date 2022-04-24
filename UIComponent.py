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
               "MoistureContent","EstablishDate","EstablishStage","HarvestDate","HarvestStage",
               "ResidueTreatment","EstablishN","DefoliationDates"]

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
        Config=pd.read_pickle(pos+"Config.pkl")
        NotSet += Config.isnull().sum()
    if NotSet > 0: 
        return html.Button("Update NBalance",id="RefreshButton",disabled=True)
    else: 
        return html.Button("Update NBalance",id="RefreshButton",disabled=False)

def updateConfig(keys,values,ConfigAddress):
    Config = pd.read_pickle(ConfigAddress)
    its = range(len(keys))
    for i in its:
        Config[keys[i]] = values[i]
    Config.to_pickle(ConfigAddress)

ddStyle = style={"height":"95%","font-size":"95%",'color':'#3a3f44','background-color':'#3a3f44','border': '#3a3f44'}
adStyle = style={"height":"95%","font-size":"95%"}
diStyle = style={"width": "95%","height":"95%","font-size":"95%",'color':'#3a3f44','background-color':'#3a3f44'}
aiStyle = style={"width": "95%","height":"95%","font-size":"95%"}
dpStyle = style={"height":"95%",'color':'#3a3f44','background-color':'#3a3f44'}
headingStyle = {"width":"95%","height":"100%","font-size":"150%", "justifyContent":'left'}
textStyle = {"width":"95%","height":"95%","font-size":"95%","justifyContent":'left'}
colStyle = {"height":"95%"}
hrStyle = {'height':'8%'}
drStyle = {'height':'10%'}
trStyle = {'height':'5%'}
brStyle = {'height':'1%'}    
    
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
    outputDF['EndUse'] = dcc.Dropdown(value = Values['EndUse'], options = EndUseCatagoriesDropdown,placeholder='Pick End use',
                                      style = ddStyle,
                                      id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"EndUse"})
    outputDF['Group'] = dcc.Dropdown(options = [], disabled = True, placeholder='Pick "End use" first', 
                                     style = ddStyle,
                                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group"})
    outputDF['Crop'] = dcc.Dropdown(options = [], disabled = True, placeholder='Pick "Group" first', 
                                    style = ddStyle,
                                    id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop"})
    outputDF['Type'] = dcc.Dropdown(options = [], disabled = True, placeholder='Pick "Crop" first', 
                                    style = ddStyle,
                                    id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type"})
    
    # Set drop down configs based on selected values
    if Values['EndUse'] != None:
        Values, DropDownOptions = checkGroupOptions(Values, DropDownOptions, CropCoefficients,pos) 
        outputDF['Group'] = dcc.Dropdown(options = DropDownOptions['Group'],placeholder = 'Pick Group', value = Values['Group'],
                                         style = adStyle,
                                         id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group"})
        if Values['Group'] != None:
            Values, DropDownOptions = checkCropOptions(Values,DropDownOptions,CropCoefficients,pos)
            outputDF['Crop'] = dcc.Dropdown(options = DropDownOptions['Crop'],placeholder = 'Pick Crop', value = Values['Crop'], 
                                            style = adStyle,
                                            id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop"})        
            if Values['Crop'] != None:
                Values, DropDownOptions = checkTypeOptions(Values,DropDownOptions,CropCoefficients,pos)
                outputDF['Type'] = dcc.Dropdown(options = DropDownOptions['Type'],placeholder = 'Pick Type', value = Values['Type'], 
                                                style = adStyle,
                                                id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type"})
        
    #Enable Crop data fields and populate with default values if all crop selection catagories are made
    PopulateDefaults = (Values["EndUse"]!=None) & (Values["Group"]!=None) & (Values["Crop"]!=None) & (Values["Type"]!=None)
    if (PopulateDefaults == True):
        CropFilter = (CropCoefficients.loc[:,'EndUse'] == Values["EndUse"])&(CropCoefficients.loc[:,'Group'] == Values["Group"])\
                     &(CropCoefficients.loc[:,'Colloquial Name'] == Values["Crop"])&(CropCoefficients.loc[:,'Type'] == Values["Type"])
        Params = pd.Series(index=CropCoefficients.loc[CropFilter,CropParams].columns, data = CropCoefficients.loc[CropFilter,CropParams].values[0])
        outputDF['SaleableYield'] = dcc.Input(type="number",disabled = False, value = Params["Typical Yield"],min=0,
                                              style = aiStyle,
                                              id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SaleableYield"})
        outputDF['Units'] = dcc.Dropdown(options = UnitsDropDown, disabled = False, value =Units.loc[Params["Typical Yield Units"],"toKG/ha"], 
                                         style = adStyle,
                                         id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units"})
        outputDF['ProductType'] = html.Div(Params['Yield type'] + " yield", 
                                           style = textStyle,
                                           id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"ProductType"})
        outputDF['FieldLoss'] = dcc.Input(type="number",disabled = False, value = Params["Typical Field Loss %"],min=0,
                                          style = aiStyle,
                                          id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "FieldLoss"})
        outputDF['DressingLoss'] = dcc.Input(type="number",disabled = False, value = Params["Typical Dressing Loss %"],min=0,
                                             style = aiStyle,
                                             id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "DressingLoss"})
        outputDF['MoistureContent'] = dcc.Input(type="number",disabled = False, value = (round(Params["Moisture %"],0)),min=0,
                                                style = aiStyle,
                                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "MoistureContent"})
        outputDF['EstablishStage'] = dcc.Dropdown(options = EstablishStageDropdown, disabled = False, value =Params["Typical Establish Stage"], 
                                                  style = adStyle,
                                                  id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage"})
        outputDF['HarvestStage'] = dcc.Dropdown(options = HarvestStageDropdown, disabled = False, value =Params["Typical Harvest Stage"], 
                                                style = adStyle,
                                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage"})
        outputDF["ResidueTreatment"] = dcc.Dropdown(options = ResidueTreatDropdown, disabled = False, value = "Incorporated", 
                                                    style = adStyle,
                                                    id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"ResidueTreatment"})
        outputDF["EstablishN"] = dcc.Input(type="number",disabled = False, value = 0, min=0, 
                                                    style = aiStyle,
                                                    id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishN"})
        updateConfig(["SaleableYield","Units","FieldLoss","DressingLoss","MoistureContent","EstablishStage","HarvestStage","ResidueTreatment"],
                     [Params["Typical Yield"],Units.loc[Params["Typical Yield Units"],"toKG/ha"],Params["Typical Field Loss %"],
                      Params["Typical Dressing Loss %"],Params["Moisture %"],Params["Typical Establish Stage"],Params["Typical Harvest Stage"],1.0],
                     pos+"Config.pkl")
        updateConfig(["EndUse","Group","Crop","Type"],Values.values,pos+"Config.pkl")
    else:
        outputDF['SaleableYield'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,
                                              style = diStyle,
                                              id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SaleableYield"})
        outputDF['Units'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', 
                                         style = ddStyle,
                                         id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units"})
        outputDF['ProductType'] = html.Div("Yield Data", 
                                           style = textStyle,
                                           id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"ProductType"})
        outputDF['FieldLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,
                                          style = diStyle,
                                          id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "FieldLoss"})
        outputDF['DressingLoss'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,
                                             style = diStyle,
                                             id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "DressingLoss"})
        outputDF['MoistureContent'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,
                                                style = diStyle,
                                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "MoistureContent"})
        outputDF['EstablishStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', 
                                                  style = ddStyle,
                                                  id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage"})
        outputDF['HarvestStage'] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', 
                                                style = ddStyle,
                                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage"})
        outputDF["ResidueTreatment"] = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', 
                                                    style = ddStyle,
                                                    id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"ResidueTreatment"})
        outputDF['EstablishN'] = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,
                                             style = diStyle,
                                             id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "EstablishN"})
        updateConfig(["SaleableYield","Units","FieldLoss","DressingLoss","MoistureContent",
                      "EstablishStage","HarvestStage","ResidueTreatment"],
                     [0.0,1.0,0.0,0.0,0.0,"Seed","EarlyReproductive",1.0],
                     pos+"Config.pkl")
        updateConfig(["EndUse","Group","Crop","Type"],[None,None,None,None],pos+"Config.pkl")
    return list(outputDF[0:4]), list(outputDF[4:14])

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
    ## Crop Type informaiton
    dbc.Row([html.B(pos[:-1]+ " crop information",
                     style=headingStyle,
                     id = {"pos":pos,"Group":"Crop","subGroup":"Title","RetType":"displaytext","id":"PositionTitle"})],
           style=hrStyle),
    dbc.Row([dbc.Col([html.B('End use',
                            style = textStyle)],
                     width=3, align='center',style = colStyle),
             dbc.Col([html.B('Group', 
                             style = textStyle)],
                     width=3, align='center',style = colStyle),
             dbc.Col([html.B('Crop', 
                             style = textStyle)], 
                     width=3, align='center',style = colStyle),
             dbc.Col([html.B('Type', 
                             style = textStyle)], 
                     width=3, align='center',style = colStyle)],
           style=trStyle), 
    dbc.Row([dbc.Col([dcc.Dropdown(options = EndUseCatagoriesDropdown, placeholder=' Select crop EndUse',
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"EndUse"})],
                     width=3 ,align='center', style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"EndUse"}),
             dbc.Col([dcc.Dropdown(options = [], placeholder=' Select "EndUse" first' ,
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Group"})], 
                      width=3 ,align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"Group"}),
             dbc.Col([dcc.Dropdown(options = [], placeholder=' Select "Group" first',
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Crop"})], 
                     width=3 ,align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"Crop"}),
             dbc.Col([dcc.Dropdown(options = [], placeholder='',
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":"Type"})], 
                     width=3 ,align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":"Type"})],
           style=drStyle),
    dbc.Row([],style=brStyle),
    ## Crop Harvest Information
    dbc.Row([dbc.Col([html.B(pos[:-1]+ ' harvest information',
                               style=headingStyle,
                               id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"displaytext","id":"ProductType"})],
                     width=12, align='left',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"Product Type"})],
            style=hrStyle),
    dbc.Row([dbc.Col([dcc.Input(type="number",placeholder = "Enter Expected Yield",min=0,disabled=True,
                                style=diStyle,
                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id": "SaleableYield"})],
                      width=3, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"SaleableYield"}),
             dbc.Col([dcc.Dropdown(options = [], placeholder = "",disabled=True,
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"Units"})], 
                     width=3, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"Units"}),
             dbc.Col([html.Div('at',
                               style=dict(display='flex', justifyContent='center'))],
                     width = 1, align='center', style = colStyle),
             dbc.Col([dcc.Input(type="number",min=0,max=96,disabled=True,
                                style=diStyle,
                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"MoistureContent"})],
                     width=2, align='center', style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"MoistureContent"}),
             dbc.Col([html.Div('% Moisture',
                               style=dict(display='flex', justifyContent='left'))], 
                     width=3, align='left',style = colStyle)],
           style=drStyle), 
    dbc.Row([],style=brStyle),
    
    dbc.Row([dbc.Col([dcc.Input(type="number",min=0,max=100,disabled=True,
                                style=diStyle,
                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"FieldLoss"})],
                     width=2, align='right',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"FieldLoss"}),
             dbc.Col([html.Div('Field Loss (%)',
                               style=dict(display='flex', justifyContent='left'))],
                     width=3, align='left',style = colStyle),
             dbc.Col([dcc.Input(type="number",min=0,max=100,disabled=True,
                                style=diStyle,
                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"DressingLoss"})],
                      width=2, align='right',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"DressingLoss"}),
            dbc.Col([html.Div('Dressing loss (%)',
                               style=dict(display='flex', justifyContent='left'))], 
                     width=3, align='left',style = colStyle)],
           style=drStyle), 
    dbc.Row([],style=brStyle),
    

    # Crop Management Information    
    dbc.Row([dbc.Col([html.B(pos[:-1]+ ' management information',
                               style=headingStyle)],
                     width=12, align='left',style = colStyle)],
            style=hrStyle),
    dbc.Row([dbc.Col([html.Div('Planting Date',
                               style = textStyle)], 
                     width=4, align='center',style = colStyle),
             dbc.Col([html.Div('Planting method',
                               style = textStyle)], 
                     width=4, align='center',style = colStyle),
             dbc.Col([html.Div('Planting Nitrogen', 
                               style = textStyle)],
                     width=4, align='center',style = colStyle)],
             style=trStyle),    
    dbc.Row([dbc.Col([dcc.DatePickerSingle(min_date_allowed=dt.date(2020, 1, 1),
                                           max_date_allowed=dt.date(2025, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                           placeholder = EDatePHtext, display_format='D-MMM-YYYY', disabled = disableDates,
                                           style = dpStyle,
                                           id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"date","id":"EstablishDate"})], 
                     width=4, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"children","id":"EstablishDate"}),
             dbc.Col([dcc.Dropdown(options =[], placeholder='',disabled=True,
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishStage"})],
                     width=4, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"EstablishStage"}),
             dbc.Col([dcc.Input(type="number",min=0,max=400,disabled=True,
                                style=diStyle,
                                id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"EstablishN"})],
                     width=2, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"children","id":"EstablishN"}),
            dbc.Col([html.Div('kg/ha',
                               style=dict(display='flex', justifyContent='left'))],
                    width=2, align='left',style = colStyle)],
            style=drStyle), 
    dbc.Row([dbc.Col([html.Div('Harvest Date',
                               style = textStyle)], 
                     width=4, align='center',style = colStyle),
            dbc.Col([html.Div('Harvest Stage',
                               style = textStyle)],
                     width=4, align='center',style = colStyle),
            dbc.Col([html.Div('Residue Treatment',
                               style = textStyle)],
                     width=4, align='center',style = colStyle)],
            style=trStyle),
    dbc.Row([dbc.Col([dcc.DatePickerSingle(min_date_allowed=dt.date(2020, 1, 1),
                                           max_date_allowed=dt.date(2025, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                           placeholder = HDatePHtext,display_format='D-MMM-YYYY',disabled=True,
                                           style = dpStyle,
                                           id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"date","id":"HarvestDate"})], 
                     width=4, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"Event","RetType":"children","id":"HarvestDate"}), 
             dbc.Col([dcc.Dropdown(options = [],placeholder='',disabled=True,
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"HarvestStage"})], 
                     width=4, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"HarvestStage"}),
             dbc.Col([dcc.Dropdown(options =[], placeholder='',disabled=True,
                                   style=ddStyle,
                                   id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"value","id":"ResidueTreatment"})],
                     width=4, align='center',style = colStyle,
                     id={"pos":pos,"Group":"Crop","subGroup":"data","RetType":"children","id":"ResidueTreatment"})],
            style=drStyle), 
    dbc.Row([dbc.Col([html.Div('Defoliatoin Dates')], 
                     width=3, align='center',style = colStyle),
            dbc.Col([dcc.Checklist(options=[],
                                   id={"pos":pos,"Group":"Crop","subGroup":"defoliation","RetType":"value","id":"DefoliationDates"})],
                    width=9, align='left',style = colStyle,
                    id={"pos":pos,"Group":"Crop","subGroup":"defoliation","RetType":"children","id":"DefoliationDates"})],
            style=drStyle)],
    style={"height": "100%"})

# -


