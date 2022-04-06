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
# %%writefile C:\Anaconda\Lib\CropNBalFunctions.py

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

Positions = ['Previous_','Current_','Following_']
Actions = ["EstablishDate", "HarvestDate"]

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

UIConfigMap = pd.DataFrame([("SYInput","SaleableYield"),
                            ("Units DD","UnitConverter"),
                            ("FLInput","FieldLoss"),
                            ("DLInput","DressingLoss"),
                            ("MCInput","MoistureContent"),
                            ("EstablishStage DD","EstablishStage"),
                            ("HarvestStage DD","HarvestStage"),
                            ("Def Dates","DefoliationDates")]
                            ,columns=["UIID","ConfigID"])
UIConfigMap.set_index("UIID",inplace=True)

def splitprops(prop_ID,propExt):
    prop_ID = prop_ID.replace(propExt,'')
    return prop_ID.split('_')[0]+'_', prop_ID.split('_')[1]

def Generalcomponents():
    # Read in Crop coefficients table and filter out nasty ones
    CropCoefficients = pd.read_excel('C:\\GitHubRepos\\Overseer-testing\\CropCoefficients\\CropCoefficientTable.xlsx',skiprows=2)

    # Make lists of end use options
    EndUseCatagories = CropCoefficients.loc[:,'End use'].drop_duplicates().dropna().values
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


Methods = ['Seed','Seedling','Vegetative','EarlyReproductive','MidReproductive','LateReproductive','Maturity','Late']
EstablishStageDropdown = [{'label':i,'value':i} for i in Methods[:2]]
HarvestStageDropdown = [{'label':i,'value':i} for i in Methods[2:]]
#Empty arrays to hold example data
BiomassScaller = []
CoverScaller = []
RootDepthScaller = []
#Example parameters
Xo_Biomass = 50
b_Biomass = Xo_Biomass*0.2
A_cov = 1
T_mat = Xo_Biomass*2
T_sen = T_mat-30
Xo_cov = T_mat * 0.25
b_cov = Xo_cov * 0.3
#Example thermal time series
Tts = range(150)
#Calculate biomass, cover and root depth callers at each Tt in the series
for tt in Tts:
    BiomassScaller.append(1/(1+np.exp(-((tt-Xo_Biomass)/(b_Biomass)))))
    cover = 0
    if tt < T_sen:
        cover = A_cov * 1/(1+np.exp(-((tt-Xo_cov)/b_cov)))
        rd = tt/T_sen
    else:
        if tt < T_mat:
            cover = A_cov * (1-(tt-T_sen)/(T_mat-T_sen))
            rd = 1.0
    CoverScaller.append(cover)
    RootDepthScaller.append(rd)

#PackScallers into a data frame    
Scallers = pd.DataFrame(index=Tts,data=BiomassScaller,columns=['scaller'])
Scallers.loc[:,'cover'] = CoverScaller
Scallers.loc[:,'rootDepth'] = RootDepthScaller
Scallers.loc[:,'max'] = Scallers.max(axis=1)

#Set up data frame with the assumed proportion of MAX DM accumulated at each reproductive stage
PrpnMaxDM = [0.0066,0.015,0.5,0.75,0.86,0.95,0.9933,0.9995]
StagePropns = pd.DataFrame(index = Methods, data = PrpnMaxDM,columns=['PrpnMaxDM']) 
#Calculate the proportion of thermal time that each stage will accumulate at and graph
for p in StagePropns.index:
    TTatProp = bisect_left(Scallers.scaller,StagePropns.loc[p,'PrpnMaxDM'])
    StagePropns.loc[p,'PrpnTt'] = TTatProp/T_mat


def CalculateMedianTt(Start, End, Met):
    ## Calculate median thermaltime for location
    duration = (End-Start+dt.timedelta(days=1)).days
    FirstYear = int(Met.Year[0])
    years = [x for x in Met.Year.drop_duplicates().values[1:-1]]
    day = Start.day
    month = Start.month
    FirstDate = dt.date(FirstYear,month,day)
    TT = pd.DataFrame(columns = years,index = range(1,duration+1))
    for y in years:
        start = str(int(y)) + '-' + str(Start.month) + '-' + str(Start.day)
        try:
            TT.loc[:,y] = Met.loc[start:,'tt'].cumsum().values[:duration]
        except:
            do = 'nothing'
    TTmed = TT.median(axis=1)
    TTmed.index = pd.date_range(start=Start,periods=duration,freq='D',name='Date')
    TTmed.name = 'Tt'
    return TTmed
    

def CalculateCropOutputs(Tt, c, CropCoefficients):

    CropFilter = (CropCoefficients.loc[:,'End use'] == c["End use"])&(CropCoefficients.loc[:,'Group'] == c["Group"])\
                 &(CropCoefficients.loc[:,'Colloquial Name'] == c["Crop"])&(CropCoefficients.loc[:,'Type'] == c["Type"])
    Params = pd.Series(index=CropCoefficients.loc[CropFilter,CropParams].columns, data = CropCoefficients.loc[CropFilter,CropParams].values[0])
    if (c["FieldLoss"]==0) and (c["DressingLoss"]==0):
        BiomassComponents = ['Root','+ Stover','TotalCrop']
        NComponentColors = ['brown','orange','green']
    if (c["FieldLoss"]>0) and (c["DressingLoss"]>0):
        BiomassComponents = ['Root','+ Stover','+ FieldLoss','+ DressingLoss','TotalCrop']
        NComponentColors = ['brown','orange','red','blue','green']
    if (c["FieldLoss"]>0) and (c["DressingLoss"]==0):
        BiomassComponents = ['Root','+ Stover','+ FieldLoss','TotalCrop']
        NComponentColors = ['brown','orange','red','green']
    if (c["FieldLoss"]==0) and (c["DressingLoss"]>0):
        BiomassComponents = ['Root','+ Stover','+ DressingLoss','TotalCrop']
        NComponentColors = ['brown','orange','blue','green']
    CropN = pd.DataFrame(index = pd.MultiIndex.from_product([BiomassComponents,Tt.index],
                                                        names=['Component','Date']),columns=['Values'])
    CropWater = pd.DataFrame(index = pd.MultiIndex.from_product([['Cover','RootDepth'],Tt.index],
                                                        names=['Component','Date']),columns=['Values'])
    ## Calculate model parameters 
    Tt_Harv = Tt[c['HarvestDate']]
    Tt_estab = Tt_Harv * (StagePropns.loc[c['EstablishStage'],'PrpnTt']/StagePropns.loc[c['HarvestStage'],'PrpnTt'])
    CropTt = Tt+Tt_estab #Create array of Tt accumulations during crop duration.
    Xo_Biomass = (Tt_Harv + Tt_estab) *.45 * (1/StagePropns.loc[c["HarvestStage"],'PrpnTt'])
    b_Biomass = Xo_Biomass * .25
    T_mat = Xo_Biomass * 2.2222
    T_maxRD = StagePropns.loc["EarlyReproductive",'PrpnTt']*T_mat
    T_sen = StagePropns.loc["MidReproductive",'PrpnTt']*T_mat
    Xo_cov = Xo_Biomass * 0.4 / Params['rCover']
    b_cov = Xo_cov * 0.2
    a_harvestIndex = Params['Typical HI'] - Params['HI Range']
    b_harvestIndex = Params['HI Range']/Params['Typical Yield']
    # Calculate fitted patterns
    BiomassScaller = []
    CoverScaller = []
    RootDepthScaller = []
    for tt in CropTt:
        BiomassScaller.append(1/(1+np.exp(-((tt-Xo_Biomass)/(b_Biomass)))))
        if tt < T_maxRD:
            rd = tt/T_maxRD
        else:
            if tt < T_mat:
                rd = 1.0
        RootDepthScaller.append(rd)
        if tt < T_sen:
            cover = 1/(1+np.exp(-((tt-Xo_cov)/b_cov)))
        else:
            if tt < T_mat:
                cover = (1-(tt-T_sen)/(T_mat-T_sen))
        CoverScaller.append(cover)
    #Crop Failure.  If yield is very low of field loss is very high assume complete crop failure.  Uptake equation are too sensitive saleable yields close to zero and field losses close to 100
    if ((c["SaleableYield"] * c['UnitConverter']) <(Params['Typical Yield']*0.05)) or (c["FieldLoss"]>95):
        c["SaleableYield"] = Params['Typical Yield']
        c["FieldLoss"] = 100
        FreshProductWt = Params['Typical Yield'] * (1/(1-Params['Typical Dressing Loss %']/100))
    else:
        FreshProductWt = c["SaleableYield"] * (1/(1-c["FieldLoss"]/100)) * (1/(1-c["DressingLoss"]/100))
    DryProductWt = FreshProductWt * c['UnitConverter'] * (1-c["MoistureContent"]/100)
    HI = a_harvestIndex + c["SaleableYield"] * b_harvestIndex
    DryStoverWt = DryProductWt * 1/HI - DryProductWt 
    DryRootWt = (DryStoverWt+DryProductWt) * Params['P Root']
    TotalProductN = DryProductWt * Params['Product [N]']/100
    c['StoverN'] = DryStoverWt * Params['Stover [N]']/100
    c['RootN'] = DryRootWt * Params['Root [N]']/100
    c['FieldLossN'] = (TotalProductN * c["FieldLoss"]/100)
    c['DressingLossN'] = (TotalProductN * c["DressingLoss"]/100)
    c['CropN'] = c['RootN'] + c['StoverN'] + TotalProductN
    dates = Tt[c['EstablishDate']:c['HarvestDate']].index
    CropN.loc[[('Root',d) for d in Tt[dates].index],'Values'] = np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), c['RootN'])
    CropN.loc[[('+ Stover',d) for d in Tt[dates].index],'Values'] = np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), c['RootN']+c['StoverN'])
    if c["FieldLoss"]>0:
        CropN.loc[[('+ FieldLoss',d) for d in Tt[dates].index],'Values'] = np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), c['RootN'] + c['StoverN'] + c['FieldLossN'])
    if c["DressingLoss"]>0:
        CropN.loc[[('+ DressingLoss',d) for d in Tt[dates].index],'Values'] = np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), c['RootN'] + c['StoverN'] + c['FieldLossN'] + c['DressingLossN'])
    CropN.loc[[('TotalCrop',d) for d in Tt[dates].index],'Values'] = np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), c['CropN'])
    CropWater.loc[[('Cover',d) for d in Tt[dates].index],'Values'] = np.multiply(CoverScaller, Params["A cover"])
    CropWater.loc[[('RootDepth',d) for d in Tt[dates].index],'Values'] = np.multiply(RootDepthScaller, Params["Max RD"])
    if len(c["DefoliationDates"])>0:
        CropN.sort_index(inplace=True)
        for dd in c["DefoliationDates"]:
            StoverNtoRemove = (CropN.loc[('+ Stover',dd),'Values'].values[0] - CropN.loc[('Root',dd),'Values'].values[0]) * 0.7
            TotalNtoRemove = StoverNtoRemove
            if Params['Yield type'] == 'Standing DM':
                StoverNtoRemove=0
                TotalNtoRemove = (CropN.loc[('TotalCrop',dd),'Values'].values[0] - CropN.loc[('Root',dd),'Values'].values[0]) * 0.7
            DefCovFact = 0.3
            for d in Tt[dates][dd:].index:
                CropN.loc[('+ Stover',d),'Values'] = CropN.loc[('+ Stover',d),'Values'] - StoverNtoRemove 
                CropN.loc[('TotalCrop',d),'Values'] = CropN.loc[('TotalCrop',d),'Values'] - TotalNtoRemove
                CropWater.loc[('Cover',d),'Values'] = CropWater.loc[('Cover',d),'Values'] * DefCovFact
                DefCovFact = min(1.0,DefCovFact + Tt[d] * 0.00001)
    return CropN, CropWater, NComponentColors

def setCropConfig(data):
    CropConfigs = ["Location","End use","Group","Crop","Type","SaleableYield","UnitConverter","FieldLoss","DressingLoss",
               "MoistureContent","EstablishDate","EstablishStage","HarvestDate","HarvestStage","DefoliationDates"]
    return pd.Series(index = CropConfigs,data = data)

def updateConfig(keys,values,ConfigAddress):
    Config = pd.read_pickle(ConfigAddress)
    its = range(len(keys))
    for i in its:
        if values[i] != None:
            Config[keys[i]] = values[i]
    Config.to_pickle(ConfigAddress)

def CropInputs(pos,EndUseCatagoriesDropdown,disableDates,EDatePHtext,HDatePHtext):
    return dbc.CardBody([
    dbc.Row([dbc.Col([html.Div('End use')], width=3, align='center'),
             dbc.Col([html.Div('Group')], width=3, align='center'),
             dbc.Col([html.Div('Crop')], width=3, align='center'),
             dbc.Col([html.Div('Type')], width=3, align='center')]), 
    dbc.Row([dbc.Col([dcc.Dropdown(id=pos+"End use DD",options = EndUseCatagoriesDropdown,placeholder=' Select crop End use')],id=pos+"End use", width=3 ,align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"Group DD",options = [],style={"--bs-body-color": "#e83e8c"}, placeholder=' Select "End use" first' )], id=pos+"Group", width=3 ,align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"Crop DD",options = [], placeholder=' Select "Group" first')], id=pos+"Crop", width=3 ,align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"Type DD",options = [], placeholder='')], id=pos+"Type", width=3 ,align='center')]),
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Yield Data', id=pos+"PTtext",style=dict(display='flex', justifyContent='right'))], id=pos+"Product Type", width=2, align='center'),
             dbc.Col([dcc.Input(id=pos+ "SYInput", type="number",placeholder = "Enter Expected Yield",min=0,style={"width": "100%"})],id=pos+"SaleableYield", width=3, align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"Units DD",options = [], placeholder = "")], id=pos+"Units",width=2, align='center'),
             dbc.Col([html.Div('at',style=dict(display='flex', justifyContent='center'))], width = 1, align='center'),
             dbc.Col([dcc.Input(id=pos+"MCInput", type="number",min=0,max=96,style={"width": "100%"})],id=pos+"MoistureContent", align='center', width=1),
             dbc.Col([html.Div('% Moisture',style=dict(display='flex', justifyContent='left'))], width=2, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Field Loss (%)',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.Input(id=pos+"FLInput", type="number",min=0,max=100)],id=pos+"FieldLoss", width=3, align='center'),
             dbc.Col([html.Div('Dressing loss (%)',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.Input(id=pos+"DLInput", type="number",min=0,max=100)],id=pos+"DressingLoss", width=3, align='center')]), 
    dbc.Row([
             ]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Planting Date',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.DatePickerSingle(id=pos+"EstablishDate DP", min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2022, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            placeholder = EDatePHtext, display_format='D-MMM-YYYY',disabled = disableDates)], id=pos+"EstablishDate",width=3, align='center'),
             dbc.Col([html.Div('Planting method',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"EstablishStage DD",options =[], placeholder='')],id=pos+"EstablishStage", width=3, align='center')]), 
    # html.Br(),
    dbc.Row([dbc.Col([html.Div('Harvest Date',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.DatePickerSingle(id=pos+"HarvestDate DP", min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2022, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            placeholder = HDatePHtext,display_format='D-MMM-YYYY',disabled=True)], id=pos+"HarvestDate", width=3, align='center'), 
             dbc.Col([html.Div('Harvest Stage',style=dict(display='flex', justifyContent='right'))], width=3, align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"HarvestStage DD",options = [],placeholder='')], id=pos+"HarvestStage", width=3, align='center')]), 
    dbc.Row([dbc.Col([html.Div('Defoliatoin Dates')], width=3, align='center'),
            dbc.Col([dcc.Checklist(id=pos+"Def Dates",options=[])],id=pos+"Defoliation Dates")]), 
    # html.Br(),
    ])

def UpdateCropOptions(EndUseValue, GroupValue, CropValue, TypeValue, CropCoefficients, pos):
    PopulateDefaults = False
    GroupDropDown = dcc.Dropdown(options = [], disabled = True,style={"--bs-body-color": "#e83e8c"}, placeholder='Choose "End use" first', id=pos+"Group DD")
    CropDropDown = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "End use" first', id=pos+"Crop DD")
    TypeDropDown = dcc.Dropdown(options = [], disabled = True, placeholder='No Type Choices', id=pos+"Type DD")
    SalableYieldInput = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id=pos+ "SYInput")
    UnitDropDown = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id=pos+"Units DD")
    ProductType = html.Div("Yield Data", id=pos+"PTtext",style=dict(display='flex', justifyContent='right'))
    FieldLossInput = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id=pos+ "FLInput")
    DressingLossInput = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id=pos+ "DLInput")
    MoistureContentInput = dcc.Input(type="number",disabled = True, placeholder='Choose "Crop" first',min=0,id=pos+ "MCInput",style={"width": "100%"})
    #EstablishDateDP = dcc.DatePickerSingle(id=pos+"EstablishDate DP", placeholder = 'Choose "Crop" first', disabled = True)
    EstablishStageDD = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id=pos+"EstablishStage DD")
    #HarvestDateDP = dcc.DatePickerSingle(id=pos+"HarvestDate DP", placeholder = 'Choose "Crop" first', disabled = True)
    HarvestStageDD = dcc.Dropdown(options = [], disabled = True, placeholder='Choose "Crop" first', id=pos+"HarvestStage DD")
    
    def SetGroupDropDown():
        GroupSelections = CropCoefficients.loc[CropCoefficients.loc[:,'End use'] == EndUseValue,"Group"].drop_duplicates().dropna().values
        GroupSelections.sort()
        Options = True
        if len(GroupSelections)==1:
                noOptions = [{'label':"No Groups for " +EndUseValue+" end use",'value': GroupSelections[0]}]
                GroupDropDown =  dcc.Dropdown(options = noOptions, disabled = True, value=GroupSelections[0], placeholder=GroupSelections[0], id=pos+"Group DD")
                updateConfig(["Group"],[GroupSelections[0]],pos+"Config.pkl")
                Options = False
        else:
            GroupDropDownOptions = [{'label':i,'value':i} for i in GroupSelections]
            GroupDropDown =  dcc.Dropdown(options = GroupDropDownOptions, value = GroupValue, placeholder = "Choose Group" , id=pos+"Group DD")
        return GroupDropDown, Options, GroupSelections
    
    def SetCropDropDown(g):
        CropSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'End use'] == EndUseValue)&(CropCoefficients.loc[:,'Group'] == g),"Colloquial Name"].drop_duplicates().dropna().values
        CropSelections.sort()
        Options = True
        if len(CropSelections) == 1:
                noOptions = [{'label':CropSelections[0]+" is the only " + EndUseValue+" crop",'value': CropSelections[0]}]
                CropDropDown = dcc.Dropdown(options = noOptions, disabled=True, value=CropSelections[0], placeholder=CropSelections[0],id=pos+"Crop DD")
                Options = False
                updateConfig(["Crop"],[CropSelections[0]],pos+"Config.pkl") 
        else:
            CropDropDownOptions = [{'label':i,'value':i} for i in CropSelections]
            CropDropDown = dcc.Dropdown(options = CropDropDownOptions, value = CropValue, placeholder = "Choose Crop", id=pos+"Crop DD")
        return CropDropDown,Options,CropSelections
    
    def SetTypeDropDown(g,c):
        TypeSelections = CropCoefficients.loc[(CropCoefficients.loc[:,'End use'] == EndUseValue)&(CropCoefficients.loc[:,'Group'] == g)&(CropCoefficients.loc[:,'Colloquial Name'] == c),"Type"].drop_duplicates().dropna().values
        TypeSelections.sort()
        PopulateDefaults = False
        if len(TypeSelections) == 1:
                noOptions = [{'label':c+" has no Type options",'value': ""}]
                TypeDropDown = dcc.Dropdown(options = noOptions, disabled=True, value="", placeholder="",id=pos+"Type DD")
                updateConfig(["Type"],[TypeSelections[0]],pos+"Config.pkl")
                PopulateDefaults = True
        else:
            TypeDropDownOptions = [{'label':i,'value':i} for i in TypeSelections]
            TypeDropDown = dcc.Dropdown(options = TypeDropDownOptions, value = TypeValue, placeholder='Choose Type',id=pos+"Type DD")
        return TypeDropDown, PopulateDefaults
    
    ctx = dash.callback_context
    if (ctx.triggered[0]['prop_id'] == pos+'End use DD.value') and (EndUseValue != None):
        GroupDropDown,GroupOptions,GroupSelections = SetGroupDropDown()
        if GroupOptions == False:
            CropDropDown,CropOptions,CropSelections = SetCropDropDown(GroupSelections[0])
            if CropOptions == False:
                TypeDropDown,PopulateDefaults = SetTypeDropDown(GroupSelections[0],CropSelections[0])
        updateConfig(["End use"],[EndUseValue],pos+"Config.pkl")
    if (ctx.triggered[0]['prop_id'] == pos+'Group DD.value') & (GroupValue != None):
        GroupDropDown,GroupOptions,GroupSelections = SetGroupDropDown()
        CropDropDown,CropOptions,CropSelections = SetCropDropDown(GroupValue)
        if CropOptions == False:
            TypeDropDown,PopulateDefaults = SetTypeDropDown(GroupValue,CropSelections[0])
        updateConfig(["Group"],[GroupValue],pos+"Config.pkl")
    if (ctx.triggered[0]['prop_id'] == pos+'Crop DD.value') & (CropValue != None):
        GroupDropDown = SetGroupDropDown()[0]
        CropDropDown = SetCropDropDown(GroupValue)[0]
        TypeDropDown,PopulateDefaults = SetTypeDropDown(GroupValue,CropValue)
        updateConfig(["Crop"],[CropValue],pos+"Config.pkl") 
    if (ctx.triggered[0]['prop_id'] == pos+'Type DD.value') & (TypeValue != None):
        GroupDropDown = SetGroupDropDown()[0]
        CropDropDown = SetCropDropDown(GroupValue)[0]
        TypeDropDown,PopulateDefaults = SetTypeDropDown(GroupValue,CropValue)        
        updateConfig(["Type"],[TypeValue],pos+"Config.pkl")
        PopulateDefaults = True
    
    if (PopulateDefaults == True):
        c = pd.read_pickle(pos+"Config.pkl")
        CropFilter = (CropCoefficients.loc[:,'End use'] == c["End use"])&(CropCoefficients.loc[:,'Group'] == c["Group"])\
                     &(CropCoefficients.loc[:,'Colloquial Name'] == c["Crop"])&(CropCoefficients.loc[:,'Type'] == c["Type"])
        Params = pd.Series(index=CropCoefficients.loc[CropFilter,CropParams].columns, data = CropCoefficients.loc[CropFilter,CropParams].values[0])
        SalableYieldInput = dcc.Input(type="number",disabled = False, value = Params["Typical Yield"],min=0,id=pos+ "SYInput")
        UnitDropDown = dcc.Dropdown(options = UnitsDropDown, disabled = False, value =Units.loc[Params["Typical Yield Units"],"toKG/ha"], id=pos+"Units DD")
        ProductType = html.Div(Params['Yield type'] + " yield", id=pos+"PTtext",style=dict(display='flex', justifyContent='right'))
        FieldLossInput = dcc.Input(type="number",disabled = False, value = Params["Typical Field Loss %"],min=0,id=pos+ "FLInput")
        DressingLossInput = dcc.Input(type="number",disabled = False, value = Params["Typical Dressing Loss %"],min=0,id=pos+ "DLInput")
        MoistureContentInput = dcc.Input(type="number",disabled = False, value = (round(Params["Moisture %"],0)),min=0,id=pos+ "MCInput",style={"width": "100%"})
        # EstablishDateDP = dcc.DatePickerSingle(id=pos+"EstablishDate DP", min_date_allowed=dt.date(2020, 1, 1),
        #                                     max_date_allowed=dt.date(2022, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
        #                                     placeholder = "Select planting date", display_format='D-MMM-YYYY')
        EstablishStageDD = dcc.Dropdown(options = EstablishStageDropdown, disabled = False, value =Params["Typical Establish Stage"], id=pos+"EstablishStage DD")
        # HarvestDateDP = dcc.DatePickerSingle(id=pos+"HarvestDate DP", placeholder = "Select sowing date first", disabled =True)
        HarvestStageDD = dcc.Dropdown(options = HarvestStageDropdown, disabled = False, value =Params["Typical Harvest Stage"], id=pos+"HarvestStage DD")
        updateConfig(["SaleableYield","UnitConverter","FieldLoss","DressingLoss","MoistureContent","EstablishStage","HarvestStage"],
                     [Params["Typical Yield"],Units.loc[Params["Typical Yield Units"],"toKG/ha"],Params["Typical Field Loss %"],
                      Params["Typical Dressing Loss %"],Params["Moisture %"],Params["Typical Establish Stage"],Params["Typical Harvest Stage"]],pos+"Config.pkl")
    else:
        updateConfig(["SaleableYield","UnitConverter","FieldLoss","DressingLoss","MoistureContent",
                      "EstablishDate","EstablishStage","HarvestDate","HarvestStage"],
                     [0,1,0,0,0,np.datetime64("NaT"),"Seed",np.datetime64("NaT"),"EarlyReproductive"],
                     pos+"Config.pkl")
    return GroupDropDown, CropDropDown, TypeDropDown, SalableYieldInput, UnitDropDown, ProductType, FieldLossInput, DressingLossInput, MoistureContentInput, EstablishStageDD, HarvestStageDD

def SetDatePicker(pos,act,PHtext,minDate,selDate,isEnabled):
    if isEnabled:
        DateP = dcc.DatePickerSingle(id=pos+act+" DP", date = selDate, placeholder = PHtext,
                                          min_date_allowed=minDate, max_date_allowed=dt.date(2023, 12, 31), 
                                          initial_visible_month = selDate, display_format='D-MMM-YYYY')     
    else:
        DateP = dcc.DatePickerSingle(id=pos+act+" DP", placeholder = PHtext, disabled = True)
    return DateP

def UpdateDatePickerOptions():
    dateVals = pd.DataFrame(index = pd.MultiIndex.from_product([Positions,Actions]),
                             columns = ['value'])
    for d in dateVals.index:
        c = pd.read_pickle(d[0]+"Config.pkl")
        dateVals.loc[d,'value'] = c[d[1]]
    
    posc = 0
    for pos in Positions:
        for act in Actions:
            if posc == 0:
                minDate = dt.date(2020,1,1)
                isEnabled = ~np.isnat(dateVals.iloc[0,0])
                selDate = dateVals.iloc[0,0].astype(dt.datetime)
                PHtext = 'Select Establish Date'
            else:
                minDate = dateVals.iloc[posc-1,0].astype(dt.datetime)
                isEnabled = ~np.isnat(dateVals.iloc[posc-1,0])
                if np.isnat(dateVals.iloc[posc,0]):
                    selDate = None
                else:    
                    selDate = dateVals.iloc[posc,0].astype(dt.datetime)
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

