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

PreviousConfig

fig = go.Figure()
weighting = [.95,.5,.05]
align = ['left','center','right']
pos = 0
for p in uic.Positions:
    c = pd.read_pickle(p+'Config.pkl')
    fig.add_trace(go.Scatter(x=[c['EstablishDate']]*2,y=[0,1000],line = {'color':'grey','dash':'dash'},mode='lines',showlegend=False))
    fig.add_trace(go.Scatter(x=[c['HarvestDate']]*2,y=[0,1000],line = {'color':'grey','dash':'dash'},mode='lines',showlegend=False))
    fig.add_annotation(dict(x= c['HarvestDate'], y= 1000, xref="x", yref="y",text="",showarrow=True,
                            ax= c['EstablishDate'], ay= 1000, axref = "x", ayref='y', arrowhead = 3, arrowwidth=1.5, arrowcolor='grey',))
    fig.add_annotation(dict(ax= c['HarvestDate'], y= 1000, xref="x", yref="y",text="",showarrow=True,
                            x= c['EstablishDate'], ay= 1000, axref = "x", ayref='y', arrowhead = 3, arrowwidth=1.5, arrowcolor='grey',))
    middate = c['EstablishDate'].astype(dt.datetime) + (c['HarvestDate'].astype(dt.datetime)-c['EstablishDate'].astype(dt.datetime))*weighting[pos]
    fig.add_trace(go.Scatter(x=[middate], y = [1000], text = p[:-1] + ' Crop <br>'+ c['Crop'], mode="lines+text",showlegend=False,textposition='middle '+align[pos]))
    pos +=1
fig


# +
def AddTimeLines(fig,ypos,start):
    weighting = [.99,.5,.05]
    align = ['left','center','right']
    pos = 0
    for p in uic.Positions:
        c = pd.read_pickle(p+'Config.pkl')
        fig.add_trace(go.Scatter(x=[c['EstablishDate']]*2,y=[0,10000],line = {'color':'grey','dash':'dash'},mode='lines',showlegend=False))
        fig.add_trace(go.Scatter(x=[c['HarvestDate']]*2,y=[0,10000],line = {'color':'grey','dash':'dash'},mode='lines',showlegend=False))
        if pos != 0:
            fig.add_annotation(dict(ax= c['HarvestDate'], y= ypos, xref="x", yref="y",text="",showarrow=True,
                                x= c['EstablishDate'], ay= ypos, axref = "x", ayref='y', arrowhead = 3, arrowwidth=1.5, arrowcolor='grey',))
            fig.add_annotation(dict(x= c['HarvestDate'], y= ypos, xref="x", yref="y",text="",showarrow=True,
                                ax= c['EstablishDate'], ay= ypos, axref = "x", ayref='y', arrowhead = 3, arrowwidth=1.5, arrowcolor='grey',))
        else:
            fig.add_annotation(dict(ax= start, y= ypos, xref="x", yref="y",text="",showarrow=True,
                                x= c['HarvestDate'], ay= ypos, axref = "x", ayref='y', arrowhead = 3, arrowwidth=1.5, arrowcolor='grey',))
            
        middate = c['EstablishDate'].astype(dt.datetime) + (c['HarvestDate'].astype(dt.datetime)-c['EstablishDate'].astype(dt.datetime))*weighting[pos]
        fig.add_trace(go.Scatter(x=[middate], y = [ypos], text = p[:-1] + ' Crop <br>'+ c['Crop'], mode="lines+text",showlegend=False,textposition='middle '+align[pos]))
        pos +=1
    return fig

def CropNGraph(NBalance,start,end):
    cols = ['brown','orange','red','blue','green']
    fig = go.Figure()
    hdates = []
    pdates = []
    for c in uic.Positions:
        config = pd.read_pickle(c+"Config.pkl")
        hdates.append(config['HarvestDate'])
        pdates.append(config['HarvestDate'].astype(dt.datetime)+dt.timedelta(days=15))
    base = [0,0,0]
    pos=0
    for c in ['Root','Stover','FieldLoss','DressingLoss','SaleableProduct']:
        data = NBalance.loc[hdates,c]
        fig.add_trace(go.Bar(x =  pdates, y = data, base = base, offsetgroup=0, name=c, text=c,width=86400000*30,marker={'color':cols[pos]}))
        base = np.add(base,data)
        pos+=1
    data = [0]* len(NBalance.index)
    for c in ['Root','Stover','FieldLoss','DressingLoss','SaleableProduct']:
        data = np.add(data,NBalance.loc[:,c])
    data = data.where(data > 0, np.nan)
    fig.add_trace(go.Scatter(x=NBalance.index,y=data,name='Crop N',line = {'color':'green'},connectgaps=False))
    
    #fig.add_trace(go.Bar(x =  [], y = []*6, offsetgroup=0, name=c, text=c,width=86400000*30,marker={'color':cols[pos]}))
    
    ypos = data.max()*1.1
    fig = AddTimeLines(fig,ypos,start)
    fig.update_layout(title_text="Crop N", title_font_size = 30, title_x = 0.5, title_xanchor = 'center')
    fig.update_yaxes(title_text="Nitrogen (kg/ha)", title_font_size = 20, range=[0,ypos*1.1])
    fig.update_xaxes(title_text=None,range= [start,end])
    fig.update_layout(legend_traceorder="reversed")
    return fig

def CropWaterGraph(cropWater):
    NData = cropWater.reset_index()
    fig = px.line(data_frame=NData,x='Date',y='Values',color='Component',color_discrete_sequence=['brown','orange','red','green'],
                 )#range_x = [c['EstablishDate']-dt.timedelta(days=7),c['HarvestDate']+dt.timedelta(days=7)])
    fig.update_layout(title_text="Cover and Root Depth", title_font_size = 30, title_x = 0.5, title_xanchor = 'center')
    fig.update_yaxes(title_text="Cover (m2/m2) and depth (m)", title_font_size = 20)
    fig.update_xaxes(title_text=None)
    return fig

def NInputsGraph(NBalance):
    NInputs = NBalance.loc[:,['SOMNmineraliation','ResidueMineralisation']].cumsum()
    NInputs.columns.name='Components'
    NInputs = NInputs.unstack().reset_index()
    fig = px.line(data_frame=NInputs,x='Date',y=0,color='Components',
                 )#range_x = [c['EstablishDate']-dt.timedelta(days=7),c['HarvestDate']+dt.timedelta(days=7)])
    fig.update_layout(title_text="N Inputs", title_font_size = 30, title_x = 0.5, title_xanchor = 'center')
    fig.update_yaxes(title_text="Nitrogen (kg/ha)", title_font_size = 20)
    fig.update_xaxes(title_text=None)
    
    return fig

def SoilNGraph(NBalance,start,end):
    SoilN = NBalance.loc[:,['SoilMineralN']]
    SoilN.columns.name='Components'
    SoilN = SoilN.unstack().reset_index()
    fig = px.line(data_frame=
                  SoilN,x='Date',y=0,color='Components',
                 )
    #print(SoilN)
    ypos = SoilN.loc[:,0].max()*1.1
    fig = AddTimeLines(fig,ypos,start)
    fig.update_xaxes(range= [start,end],title_text=None)
    fig.update_yaxes(title_text="Nitrogen (kg/ha)", title_font_size = 20,range = [0,ypos*1.1])
    fig.update_layout(title_text="SoilN", title_font_size = 30, title_x = 0.5, title_xanchor = 'center')
    
    return fig


# -

CropNGraph(NBalance,start,end)

SoilNGraph(NBalance,start,end)

PreviousConfig = pd.read_pickle("Previous_Config.pkl")
CurrentConfig = pd.read_pickle("Current_Config.pkl")
FollowingConfig = pd.read_pickle("Following_Config.pkl")
FieldConfig = pd.read_pickle("Field_Config.pkl")
Tt = CalculateMedianTt(PreviousConfig["EstablishDate"].astype(dt.datetime),FollowingConfig["HarvestDate"].astype(dt.datetime),metFiles[FieldConfig["Location"]])
NBalance = MakeNBalanceFrame(Tt.index)
NBalance = CalculateCropOutputs(Tt,CropCoefficients,NBalance)
NBalance = CalculateSOMMineralisation(Tt, NBalance)
NBalance = CalculateResidueMineralisation(Tt,NBalance)
NBalance = CalculateSoilMineralN(NBalance)
start = PreviousConfig['HarvestDate'].astype(dt.datetime)-dt.timedelta(30)
end = FollowingConfig['HarvestDate'].astype(dt.datetime)+dt.timedelta(30)
        

ConfigFiles = []
mydir = 'C:\GitHubRepos\SVS'
for File in os.listdir(mydir):
    if File.endswith('.pkl'):
        if ('_SavedConfig' in File):
            ConfigFiles.append(File.replace('_SavedConfig.pkl',''))


def MakeNBalanceFrame(index):
    columns = ['Root', 'Stover', 'FieldLoss', 'DressingLoss','SaleableProduct', 'TotalCrop', 'Cover','RootDepth', 'SOMNmineraliation', 'PresRoot', 'PresStover', 'PresFeildLoss', 'CresRoot', 'CresStover', 'CresFeildLoss', 'ResidueMineralisation', 'LeachingLoss', 'GasiousLoss', 'SoilMineralN','UnMeasuredSoilN']
    return pd.DataFrame(index = index, columns = columns, data= 0.0)


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
            TT.loc[:,y] = Met.loc[start:,'tt'].values[:duration]
        except:
            do = 'nothing'
    TTmed = TT.median(axis=1)
    TTmed.index = pd.date_range(start=Start,periods=duration,freq='D',name='Date')
    TTmed.name = 'Tt'
    return TTmed

def calcDelta(Integral):
    prior = Integral[0]
    delta = []
    for i in Integral:
        delta.append(i-prior)
        prior = i
    return delta

def CalculateCropOutputs(AllTt, CropCoefficients, NBalance):
    NBalance.loc[:,'CropUptake'] = 0
    for pos in  uic.Positions:
        Config = pd.read_pickle(pos+'Config.pkl')
        CropFilter = (CropCoefficients.loc[:,'EndUse'] == Config["EndUse"])&(CropCoefficients.loc[:,'Group'] == Config["Group"])\
                     &(CropCoefficients.loc[:,'Colloquial Name'] == Config["Crop"])&(CropCoefficients.loc[:,'Type'] == Config["Type"])
        Params = pd.Series(index=CropCoefficients.loc[CropFilter,uic.CropParams].columns, data = CropCoefficients.loc[CropFilter,uic.CropParams].values[0])
        ## Calculate model parameters 
        
        Tt = AllTt[Config['EstablishDate']:Config['HarvestDate']].cumsum()
        Tt_Harv = Tt[Config['HarvestDate']] 
        Tt_estab = Tt_Harv * (StagePropns.loc[Config['EstablishStage'],'PrpnTt']/StagePropns.loc[Config['HarvestStage'],'PrpnTt'])
        CropTt = Tt+Tt_estab #Create array of Tt accumulations during crop duration.
        Xo_Biomass = (Tt_Harv + Tt_estab) *.45 * (1/StagePropns.loc[Config["HarvestStage"],'PrpnTt'])
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
        if ((Config["SaleableYield"] * Config['Units']) <(Params['Typical Yield']*0.05)) or (Config["FieldLoss"]>95):
            Config["SaleableYield"] = Params['Typical Yield']
            Config["FieldLoss"] = 100
            FreshTotalProductWt = Params['Typical Yield'] * (1/(1-Params['Typical Dressing Loss %']/100))
        else:
            FreshTotalProductWt = Config["SaleableYield"] * (1/(1-Config["FieldLoss"]/100)) * (1/(1-Config["DressingLoss"]/100))
        DryTotalProductWt = FreshTotalProductWt * Config['Units'] * (1-Config["MoistureContent"]/100)
        DryFieldLossWt = DryTotalProductWt * Config["FieldLoss"]/100
        FieldLossN = DryFieldLossWt * Params['Product [N]']/100
        DryDressingLossWt = DryTotalProductWt * Config["DressingLoss"]/100
        DressingLossN = DryDressingLossWt * Params['Product [N]']/100
        DrySaleableProductWt = DryTotalProductWt - DryFieldLossWt - DryDressingLossWt
        SaleableProductN = DrySaleableProductWt * Params['Product [N]']/100
        HI = a_harvestIndex + FreshTotalProductWt * b_harvestIndex
        DryStoverWt = DryTotalProductWt * 1/HI - DryTotalProductWt 
        StoverN = DryStoverWt * Params['Stover [N]']/100
        DryRootWt = (DryStoverWt+DryTotalProductWt) * Params['P Root']
        RootN = DryRootWt * Params['Root [N]']/100
        CropN = RootN + StoverN + FieldLossN + DressingLossN + SaleableProductN
        dates = Tt[Config['EstablishDate']:Config['HarvestDate']].index
        StageCorrection = 1/(StagePropns.loc[Config["HarvestStage"],'PrpnMaxDM'])
        NBalance.loc[Tt[dates].index,'Root']  = np.multiply(np.multiply(BiomassScaller , RootN),  StageCorrection)
        NBalance.loc[Tt[dates].index,'Stover'] = np.multiply(np.multiply(BiomassScaller , StoverN), StageCorrection)
        NBalance.loc[Tt[dates].index,'SaleableProduct'] = np.multiply(np.multiply(BiomassScaller , SaleableProductN), StageCorrection)
        NBalance.loc[Tt[dates].index,'FieldLoss'] = np.multiply(np.multiply(BiomassScaller , FieldLossN), StageCorrection)
        NBalance.loc[Tt[dates].index,'DressingLoss'] = np.multiply(np.multiply(BiomassScaller , DressingLossN), StageCorrection)
        NBalance.loc[Tt[dates].index,'TotalCrop'] = np.multiply(np.multiply(BiomassScaller , CropN),StageCorrection)
        NBalance.loc[Tt[dates].index,'CropUptake'] = calcDelta(NBalance.loc[Tt[dates].index,'TotalCrop'])
        NBalance.loc[Tt[dates].index,'Cover'] = np.multiply(CoverScaller, Params["A cover"])
        NBalance.loc[Tt[dates].index,'RootDepth'] = np.multiply(RootDepthScaller, Params["Max RD"])
        # if len(c["DefoliationDates"])>0:
        #     CropN.sort_index(inplace=True)
        #     for dd in Config["DefoliationDates"]:
        #         StoverNtoRemove = (CropN.loc[('+ Stover',dd),'Values'].values[0] - CropN.loc[('Root',dd),'Values'].values[0]) * 0.7
        #         TotalNtoRemove = StoverNtoRemove
        #         if Params['Yield type'] == 'Standing DM':
        #             StoverNtoRemove=0
        #             TotalNtoRemove = (CropN.loc[('TotalCrop',dd),'Values'].values[0] - CropN.loc[('Root',dd),'Values'].values[0]) * 0.7
        #         DefCovFact = 0.3
        #         for d in Tt[dates][dd:].index:
        #             CropN.loc[('+ Stover',d),'Values'] = CropN.loc[('+ Stover',d),'Values'] - StoverNtoRemove 
        #             CropN.loc[('TotalCrop',d),'Values'] = CropN.loc[('TotalCrop',d),'Values'] - TotalNtoRemove
        #             CropWater.loc[('Cover',d),'Values'] = CropWater.loc[('Cover',d),'Values'] * DefCovFact
        #             DefCovFact = min(1.0,DefCovFact + Tt[d] * 0.00001)
    return NBalance

def CalculateResidueMineralisation(Tt, NBalance):
    PreviousConfig = pd.read_pickle("Previous_Config.pkl")
    CurrentConfig = pd.read_pickle("Current_Config.pkl")
    FollowingConfig = pd.read_pickle("Following_Config.pkl")
    for d in Tt.index[:-1]:
        if d == PreviousConfig['HarvestDate']:
            NBalance.loc[d,'PresRoot'] = NBalance.loc[d,'Root']
            NBalance.loc[d,'PresStover'] = NBalance.loc[d,'Stover'] * PreviousConfig["ResidueTreatment"]
            NBalance.loc[d,'PresFeildLoss'] = NBalance.loc[d,'FieldLoss'] 
        if d == CurrentConfig['HarvestDate']:
            NBalance.loc[d,'CresRoot'] = NBalance.loc[d,'Root']
            NBalance.loc[d,'CresStover'] = NBalance.loc[d,'Stover'] * CurrentConfig["ResidueTreatment"]
            NBalance.loc[d,'CresFeildLoss'] = NBalance.loc[d,'FieldLoss']
        
        for pool in ['PresRoot', 'PresStover', 'PresFeildLoss', 'CresRoot', 'CresStover', 'CresFeildLoss']:
            tomorrow = d + dt.timedelta(1)
            mineralisation = NBalance.loc[d,pool] * 0.002 * Tt[d]
            NBalance.loc[d,'ResidueMineralisation'] += mineralisation
            NBalance.loc[tomorrow,pool] = NBalance.loc[d,pool] - mineralisation
    return NBalance  

def CalculateSOMMineralisation(Tt, NBalance):
    FieldConfig = pd.read_pickle("Field_Config.pkl")
    for d in Tt.index[1:]:
        NBalance.loc[d,'SOMNmineraliation'] =  FieldConfig['HWEON'] * Tt[d] * 0.005
    return NBalance

def CalculateSoilMineralN(NBalance):
    PreviousConfig = pd.read_pickle("Previous_Config.pkl")
    CurrentConfig = pd.read_pickle("Current_Config.pkl")
    FollowingConfig = pd.read_pickle("Following_Config.pkl")
    FieldConfig = pd.read_pickle('Field_Config.pkl')
    
    dbfh = np.datetime64(PreviousConfig['HarvestDate'].astype(dt.datetime)  - dt.timedelta(1))
    NBalance.loc[dbfh,'UnMeasuredSoilN'] = 100
    for d in NBalance.loc[PreviousConfig['HarvestDate']:,:].index:
        yesterday = d - dt.timedelta(1)
        NBalance.loc[d, 'UnMeasuredSoilN'] = NBalance.loc[yesterday, 'UnMeasuredSoilN'] -\
                                             NBalance.loc[d,'CropUptake'] +\
                                             NBalance.loc[d,['SOMNmineraliation','ResidueMineralisation']].sum()
    Adjustment = NBalance.loc[FieldConfig['MinNDate'], 'UnMeasuredSoilN'] - FieldConfig['MinN']
    NBalance.loc[:,'SoilMineralN'] = NBalance.loc[:,'UnMeasuredSoilN'] - Adjustment
    
    
#     FinalN = 30
#     Eff = 0.8
#     splits = 3
#     duration = (CurrentConfig['HarvestDate']-CurrentConfig['EstablishDate']).days
#     InCropMineralisation = CurrentConfig[['RootN',"StoverN","FieldLossN","SOMN"]].sum()
#     NFertReq = (CurrentConfig["CropN"] + FinalN) - FieldConfig["MineralN"] - InCropMineralisation
#     NFertReq = NFertReq * 1/Eff
#     NFertReq = np.ceil(NFertReq)
#     print(NFertReq)
#     NAppn = NFertReq/splits
#     plength = duration/(splits + 1)
#     xlocs = [0]
#     plength = np.ceil(duration/(splits + 1))
#     xlocs = []
#     for x in range(1,int(splits+1)):
#         xlocs.append(x * plength)
#     FertApplied = 0
#     FertAppNo = 0
#     maxSoilN = max(FieldConfig["MineralN"],FinalN + NAppn)
#     SoilN[CurrentConfig['EstablishDate']] = FieldConfig["MineralN"]
#     for d in SoilN[CurrentConfig['EstablishDate']:].index[1:]:
#         yesterday = d - dt.timedelta(days=1)
#         CropNd = np.nan_to_num(CropN.loc['TotalCrop','Values'].diff()[d],0)
#         SoilN[d] = SoilN[yesterday] + DeltaResidueN[d] + DeltaSOMN[d] - CropNd 
#         if (SoilN[yesterday] > SoilN[d]) and (SoilN[d] < FinalN) and (FertApplied < NFertReq): #and ((CropPatterns.iloc[d-1,4]-CropPatterns.iloc[d,4])<0):
#             SoilN[d] += NAppn * Eff
#             FertApplied += NAppn
    return NBalance
# -

# ## App layout and callbacks

# +
# Empty the config files
FieldConfigs = ['FieldNameInput','Location','HWEON','MinN','MinNDate']
FieldConfig = pd.Series(index = FieldConfigs, data = [""]+[None]*4)
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
              Output({"Group":"Field","subGroup":ALL,"RetType":"date","id":ALL},'date'),
              Input({"Group":"Field","subGroup":ALL,"RetType":"value","id":ALL},'value'),
              Input({"Group":"Field","subGroup":ALL,"RetType":"date","id":ALL},'date'),
              prevent_initial_call=True)
def setInputValue(values,date):
    inputDF = uic.makeDataSeries(dash.callback_context.inputs_list[:-1],values)
    for v in inputDF.index:
        if inputDF[v] != None:
            uic.updateConfig([v],[inputDF[v]],"Field_Config.pkl")
    uic.updateConfig(['MinNDate'],[np.datetime64(date[0])],"Field_Config.pkl")    
    return values,date

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
    Output('MineralNGraph','figure'),
    Output('NInputsGraph','figure'),
    Input('RefreshButton','n_clicks'), prevent_initial_call=True)
def RefreshGraphs(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    else:
        PreviousConfig = pd.read_pickle("Previous_Config.pkl")
        CurrentConfig = pd.read_pickle("Current_Config.pkl")
        FollowingConfig = pd.read_pickle("Following_Config.pkl")
        FieldConfig = pd.read_pickle("Field_Config.pkl")
        start = PreviousConfig['HarvestDate'].astype(dt.datetime)-dt.timedelta(30)
        end = FollowingConfig['HarvestDate'].astype(dt.datetime)+dt.timedelta(30)
        Tt = CalculateMedianTt(PreviousConfig["EstablishDate"].astype(dt.datetime),FollowingConfig["HarvestDate"].astype(dt.datetime),metFiles[FieldConfig["Location"]])
        NBalance = MakeNBalanceFrame(Tt.index)
        NBalance = CalculateCropOutputs(Tt,CropCoefficients,NBalance)
        NBalance = CalculateSOMMineralisation(Tt,NBalance)
        NBalance = CalculateResidueMineralisation(Tt,NBalance)
        NBalance = CalculateSoilMineralN(NBalance)
        return CropNGraph(NBalance,start,end), SoilNGraph(NBalance,start,end), NInputsGraph(NBalance)

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
                             dbc.Row(html.Div("MinN test date", id="MinDatetext",style=dict(display='flex', justifyContent='right'))),
                             dbc.Col([dcc.DatePickerSingle(id={"Group":"Field","subGroup":"Soil","RetType":"date","id":"MinNDate"}, min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2025, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            placeholder = 'Select date',display_format='D-MMM-YYYY')], 
                                     id={"Group":"Field","subGroup":"Soil","RetType":"children","id":"MinNDate"}, width=2, align='center'), 
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
for pos in uic.Positions+['field_']:
    Config=pd.read_pickle(pos+"Config.pkl")
    print(Config.isnull().sum())

FieldConfig = pd.read_pickle("Field_Config.pkl")
FieldConfig

PreviousConfig = pd.read_pickle("Previous_Config.pkl")
CurrentConfig = pd.read_pickle("Current_Config.pkl")
FollowingConfig = pd.read_pickle("Following_Config.pkl")
FieldConfig = pd.read_pickle("Field_Config.pkl")
Tt = CalculateMedianTt(PreviousConfig["EstablishDate"].astype(dt.datetime),FollowingConfig["HarvestDate"].astype(dt.datetime),metFiles[FieldConfig["Location"]])
NBalance = MakeNBalanceFrame(Tt.index)
NBalance = CalculateCropOutputs(Tt,CropCoefficients,NBalance)
NBalance = CalculateSOMMineralisation(Tt, NBalance)
NBalance = CalculateResidueMineralisation(Tt,NBalance)
NBalance = CalculateSoilMineralN(NBalance)

NBalance.loc[:,'UnMeasuredSoilN'].plot()

NBalance.loc[:,'CropUptake'].plot()

NBalance.loc[PreviousConfig['HarvestDate']:,:]#['SoilMineralN','UnMeasuredSoilN']]

NBalance.loc[np.datetime64(PreviousConfig['HarvestDate'].astype(dt.datetime) - dt.timedelta(1)),:]

NBalance.index[248]

NBalance.Root.plot()

Tt

CropN.loc[CropN.Components=='Root',0]#.plot()

pd.read_pickle('Previous_Config.pkl')

pd.read_pickle('Current_Config.pkl')

pd.read_pickle('Following_Config.pkl')

pd.read_pickle('Field_Config.pkl')

help(dash.dcc.Dropdown)
