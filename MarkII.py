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
import CropNBalUICompenents as uic
#from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
from dash.exceptions import PreventUpdate
import os

from dash import Dash, dcc, html, Input, Output, State, MATCH, ALL

# ## General components

CropCoefficients, EndUseCatagoriesDropdown, metFiles, MetDropDown, MonthIndexs = uic.Generalcomponents()

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

ConfigFiles = []
mydir = 'C:\GitHubRepos\SVS'
for File in os.listdir(mydir):
    if File.endswith('.pkl'):
        if ('_SavedConfig' in File):
            ConfigFiles.append(File.replace('_SavedConfig.pkl',''))

# +
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
StagePropns = pd.DataFrame(index = uic.Methods, data = PrpnMaxDM,columns=['PrpnMaxDM']) 
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

    CropFilter = (CropCoefficients.loc[:,'EndUse'] == c["EndUse"])&(CropCoefficients.loc[:,'Group'] == c["Group"])\
                 &(CropCoefficients.loc[:,'Colloquial Name'] == c["Crop"])&(CropCoefficients.loc[:,'Type'] == c["Type"])
    Params = pd.Series(index=CropCoefficients.loc[CropFilter,uic.CropParams].columns, data = CropCoefficients.loc[CropFilter,uic.CropParams].values[0])
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
    Tt = Tt- Tt[c['EstablishDate']] 
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
    if ((c["SaleableYield"] * c['Units']) <(Params['Typical Yield']*0.05)) or (c["FieldLoss"]>95):
        c["SaleableYield"] = Params['Typical Yield']
        c["FieldLoss"] = 100
        FreshProductWt = Params['Typical Yield'] * (1/(1-Params['Typical Dressing Loss %']/100))
    else:
        FreshProductWt = c["SaleableYield"] * (1/(1-c["FieldLoss"]/100)) * (1/(1-c["DressingLoss"]/100))
    DryProductWt = FreshProductWt * c['Units'] * (1-c["MoistureContent"]/100)
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

def CalculateResidueMineralisation(Tt,date, amounts):
    ResidueN = pd.DataFrame(index = pd.MultiIndex.from_product([BiomassComponents,Tt.index],
                                                        names=['Component','Date']),columns=['Values'])
    p = 0.1
    for d in Tt.index[1:]:
        yesterday = d-dt.timedelta(days=1) 
        ResidualN.loc[('Root',d),'Values'] = ResidualN.loc[('Root',yesterday),'Values']
        ResidualN.loc[('Stover',d),'Values'] = ResidualN.loc[('Stover',yesterday),'Values']
        ResidualN.loc[('FieldLoss',d),'Values'] = ResidualN.loc[('FieldLoss',yesterday),'Values']
        DeltaRootN[d] = ResidualN.loc[('Root',d),'Values'] * (Tt[d] - Tt[yesterday])* p
        DeltaStoverN[d] = ResidualN.loc[('Stover',d),'Values'] * (Tt[d] - Tt[yesterday])* p
        DeltaFieldLossN[d] = ResidualN.loc[('FieldLoss',d),'Values'] * (Tt[d] - Tt[yesterday])* p
        DeltaResidueN[d] = DeltaRootN[d] + DeltaStoverN[d] + DeltaFieldLossN[d]
        ResidualN.loc[('Root',d),'Values'] -= DeltaRootN[d]
        ResidualN.loc[('Stover',d),'Values'] -= DeltaStoverN[d]
        ResidualN.loc[('FieldLoss',d),'Values'] -= DeltaFieldLossN[d]
        for c in [PriorConfig,CurrentConfig,FollowingConfig]:
            if d == (c["HarvestDate"] + dt.timedelta(days=7)):
                ResidualN.loc[('Root',d),'Values'] += c['RootN']
                ResidualN.loc[('Stover',d),'Values'] += c['StoverN']
                ResidualN.loc[('FieldLoss',d),'Values'] += c['FieldLossN']
    ResidualN.loc['Stover','Values'] = (ResidualN.loc['Root','Values'] + ResidualN.loc['Stover','Values']).values
    ResidualN.loc['FieldLoss','Values'] = (ResidualN.loc['Stover','Values'] + ResidualN.loc['FieldLoss','Values']).values

def CalculateSOMMineralisation():
    p = 0.1
    for d in Tt.index[1:]:
        yesterday = d - dt.timedelta(days=1)
        DeltaSOMN[d] =  FieldConfig['HWEON'] * (Tt[d] - Tt[yesterday])* p
    CurrentConfig["SOMN"] = DeltaSOMN[CurrentConfig["EstablishDate"]:CurrentConfig["HarvestDate"]].sum()

def CalculateSoilMineralN():
    FinalN = 30
    Eff = 0.8
    splits = 3
    duration = (CurrentConfig['HarvestDate']-CurrentConfig['EstablishDate']).days
    InCropMineralisation = CurrentConfig[['RootN',"StoverN","FieldLossN","SOMN"]].sum()
    NFertReq = (CurrentConfig["CropN"] + FinalN) - FieldConfig["MineralN"] - InCropMineralisation
    NFertReq = NFertReq * 1/Eff
    NFertReq = np.ceil(NFertReq)
    print(NFertReq)
    NAppn = NFertReq/splits
    plength = duration/(splits + 1)
    xlocs = [0]
    plength = np.ceil(duration/(splits + 1))
    xlocs = []
    for x in range(1,int(splits+1)):
        xlocs.append(x * plength)
    FertApplied = 0
    FertAppNo = 0
    maxSoilN = max(FieldConfig["MineralN"],FinalN + NAppn)
    SoilN[CurrentConfig['EstablishDate']] = FieldConfig["MineralN"]
    for d in SoilN[CurrentConfig['EstablishDate']:].index[1:]:
        yesterday = d - dt.timedelta(days=1)
        CropNd = np.nan_to_num(CropN.loc['TotalCrop','Values'].diff()[d],0)
        SoilN[d] = SoilN[yesterday] + DeltaResidueN[d] + DeltaSOMN[d] - CropNd 
        if (SoilN[yesterday] > SoilN[d]) and (SoilN[d] < FinalN) and (FertApplied < NFertReq): #and ((CropPatterns.iloc[d-1,4]-CropPatterns.iloc[d,4])<0):
            SoilN[d] += NAppn * Eff
            FertApplied += NAppn


# -

# ## App layout and callbacks

# +
# Empty the config files
FieldConfigs = ['FieldName','Location','HWEON','MinN']
FieldConfig = pd.Series(index = FieldConfigs, data = [""]+[None]*3)
FieldConfig.to_pickle("Field_Config.pkl")

PreviousConfig = pd.Series(index = uic.CropConfigs,data = [None]*14+[[]])
PreviousConfig.to_pickle("Previous_Config.pkl")

CurrentConfig = pd.Series(index = uic.CropConfigs,data = [None]*14+[[]])
CurrentConfig.to_pickle("Current_Config.pkl")

FollowingConfig = pd.Series(index = uic.CropConfigs,data = [None]*14+[[]])
FollowingConfig.to_pickle("Following_Config.pkl")

import ast

app = JupyterDash(external_stylesheets=[dbc.themes.SLATE])


#Planting and Harvest date callback
@app.callback(Output({"pos":ALL,"Group":"Crop","subGroup":"Event","RetType":"children","id":ALL},'children'), 
              Input({"pos":ALL,"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), prevent_initial_call=True)
def StateCrop(dates):
    datedf = uic.makeDateDataDF(dash.callback_context.inputs_list,dates)
    return uic.UpdateDatePickerOptions(datedf)

# Crop type information callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"Catagory","RetType":"children","id":ALL},"children"),
              Output({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"children","id":ALL},"children"),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"Catagory","RetType":"value","id":ALL},"value"),
              prevent_initial_call=True)
def ChangeCrop(values):
    print('tick')
    if not any(values):
        raise PreventUpdate
    inputDF = uic.makeDataSeries(dash.callback_context.inputs_list,values)
    outputDF = uic.makeDataSeries(dash.callback_context.outputs_list,[""]*13)
    pos = dash.callback_context.outputs_list[0][0]['id']['pos']
    return uic.UpdateCropOptions(pos,inputDF,outputDF,CropCoefficients,EndUseCatagoriesDropdown)

# Defoliation callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"defoliation","RetType":"children","id":"DefoliationDates"},"children"),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"Event","RetType":"date","id":ALL},'date'), 
              prevent_initial_call=True)
def DefoliationOptions(dates):
    datedf = pd.DataFrame.from_dict(dash.callback_context.inputs,orient='index',columns=['date'])
    datedf.index = [x.replace(".date","") for x in datedf.index]
    pos = dash.callback_context.outputs_list['id']['pos']
    DefCheckMonths = []
    if (datedf.iloc[0,0] != None) and (datedf.iloc[1,0] != None):
        cropMonths = pd.date_range(dt.datetime.strptime(str(datedf.iloc[0,0]),'%Y-%m-%d'),
                                   dt.datetime.strptime(str(datedf.iloc[1,0]),'%Y-%m-%d'),freq='MS')
        DefCheckMonths = [{'label':MonthIndexs.loc[i.month,'Name'],'value':i} for i in cropMonths]    
    return [dcc.Checklist(id={"pos":"Previous_","Group":"Crop","subGroup":"defoliation","RetType":"value","id":"DefoliationDates"}, options = DefCheckMonths, value=[])]

# Crop yield information callback
@app.callback(Output({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"value","id":MATCH},'value'),
              Input({"pos":MATCH,"Group":"Crop","subGroup":"data","RetType":"value","id":MATCH},'value'), prevent_initial_call=True)
def setInputValue(value):
    pos = dash.callback_context.inputs_list[0]['id']['pos']
    outp = dash.callback_context.inputs_list[0]['id']['id']
    uic.updateConfig([outp],[value],pos+"Config.pkl")
    return value

# Activate Load and Save buttons
@app.callback(Output({"Group":"Field","subGroup":"FileButton","RetType":"children","id":ALL},"children"),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNamePicker"},'value'),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNameInput"},'value'),
              prevent_initial_call=True)
def FieldSet(selection,inputval):
    if (selection == None) and (inputval  == None):
        raise PreventUpdate
    else:
        loadbutton = html.Button("Load Config",id="LoadButton")
        savebutton = html.Button("Save Config",id="SaveButton")
    return loadbutton, savebutton

# Config load callback
@app.callback(Output({"Group":"UI","id":ALL},"children"),
              Output("LLtext","children"),
              Input("LoadButton","n_clicks"),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNamePicker"},'value'),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNameInput"},'value'),
              prevent_initial_call=True)
def loadConfig(n_clicks,selection,inputval):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if selection != None:
            FieldName = selection
        else:
            FieldName = inputval
        config = pd.read_pickle(FieldName+"_SavedConfig.pkl")
        time = dt.datetime.now()
        config["PreviousVal"].to_pickle("Previous_Config.pkl")
        config["CurrentVal"].to_pickle("Current_Config.pkl")
        config["FollowingVal"].to_pickle("Following_Config.pkl")
        config["FieldVal"].to_pickle("Field_Config.pkl")
    return (config["PreviousUI"], config["CurrentUI"], config["FollowingUI"], config["FieldUI"]), FieldName+" loaded at "+ str(time)

# Config Save callback
@app.callback(Output("LStext",'children'), 
              Input("SaveButton","n_clicks"), 
              Input({"Group":"UI","id":ALL},"children"),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNamePicker"},'value'),
              Input({"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNameInput"},'value'),
              prevent_initial_call=True)
def SaveConfig(n_clicks,UIs,selection,inputval):
    if n_clicks is None:
        raise PreventUpdate
    else:
        if selection != None:
            FieldName = selection
        else:
            FieldName = inputval
        ConfigDF = pd.Series(index=["FieldUI","PreviousUI","CurrentUI","FollowingUI","FieldVal","PreviousVal","CurrentVal","FollowingVal"],dtype=object)
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
    inputDF = uic.makeDataSeries(dash.callback_context.inputs_list,values)
    for v in inputDF.index:
        if inputDF[v] != None:
            uic.updateConfig([v],[inputDF[v]],"Field_Config.pkl")
    return list(inputDF.values)

#Validate config callback to activate "Update NBalance" button for running the model
@app.callback(Output("RefreshButtonRow",'children'),
              Input({"pos":ALL,"Group":ALL,"subGroup":ALL,"RetType":"value","id":ALL},'value'), 
              Input({"pos":ALL,"Group":ALL,"subGroup":ALL,"RetType":"date","id":ALL},'date'),
              Input({"Group":ALL,"subGroup":ALL,"RetType":"value","id":ALL},'value'), 
              prevent_initial_call=True)
def checkConfigAndEnableUpdate(values,dates,field):
    return uic.validateConfigs()

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
        FieldConfig = pd.read_pickle("Field_Config.pkl")
        Tt = cnbf.CalculateMedianTt(PreviousConfig["EstablishDate"].astype(dt.datetime),FollowingConfig["HarvestDate"].astype(dt.datetime),metFiles[FieldConfig["Location"]])
        PreviousCropN, PreviousCropWater, PreviousNComponentColors = CalculateCropOutputs(Tt[PreviousConfig["EstablishDate"]:PreviousConfig["HarvestDate"]],
                                                                                               PreviousConfig,CropCoefficients)
        CurrentCropN, CurrentCropWater, CurrentNComponentColors = CalculateCropOutputs(Tt[CurrentConfig["EstablishDate"]:CurrentConfig["HarvestDate"]],
                                                                                               CurrentConfig,CropCoefficients)
        FollowingCropN, FollowingCropWater, FollowingNComponentColors = CalculateCropOutputs(Tt[FollowingConfig["EstablishDate"]:FollowingConfig["HarvestDate"]],
                                                                                               FollowingConfig,CropCoefficients)
        BiomassComponents = ['Root','+ Stover','+ FieldLoss','+ DressingLoss','TotalCrop']
        CropN = pd.DataFrame(index = pd.MultiIndex.from_product([BiomassComponents,Tt.index],
                                                                names=['Component','Date']),columns=['Values'])
        CropN.update(PreviousCropN)
        CropN.update(CurrentCropN)
        CropN.update(FollowingCropN)
        return CropNGraph(CropN, FollowingNComponentColors)

SavedConfigFiles = []
mydir = 'C:\GitHubRepos\SVS'
for File in os.listdir(mydir):
    if File.endswith('.pkl'):
        if ('_SavedConfig' in File):
            SavedConfigFiles.append(File.replace('_SavedConfig.pkl',''))
            
app.layout = html.Div([
                dbc.Row([
                    dbc.Col([dbc.Row(dbc.Card(uic.CropInputs('Previous_',EndUseCatagoriesDropdown,False,'Select Planting Date','Set Planting Date first')),
                                     id={"Group":"UI","id":"PreviousConfigUI"}),
                             dbc.Row(dbc.Card(uic.CropInputs('Current_',EndUseCatagoriesDropdown,True, 'Set Prior Crop dates first','Set Prior Crop dates first')),
                                     id={"Group":"UI","id":"CurrentConfigUI"}),
                             dbc.Row(dbc.Card(uic.CropInputs('Following_',EndUseCatagoriesDropdown,True, 'Set Prior Crop dates first','Set Prior Crop dates first')),
                                     id={"Group":"UI","id":"FollowingConfigUI"})
                            ]),
                    dbc.Col([dbc.Row(html.H1("Field Name", id="FNtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(dcc.Dropdown(options = SavedConfigFiles, placeholder='Select saved field', id={"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNamePicker"})),
                             dbc.Row(dcc.Input(type="text",debounce=True, placeholder='or type new field name',min=0,id={"Group":"Field","subGroup":"Place","RetType":"value","id":"FieldNameInput"})),
                             dbc.Row(html.Button("Load Config", disabled=True, id="LoadButton"),
                                     id={"Group":"Field","subGroup":"FileButton","RetType":"children","id":"LoadButton"}),
                             dbc.Row(html.Div("Last Load", id="LLtext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Row(html.Button("Save Config",disabled=True,id="SaveButton"),
                                     id={"Group":"Field","subGroup":"FileButton","RetType":"children","id":"SaveButton"}),
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
pd.read_pickle('Previous_Config.pkl').isnull().sum()

pd.read_pickle('Current_Config.pkl').isnull().sum()

pd.read_pickle('Following_Config.pkl')

pd.read_pickle('Field_Config.pkl')
