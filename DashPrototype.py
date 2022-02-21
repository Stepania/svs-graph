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

def DeriveMedianTt(Loc,EstablishDate,HarvestDate):
    ## Calculate median thermaltime for location
    Met = metFiles[Loc]
    FirstYear = int(Met.Year[0])
    years = [x for x in Met.Year.drop_duplicates().values[1:-1]]
    day = EstablishDate.day
    month = EstablishDate.month
    FirstDate = dt.date(FirstYear,month,day)
    TT = pd.DataFrame(columns = years,index = range(1,368))
    for y in years:
        start = str(EstablishDate.day) + '-' + str(EstablishDate.month) + '-' + str(int(y))
        end = str(HarvestDate.day) + '-' + str(HarvestDate.month) + '-' + str(int(y)+1)
        duration = (dt.datetime.strptime(end,'%d-%m-%Y') - dt.datetime.strptime(start,'%d-%m-%Y')).days
        try:
            TT.loc[:,y] = Met.loc[start:,'tt'].cumsum().values[:367]
        except:
            do = 'nothing'
    TTmed = (TT.median(axis=1))/30 # (TT.median(axis=1)-[5*x for x in TT.index])/30
    TTmed.index = pd.date_range(start=EstablishDate,periods=367,freq='D',name='Date')
    TTmed.name = 'Tt'
    return TTmed


def DeriveCropUptake(TTmed,EstablishDate,HarvestDate,EstablishStage,HarvestStage,Crop,ExpectedYield):
    ## Calculate model parameters 
    Tt_Harv = TTmed[HarvestDate]
    Tt_estab = Tt_Harv * (StagePropns.loc[EstablishStage,'PrpnTt']/StagePropns.loc[HarvestStage,'PrpnTt'])
    Xo_Biomass = (Tt_Harv + Tt_estab) *.5 * (1/StagePropns.loc[HarvestStage,'PrpnTt'])
    b_Biomass = Xo_Biomass * .2
    # Calculate fitted patterns
    BiomassScaller = []
    for tt in TTmed[EstablishDate:HarvestDate]:
        BiomassScaller.append(1/(1+np.exp(-((tt-Xo_Biomass)/(b_Biomass)))))
    RejectProportion = 0.1 # Proportion of tubers left in feild
    TotalProduct = ExpectedYield * (1 + RejectProportion)
    DryYield = TotalProduct * 1000 * CropCoefficients.loc[Crop,'k_DM'] # dry matter content of tubers
    HI = CropCoefficients.loc[Crop,'a_Harvest'] + ExpectedYield * CropCoefficients.loc[Crop,'b_harvest']
    StoverYield = DryYield * 1/HI - DryYield # Harvest index
    RootYield = (StoverYield+DryYield) * CropCoefficients.loc[Crop,'p_Root']
    ProductN = DryYield * CropCoefficients.loc[Crop,'Nconc_Tops']
    StoverN = StoverYield * CropCoefficients.loc[Crop,'Nconc_Stover']
    RootN = RootYield * CropCoefficients.loc[Crop,'Nconc_Roots']
    totalN = ProductN + StoverN + RootN
    CropN = np.multiply(np.multiply(BiomassScaller , 1/(StagePropns.loc[HarvestStage,'PrpnMaxDM'])), totalN)
    return pd.DataFrame(index=TTmed[EstablishDate:HarvestDate].index,data=CropN,columns=['Values'])
    
def MineralisationGraph(ax,Met,Establish,Harvest,EstablishStage,HarvestStage,p,col):
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
        end = Establish + '-' + str(y+1)
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
defaultSow = dt.datetime.strptime('01-01-2020','%d-%m-%Y')
defaultHarv = dt.datetime.strptime('10-10-2020','%d-%m-%Y')
Tt = DeriveMedianTt(defaultLoc,defaultSow,defaultHarv)

app.layout = html.Div([
    dbc.Card(
    dbc.CardBody([
    dbc.Row([dbc.Col([html.Div('Location of field')], width=1, align='right'),
             dbc.Col([dcc.Dropdown(id="Location",options = MetDropDown,value=defaultLoc)], width=3, align='center')]), 
    html.Br(),
    dbc.Row(dbc.Col([html.Div('Crop Grown.')], width=3 ,align='center')),
    html.Br(),
    dbc.Row([dbc.Col([dcc.Dropdown(id="Crop",options = CropDropDown,value='Barleyspring')], width=3 ,align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Salable Yield')], width=1, align='center'),
             dbc.Col([html.Div('Units')], width=1, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([dcc.Input(id="ExpectedYield", type="number",value=20)], width=1, align='center'),
             dbc.Col([dcc.Dropdown(id="Units", options = UnitsDropDown,value='t/ha')], width=1, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Field Harvest (%)')], width=1, align='center'),
             dbc.Col([html.Div('Dressing (%)')], width=1, align='center'),
             dbc.Col([html.Div('Moisture (%)')], width=1, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([dcc.Input(id="FieldHarvest", type="number",value=10)], width=1, align='center'),
             dbc.Col([dcc.Input(id="Dressing", type="number",value=10)], width=1, align='center'),
             dbc.Col([dcc.Input(id="MoistureContent", type="number",value=80)], width=1, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Planting Date')], width=1, align='center'),
             dbc.Col([html.Div('Planting method')], width=3, align='center'),
             dbc.Col([html.Div('Residue')], width=1, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([dcc.DatePickerSingle(id='EstablishDate', min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2022, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            date=defaultSow,display_format='Do/MMM/YYYY')], width=1, align='center'),
            dbc.Col([dcc.Dropdown(id="EstablishStage",options =EstablishStageDropdown,value='Seed')], width=3, align='center'),
            dbc.Col([dcc.Input(id="Residue", type="number",value=20)],width=3, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([html.Div('Harvest Date')], width=1, align='center'),
             dbc.Col([html.Div('Harvest Stage')], width=3, align='center'),
             dbc.Col([html.Div('HWEON')], width=1, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([dcc.DatePickerSingle(id='HarvestDate', min_date_allowed=dt.date(2020, 1, 1),
                                            max_date_allowed=dt.date(2022, 12, 31), initial_visible_month=dt.date(2021, 5, 15),
                                            date=defaultHarv,display_format='Do/MMM/YYYY')], width=1, align='center'), 
             dbc.Col([dcc.Dropdown(id="HarvestStage",options = HarvestStageDropdown,value='Maturity')], width=3, align='center'),
             dbc.Col([dcc.Input(id="HWEON", type="number",value=20)],width=3, align='center')]), 
    html.Br(),
    dbc.Row([dbc.Col([dcc.Graph(id='CropUptakeGraph')], width=4, align='center'), 
             dbc.Col([dcc.Graph(id='SoilMineralisation')], width=4, align='center'),
            dbc.Col([dcc.Graph(id='SoilN')], width=4, align='center')]), 
    html.Br(),
    ]), color = 'dark'
    )
])

@app.callback(
    Output('CropUptakeGraph','figure'),
    Input('Location','value'),
    Input('Crop','value'),
    Input('ExpectedYield','value'),
    Input('EstablishDate','date'),
    Input('HarvestDate','date'),
    Input('EstablishStage','value'),
    Input('HarvestStage','value'))
def update_Cropgraph(Location,Crop,ExpectedYield,EstablishDate,HarvestDate,EstablishStage,HarvestStage):
    EstablishDate = dt.datetime.strptime(str(EstablishDate).split('T')[0],'%Y-%m-%d')
    HarvestDate = dt.datetime.strptime(str(HarvestDate).split('T')[0],'%Y-%m-%d')
    EndYearDate  = EstablishDate + dt.timedelta(days = 365)
    Tt = DeriveMedianTt(Location,EstablishDate,HarvestDate)
    Data = DeriveCropUptake(Tt,EstablishDate,HarvestDate,EstablishStage,HarvestStage,Crop,ExpectedYield)
    fig = px.line(x=Data.index, y=Data.Values,color_discrete_sequence=['green'],range_x = [EstablishDate,EndYearDate])
    return fig
    
# @app.callback(
#     Output('SoilMineralisation','figure),
#     Input('Location','value'),
#     Input('EstablishDate','date'),
#     Input('HWEON','value'),
#     Input('PreviousCrop','value')
#     Input('PreviousCropYield','value')       
#     Input('ResidueTreatment','value')
# def update_MineralisationGraph(Location,EstablishmentDate,HWEON,PreviousCrop,PreviousCropYield,

# )    
    
# Run app and display result inline in the notebook
app.run_server(mode='external')
