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
import ETFunctions
import matplotlib.dates as mdates
import GraphHelpers as GH
from bisect import bisect_left, bisect_right
from jupyter_dash import JupyterDash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
# %matplotlib inline

# +
# Data extracted from CropData.cs InitialiseCropData() method
CropCoefficients = pd.read_excel('C:\\GitHubRepos\\Overseer-testing\\CropCoefficients\\CropCoefficients.xlsx')
CropCoefficients.set_index(['CropName'],inplace=True)
Categories = CropCoefficients.Category.drop_duplicates().values
CatFilt = (CropCoefficients.loc[:,'Category'] != 'Undefined') & (CropCoefficients.loc[:,'Category'] != 'Pasture')
CropCoefficients = CropCoefficients.loc[CatFilt,:]
CropDropDown = [{'label':i,'value':i} for i in CropCoefficients.index]

LincolnMet = pd.read_csv('C:\GitHubRepos\Weather\Broadfields\LincolnClean.met',delimiter = '\t')
LincolnMet.name = 'Lincoln'
GoreMet = pd.read_csv('C:\GitHubRepos\Weather\OtherLocations\GoreClean.met',delimiter = '\t')
GoreMet.name = 'Gore'
WhatatuMet = pd.read_csv('C:\GitHubRepos\Weather\OtherLocations\WhatatuClean.met',delimiter = '\t')
WhatatuMet.name = 'Napier'
PukekoheMet = pd.read_csv('C:\GitHubRepos\Weather\OtherLocations\PukekoheClean.met',delimiter = '\t')
PukekoheMet.name = 'Pukekohe'

metFiles ={'Pukekohe':PukekoheMet,'Whatatu':WhatatuMet,'Lincoln':LincolnMet,'Gore':GoreMet}

def tt(x,b):
    return max(0,x-b)

for f in metFiles.keys():
    metFiles[f].loc[:,'Date'] = pd.to_datetime(metFiles[f].loc[:,'Date'])
    metFiles[f].loc[:,'tt'] = [tt(x,5) for x in metFiles[f].Temp]
    
    metFiles[f].set_index('Date',inplace=True)

    MetDropDown = [{'label':i,'value':i} for i in metFiles.keys()]

Units = pd.DataFrame(index = ['t/ha','kg/ha'],data=[1000,1],columns=['toKG/ha'])
UnitsDropDown = [{'label':i,'value':i} for i in Units.index]

ResidueTreatments = pd.DataFrame(index = ['Incorporated','Left on Surface','Baled','Garzed','Burnt'],
                                 data = [0,0,80,50,90],
                                 columns = ['%returned'])
ResidueTreatmentsDropdown = [{'label':i,'value':i} for i in ResidueTreatments.index]

CropConfigs = ["Crop","SaleableYield","Units","FieldLoss","DressingLoss","MoistureContent",
               "EstablishDate","EstablishStage","HarvestDate","HarvestStage","ResidueTreatment"]

def setCropConfigDefaults(data):
     return pd.Series(index = CropConfigs,data = data)
                                 
PriorConfig = setCropConfigDefaults(["Wheatautumn",16000,"kg/ha",5,0,0,dt.datetime.strptime('01-04-2020','%d-%m-%Y'),
                                         "Seed",dt.datetime.strptime('1-10-2020','%d-%m-%Y'),"EarlyReproductive","Incorporated"])
CurrentConfig = setCropConfigDefaults(["Potatolong",70,"t/ha",10,5,77,dt.datetime.strptime('15-10-2020','%d-%m-%Y'),
                                         "Seed",dt.datetime.strptime('10-3-2021','%d-%m-%Y'),"Maturity","Incorporated"])
FollowingConfig = setCropConfigDefaults(["Wheatautumn",12,"t/ha",5,5,15,dt.datetime.strptime('01-04-2021','%d-%m-%Y'),
                                         "Seed",dt.datetime.strptime('10-2-2022','%d-%m-%Y'),"Maturity","Incorporated"])
# -

CropConfigDefaults["Crop"]

# +
BiomassScaller = []
Covers = []
Xo_Biomass = 50
b_Biomass = Xo_Biomass*0.2
A_cov = 1
T_mat = Xo_Biomass*2
T_sen = T_mat-30
Xo_cov = T_mat * 0.25
b_cov = Xo_cov * 0.2
Tts = range(150)
for tt in Tts:
    BiomassScaller.append(1/(1+np.exp(-((tt-Xo_Biomass)/(b_Biomass)))))
    cover = 0
    if tt < T_sen:
        cover = A_cov * 1/(1+np.exp(-((tt-Xo_cov)/b_cov)))
    else:
        if tt < T_mat:
            cover = A_cov * (1-(tt-T_sen)/(T_mat-T_sen))
    Covers.append(cover)
DMscaller = pd.DataFrame(index=Tts,data=BiomassScaller,columns=['scaller'])
DMscaller.loc[:,'cover'] = Covers
print(DMscaller.loc[99,'scaller'])
plt.plot(DMscaller.loc[:,'scaller'])
plt.plot(DMscaller.loc[:,'cover'])
DMscaller.loc[:,'max'] = DMscaller.max(axis=1)

Methods = ['Seed','Seedling','Vegetative','EarlyReproductive','LateReproductive','Maturity','Late']
PrpnMaxDM = [0.0066,0.03,0.5,0.75,0.95,0.9933,0.9995]
StagePropns = pd.DataFrame(index = Methods, data = PrpnMaxDM,columns=['PrpnMaxDM']) 
for p in StagePropns.index:
    TTatProp = bisect_left(DMscaller.scaller,StagePropns.loc[p,'PrpnMaxDM'])
    StagePropns.loc[p,'PrpnTt'] = TTatProp/T_mat
    plt.plot(StagePropns.loc[p,'PrpnTt']*T_mat,StagePropns.loc[p,'PrpnMaxDM'],'o',color='k')
    plt.text(StagePropns.loc[p,'PrpnTt']*T_mat+3,StagePropns.loc[p,'PrpnMaxDM'],p,verticalalignment='top')
    plt.plot([StagePropns.loc[p,'PrpnTt']*T_mat]*2,[0,DMscaller.loc[round(StagePropns.loc[p,'PrpnTt'] * T_mat),'max']],'--',color='k',lw=1)
plt.ylabel('Relative DM accumulation')
plt.xlabel('Temperature accumulation')
EstablishStageDropdown = [{'label':i,'value':i} for i in Methods[:2]]
HarvestStageDropdown = [{'label':i,'value':i} for i in Methods[2:]]


# +
def CalcCovers(Tts, A_cov, Xo_cov, b_cov,T_sen,T_mat):
    Covers = []
    for tt in Tts:
        cover = 0
        if tt < T_sen:
            cover = A_cov * 1/(1+np.exp(-((tt-Xo_cov)/b_cov)))
        else:
            if tt < T_mat:
                cover = A_cov * (1-(tt-T_sen)/(T_mat-T_sen))
        Covers.append(cover)
    return Covers

def CalcBiomass(Tts,Xo_Biomass,b_Biomass):
    BiomassScaller = []
    for tt in Tts:
        BiomassScaller.append(1/(1+np.exp(-((tt-Xo_Biomass)/(b_Biomass)))))
    return BiomassScaller    

def NDilution(An,Bn,c,R):
    return An * (1 + Bn * np.exp(c*R))

def MakeDate(DateString,CheckDate):
    Date = dt.datetime(2000,int(dt.datetime.strptime(DateString.split('-')[1],'%b').month),int(DateString.split('-')[0]))
    if CheckDate == '':
        CheckDate = dt.datetime(2000,1,1)
    if Date < CheckDate:
        Date = dt.datetime(2001,int(dt.datetime.strptime(DateString.split('-')[1],'%b').month),int(DateString.split('-')[0]))
    return Date



def firstIndex(series,threshold):
    pos=0
    passed = False
    while passed == False:
        if series.iloc[pos] < threshold:
            passed = True
        pos +=1
    return pos

def DeriveMedianTt(Loc,StartDate,EndDate):
    ## Calculate median thermaltime for location
    duration = (EndDate-StartDate).days
    Met = metFiles[Loc]
    FirstYear = int(Met.Year[0])
    years = [x for x in Met.Year.drop_duplicates().values[1:-1]]
    day = StartDate.day
    month = StartDate.month
    FirstDate = dt.date(FirstYear,month,day)
    TT = pd.DataFrame(columns = years,index = range(1,duration+1))
    for y in years:
        start = str(StartDate.day) + '-' + str(StartDate.month) + '-' + str(int(y))
        try:
            TT.loc[:,y] = Met.loc[start:,'tt'].cumsum().values[:duration]
        except:
            do = 'nothing'
    TTmed = (TT.median(axis=1))/30 # (TT.median(axis=1)-[5*x for x in TT.index])/30
    TTmed.index = pd.date_range(start=StartDate,periods=duration,freq='D',name='Date')
    TTmed.name = 'Tt'
    return TTmed

def DeriveCropUptake(TTmed,cropConfigs):
    RootN = pd.DataFrame(index=TTmed.index,columns=['Values'],data=[0]*TTmed.index.size)
    StoverN = pd.DataFrame(index=TTmed.index,columns=['Values'],data=[0]*TTmed.index.size)
    ResidueN = pd.DataFrame(index=TTmed.index,columns=['Values'],data=[0]*TTmed.index.size)
    TotalN = pd.DataFrame(index=TTmed.index,columns=['Values'],data=[0]*TTmed.index.size)
    Root = pd.concat([RootN],axis=0,keys=['Root'],names=['Nitrogen'])
    Stover = pd.concat([StoverN],axis=0,keys=['Stover'],names=['Nitrogen'])
    Residue = pd.concat([ResidueN],axis=0,keys=['Residue'],names=['Nitrogen'])
    Total = pd.concat([TotalN],axis=0,keys=['Total'],names=['Nitrogen'])
    CropN = pd.concat([Root,Stover,Residue,Total],axis=0)
    for c in cropConfigs:
        ## Calculate model parameters 
        EstablishDate = c["EstablishDate"]
        HarvestDate = c["HarvestDate"]
        Crop = c["Crop"] 
        CropTt = TTmed[EstablishDate:HarvestDate] - TTmed[EstablishDate] 
        Tt_Harv = TTmed[HarvestDate] - TTmed[EstablishDate] 
        Tt_estab = Tt_Harv * (StagePropns.loc[c["EstablishStage"],'PrpnTt']/StagePropns.loc[c["HarvestStage"],'PrpnTt'])
        Xo_Biomass = (Tt_Harv + Tt_estab) *.5 * (1/StagePropns.loc[c["HarvestStage"],'PrpnTt'])
        b_Biomass = Xo_Biomass * .2
        # Calculate fitted patterns
        BiomassScaller = []
        for tt in CropTt:
            BiomassScaller.append(1/(1+np.exp(-((tt-Xo_Biomass)/(b_Biomass)))))
        UnitConverter = Units.loc[c["Units"],'toKG/ha']
        FreshProductWt = c["SaleableYield"] * (1 + c["FieldLoss"]/100) * (1 + c["DressingLoss"]/100)
        DryProductWt = FreshProductWt * UnitConverter * (1-c["MoistureContent"]/100)
        HI = CropCoefficients.loc[Crop,'a_Harvest'] + c["SaleableYield"] * UnitConverter * CropCoefficients.loc[Crop,'b_harvest']
        DryStoverWt = DryProductWt * 1/HI - DryProductWt 
        DryRootWt = (DryStoverWt+DryProductWt) * CropCoefficients.loc[Crop,'p_Root']
        TotalProductN = DryProductWt * CropCoefficients.loc[Crop,'Nconc_Tops']/100
        TotalStoverN = DryStoverWt * CropCoefficients.loc[Crop,'Nconc_Stover']/100
        TotalRootN = DryRootWt * CropCoefficients.loc[Crop,'Nconc_Roots']/100
        TotalResidueN = TotalRootN + TotalStoverN + (TotalProductN * c["FieldLoss"]/100)
        TotalCropN = TotalRootN + TotalStoverN + TotalProductN  
        RootN = pd.Series(index=TTmed[EstablishDate:HarvestDate].index,data=np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), TotalRootN))
        StoverN = pd.Series(index=TTmed[EstablishDate:HarvestDate].index,data=np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), TotalRootN+TotalStoverN))
        ResidueN = pd.Series(index=TTmed[EstablishDate:HarvestDate].index,data=np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), TotalResidueN))
        TotalN = pd.Series(index=TTmed[EstablishDate:HarvestDate].index,data=np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[c["HarvestStage"],'PrpnMaxDM'])), TotalCropN))
        for d in TTmed[EstablishDate:HarvestDate].index:
            CropN.loc[('Root',d),'Values'] = RootN[d]
            CropN.loc[('Stover',d),'Values'] = StoverN[d]
            CropN.loc[('Residue',d),'Values'] = ResidueN[d]
            CropN.loc[('Total',d),'Values'] = TotalN[d]
    return CropN.reset_index()
    
def MineralisationGraph(TTmed,EstablishDate,HWEON):
    ## Calculate date variables
    EstabDate = MakeDate(Establish,'')
    HarvestDate = MakeDate(Harvest,EstabDate)
    Tt_Harv = TTmed[HarvestDate]
    Tt_estab = Tt_Harv * (StagePropns.loc[EstablishStage,'PrpnTt']/StagePropns.loc[HarvestStage,'PrpnTt'])
    CropPatterns = pd.DataFrame(TTmed+Tt_estab)
    CropPatterns.loc[:,'biomass'] = CropPatterns.Tt.values * p
    plt.plot(CropPatterns.index,CropPatterns.biomass,color=col)
    #plt.plot(CropPatterns.index,CropPatterns.nitrogen)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.xlim(EstabDate,HarvestDate)
    return CropPatterns.loc[:HarvestDate,'biomass'].max()
    #plt.ylim(0,1.1)

    
def Deficit(ax,Met,Establish,Harvest,EstablishStage,HarvestStage,r,m,InitialN,FinalN,TotalCropN,splits,Eff):
    ## Calculate median thermaltime for location
    FirstYear = int(Met.Year[0])
    years = [int(x) for x in Met.Year.drop_duplicates().values[1:-1]]
    day = int(Establish.split('-')[0])
    month = dt.datetime.strptime(Establish.split('-')[1],'%b').month
    FirstDate = dt.datetime(FirstYear,month,day)

    Met.loc[:,'tt'] = [tt(x,5) for x in Met.Temp]
    TT = pd.DataFrame(columns = years,index = range(1,368))
    for y in years:
        start = Establish + '-' + str(y)
        end = Harvest + '-' + str(y+1)
        duration = (dt.datetime.strptime(end,'%d-%b-%Y') - dt.datetime.strptime(start,'%d-%b-%Y')).days
        try:
            TT.loc[:,y] = Met.loc[start:,'tt'].cumsum().values[:367]
        except:
            do = 'nothing'
    TTmed = (TT.median(axis=1))/30 # (TT.median(axis=1)-[5*x for x in TT.index])/30
    TTmed.index = pd.date_range(start=Establish+'-2000',periods=367,freq='D',name='Date')
    TTmed.name = 'Tt'
    ## Calculate date variables
    EstabDate = MakeDate(Establish,'')
    HarvestDate = MakeDate(Harvest,EstabDate)

    ## Calculate model parameters 
    Tt_Harv = TTmed[HarvestDate]
    Tt_estab = Tt_Harv * (StagePropns.loc[EstablishStage,'PrpnTt']/StagePropns.loc[HarvestStage,'PrpnTt'])
    Xo_Biomass = (Tt_Harv + Tt_estab) *.5 * (1/StagePropns.loc[HarvestStage,'PrpnTt'])
    b_Biomass = Xo_Biomass * .2

    # Calculate fitted patterns
    CropPatterns = pd.DataFrame(TTmed+Tt_estab)
    CropPatterns.loc[:,'biomass'] = CalcBiomass(CropPatterns.Tt.values,Xo_Biomass,b_Biomass) * 1/(StagePropns.loc[HarvestStage,'PrpnMaxDM']) * TotalCropN
    CropPatterns.loc[:,'residue'] = CropPatterns.Tt.values * r
    CropPatterns.loc[:,'mineralisation'] = CropPatterns.Tt.values * m
    CropPatterns.loc[:,'mineral'] = InitialN
    CropPatterns = CropPatterns.iloc[:duration,:]
    NFertReq = (CropPatterns.loc[:,'biomass'].max() + FinalN) - InitialN - CropPatterns.loc[:,'mineralisation'].max() - CropPatterns.loc[:,'residue'].max()
    NFertReq = NFertReq * 1/Eff
    NFertReq = np.ceil(NFertReq)
    NAppn = NFertReq/splits
    plength = duration/(splits + 1)
    xlocs = [0]
    plength = np.ceil(duration/(splits + 1))
    xlocs = []
    for x in range(1,int(splits+1)):
        xlocs.append(x * plength)
    FertApplied = 0
    FertAppNo = 0
    maxSoilN = max(InitialN,FinalN + NAppn)
    for d in range(1,CropPatterns.index.size):
        PotentialN = CropPatterns.iloc[d-1,4]+CropPatterns.iloc[:,2].diff()[d]+CropPatterns.iloc[:,3].diff()[d]-CropPatterns.iloc[:,1].diff()[d] 
        CropPatterns.iloc[d,4] = PotentialN
        if (CropPatterns.iloc[d-1,4] > CropPatterns.iloc[d,4]) and (PotentialN < FinalN) and (FertApplied < NFertReq): #and ((CropPatterns.iloc[d-1,4]-CropPatterns.iloc[d,4])<0):
            CropPatterns.iloc[d,4]  += NAppn * Eff
            FertApplied += NAppn
            plt.plot([CropPatterns.index[d]]*2,[CropPatterns.iloc[d-1,4],CropPatterns.iloc[d,4]],'-',color='k',lw=3)
            recString = CropPatterns.index[d].strftime('%d-%b') +'\n' +str(int(NAppn)) + ' kg/ha'
            plt.text(CropPatterns.index[int(xlocs[FertAppNo])],maxSoilN*1.1,recString,fontsize=8,rotation=0,horizontalalignment='center',verticalalignment='bottom')
            plt.arrow(CropPatterns.index[int(xlocs[FertAppNo])],maxSoilN*1.1,
                      (CropPatterns.index[d]-CropPatterns.index[int(xlocs[FertAppNo])]).days,
                      CropPatterns.iloc[d,4]-maxSoilN*1.1,
                      length_includes_head = True,)
            if FertAppNo == 0:
                FirstFertDay = d
            FertAppNo += 1
    plt.text(0.02,0.05,'Total N Fert = ' + str(int(np.ceil(NFertReq))) + ' kg/ha',transform=ax.transAxes,horizontalalignment='left',fontsize=8)
    plt.plot(CropPatterns.index,CropPatterns.mineral,color='blue')
    plt.text(CropPatterns.index[1],CropPatterns.iloc[0,4]*1.1,'Initial N \n' + str(int(InitialN))+ 'kg/ha',
             fontsize=8,horizontalalignment='left',verticalalignment='bottom',color='blue')
    plt.plot([CropPatterns.index[1],CropPatterns.index[30]], [CropPatterns.iloc[0,4]]*2,'--',color='blue')
    plt.text(CropPatterns.index[-1],CropPatterns.iloc[-1,4]*1.1,'Trigger N \n' + str(int(FinalN))+ 'kg/ha',
             fontsize=8,horizontalalignment='right',verticalalignment='bottom',color='purple')
    plt.plot([CropPatterns.index[FirstFertDay],CropPatterns.index[-1]], [CropPatterns.iloc[-1,4]]*2,'--',color='purple')
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    plt.xlim(EstabDate,HarvestDate)
    plt.ylim(0,maxSoilN*1.5)
    return CropPatterns


# -

test = DeriveCropUptake(Tt,[PriorConfig,CurrentConfig,FollowingConfig])
test.sort_index(inplace=True)

Tt[CurrentConfig["EstablishDate"]:CurrentConfig["HarvestDate"]] - Tt[CurrentConfig["EstablishDate"]]

px.line(data_frame=test,x='Date',y='Values',color='Nitrogen',color_discrete_sequence=['brown','yellow','red','green'])

px.line(data_frame=Data,x='Tt',y='Values',color='Nitrogen',color_discrete_sequence=['brown','yellow','red','green'],range_x = [EstablishDate,EndYearDate])

(defaultHarv - defaultSow).days


# +
# Iris bar figure
def drawFigure():
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    figure=px.bar(
                        df, x="sepal_width", y="sepal_length", color="species"
                    ).update_layout(
                        template='plotly_dark',
                        plot_bgcolor= 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)',
                    ),
                    config={
                        'displayModeBar': False
                    }
                ) 
            ])
        ),  
    ])

# Data
df = px.data.iris()

# Build App
app = JupyterDash(external_stylesheets=[dbc.themes.SLATE])

defaultLoc = 'Lincoln'
defaultStartDate = PriorConfig["EstablishDate"]
defaultEndDate = FollowingConfig["HarvestDate"] + dt.timedelta(days=7)
Tt = DeriveMedianTt(defaultLoc,defaultStartDate,defaultEndDate)

def CropInputs(pos):
    CropConfig = globals()[pos+"Config"]
    return dbc.CardBody([
    dbc.Row([dbc.Col([html.H1(pos+" Crop")], width=6 ,align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"Crop",options = CropDropDown,value=CropConfig["Crop"])], width=6 ,align='center'),]),
    html.Br(),
    dbc.Row([dbc.Col([html.Div('')], width=3, align='center'),
             dbc.Col([html.Div('Saleable Yield')], width=3, align='center'),
             dbc.Col([dcc.Input(id=pos+"SaleableYield", type="number",value=CropConfig["SaleableYield"],min=0.01)], width=3, align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"Units", options = UnitsDropDown,value=CropConfig["Units"])], width=3, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('')], width=3, align='center'),
             dbc.Col([html.Div('Field Loss (%)')], width=3, align='center'),
             dbc.Col([html.Div('Dressing loss (%)')], width=3, align='center'),
             dbc.Col([html.Div('Moisture (%)')], width=3, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('')], width=3, align='center'),
             dbc.Col([dcc.Input(id=pos+"FieldLoss", type="number",value=CropConfig["FieldLoss"],min=0,max=100)], width=3, align='center'),
             dbc.Col([dcc.Input(id=pos+"DressingLoss", type="number",value=CropConfig["DressingLoss"],min=0,max=100)], width=3, align='center'),
             dbc.Col([dcc.Input(id=pos+"MoistureContent", type="number",value=CropConfig["MoistureContent"],min=0,max=96)], width=3, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Planting Date')], width=3, align='center'),
             dbc.Col([dcc.DatePickerSingle(id=pos+"EstablishDate", min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2022, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            date=CropConfig["EstablishDate"],display_format='D-MMM-YYYY')], width=3, align='center'),
             dbc.Col([html.Div('Planting method')], width=3, align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"EstablishStage",options =EstablishStageDropdown,value=CropConfig["EstablishStage"])], width=3, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Harvest Date')], width=3, align='center'),
             dbc.Col([dcc.DatePickerSingle(id=pos+"HarvestDate", min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2022, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            date=CropConfig["HarvestDate"],display_format='D-MMM-YYYY')], width=3, align='center'), 
             dbc.Col([html.Div('Harvest Stage')], width=3, align='center'),
             dbc.Col([dcc.Dropdown(id=pos+"HarvestStage",options = HarvestStageDropdown,value=CropConfig["HarvestStage"])], width=3, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('ResidueTreatment')], width=3, align='center'), 
            dbc.Col([dcc.Dropdown(id=pos+"ResidueTreatment", options=ResidueTreatmentsDropdown,value=CropConfig["ResidueTreatment"])],width=3, align='center')]), 
    ])

app.layout = html.Div([
    dbc.Row([dbc.Col(html.H1("Field Location"), width=3 ,align='center'),
             dbc.Col(dcc.Dropdown(id="Location",options = MetDropDown,value='Lincoln'), width=3 ,align='center')]),
    dbc.Row([dbc.Col(html.H1("Soil Tests"), width=2 ,align='center'),
             dbc.Col(html.Div('HWEON'),width=1,align='center'),
             dbc.Col(dcc.Input(id="HWEON",type="number",value = 17,min=0),width=1, align='center'),
             dbc.Col(html.Div(''),width=1, align='center'),
             dbc.Col(html.Div('Mineral N'),width=1,align='center'),
             dbc.Col(dcc.Input(id="MineralN",type="number",value = 17,min=0),width=1, align='center'),
             ]),
    dbc.Row([dbc.Col(dbc.Card(CropInputs("Prior"))),
             dbc.Col(dbc.Card(CropInputs("Current"))),
             dbc.Col(dbc.Card(CropInputs("Following")))]),
    dbc.Row([dbc.Col(dbc.Card(dcc.Graph(id='CropUptakeGraph')),width=4),
             dbc.Col(dbc.Card(dcc.Graph(id='SoilMineralisation')),width=4),
             dbc.Col(dbc.Card(dcc.Graph(id='SoilN')),width=4)]),
    dbc.Row([dbc.Col(dbc.Card(dcc.Graph(id='TtGraph')),width=4)]) 
    ])
    
@app.callback(
    Output('TtGraph','figure'),
    Input('Location','value'),
    Input('PriorEstablishDate','date'),
    Input('FollowingHarvestDate','date'))
def update_Tt(Location,PriorEstablishDate,FollowingHarvestDate):
    StartDate = dt.datetime.strptime(str(PriorEstablishDate).split('T')[0],'%Y-%m-%d') 
    EndDate = dt.datetime.strptime(str(FollowingHarvestDate).split('T')[0],'%Y-%m-%d') + dt.timedelta(days=7)
    Tt = DeriveMedianTt(Location,StartDate,EndDate)
    fig = px.line(x=Tt.index,y=Tt.values)
    return fig

@app.callback(
    Output('CropUptakeGraph','figure'),
    Input('Location','value'),
    Input('CurrentCrop','value'),
    Input('CurrentSaleableYield','value'),
    Input('CurrentUnits','value'),
    Input('CurrentFieldLoss','value'),
    Input('CurrentDressingLoss','value'),
    Input('CurrentMoistureContent','value'),
    Input('CurrentEstablishDate','date'),
    Input('CurrentHarvestDate','date'),
    Input('CurrentEstablishStage','value'),
    Input('CurrentHarvestStage','value'),
    Input('CurrentResidueTreatment','value'))
def update_Cropgraph(Location,CurrentCrop,CurrentSaleableYield,CurrentUnits,CurrentFieldLoss,CurrentDressingLoss,
                     CurrentMoistureContent,CurrentEstablishDate,CurrentHarvestDate,CurrentEstablishStage,
                     CurrentHarvestStage,CurrentResidueTreatment):
    # EstablishDate = dt.datetime.strptime(str(CurrentEstablishDate).split('T')[0],'%Y-%m-%d')
    # HarvestDate = dt.datetime.strptime(str(CurrentHarvestDate).split('T')[0],'%Y-%m-%d')
    # CurrentConfig["Crop"]=CurrentCrop
    # CurrentConfig["SaleableYeild"] = 
    Data = DeriveCropUptake(Tt,[PriorConfig,CurrentConfig,FollowingConfig])
    GraphStart =PriorConfig["HarvestDate"] - dt.timedelta(day=14)
    EndYearDate 
    fig = px.line(data_frame=Data,x='Date',y='Values',color='Nitrogen',color_discrete_sequence=['brown','orange','red','green'],range_x = [GraphStart,EndYearDate])
    return fig
    
# @app.callback(
#     Output('SoilMineralisation','figure),
#     Input('Location','value'),
#     Input('EstablishDate','date'),
#     Input('HWEON','value'),
#     Input('PreviousCrop','value')
#     Input('PreviousCropYield','value')       
#     Input('ResidueTreatment','value'))
# def update_MineralisationGraph(Location,EstablishDate,HWEON,PreviousCrop,PreviousCropYield,
#     EstablishDate = dt.datetime.strptime(str(EstablishDate).split('T')[0],'%Y-%m-%d')
#     Tt = DeriveMedianTt(Location,EstablishDate)
#     StartResidue = 
    
# Run app and display result inline in the notebook
app.run_server(mode='External')
