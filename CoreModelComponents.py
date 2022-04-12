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
import ast
import CropNBalUICompenents as uic

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

