using Helper;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SVSModel
{
    class Fertiliser
    {
        /* public static Dictionary<DateTime, double> CalculateOutputs(DateTime[] simDates, ref Dictionary<DateTime, double> soilN, Config config)
         {
             Dictionary<DateTime, double> fert = Functions.dictMaker(simDates, new double[simDates.Length]);
             //Apply Planting N
             fert[config.Current.EstablishDate] = config.field.EstablishN);
             soilN[config.Current.EstablishDate] += Functions.Num(config["EstablishN"]);
             //Calculate further N requirements
             double InitialSoilN = NBalance.loc[CurrentConfig['EstablishDate'], 'SoilMineralN']
             double InCropMineralisation = NBalance.loc[CurrentConfig['EstablishDate']:CurrentConfig['HarvestDate'],['SOMNmineraliation', 'ResidueMineralisation']].sum().sum()
             CropN = NBalance.loc[CurrentConfig['HarvestDate'], 'TotalCrop'] - NBalance.loc[CurrentConfig['EstablishDate'], 'TotalCrop']
             NFertReq = (CropN + trigger) - InitialSoilN - InCropMineralisation
             NFertReq = NFertReq * 1 / efficiency
             NAppn = np.ceil(NFertReq / splits)
             FertApplied = 0
             FertAppNo = 0
             ffd = (CurrentConfig['HarvestDate'].astype(dt.datetime) - dt.timedelta(days = 5)).strftime('%Y-%m-%d')
             if splits > 0:
                 for d in NBalance[CurrentConfig['EstablishDate']:ffd].index:
                     yesterday = d - dt.timedelta(days = 1)
                     if (NBalance.loc[d, 'SoilMineralN'] < trigger) and(FertApplied < NFertReq):
                         NBalance.loc[d:, 'SoilMineralN'] = NBalance.loc[yesterday:, 'SoilMineralN'] + (NAppn * efficiency)
                         NBalance.loc[d, 'FertiliserN'] = NAppn
             NBalance.loc[:FieldConfig['MinNDate'], 'SoilMineralN'] = np.nan
             return NBalance
     }*/
    }
}
