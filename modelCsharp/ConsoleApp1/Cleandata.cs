using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ConsoleApp1
{
    internal class Cleandata
    {
        public static Dictionary<string, object> configDict = new Dictionary<string, object>
            {
                {"InitialN",50},
                {"SoilOrder","Brown"},
                {"SampleDepth","0-30cm"},
                {"BulkDensity",1.22},
                { "PMNtype","PMN"},
                {"PMN",60},
                { "Trigger",30},
                { "Efficiency",80},
                { "Splits",1},
                { "AWC",120},
                { "PrePlantRain","Typical"},
                { "InCropRain","Typical"},
                { "Irrigation","None"},
                { "PriorCropNameFull","Barley Fodder General"},
                { "PriorSaleableYield",8},
                { "PriorFieldLoss",0},
                { "PriorDressingLoss",0},
                { "PriorMoistureContent",0},
                { "PriorEstablishDate","28/08/2023"},
                { "PriorEstablishStage","Seed"},
                { "PriorHarvestDate","27/09/2023"},
                { "PriorHarvestStage","EarlyReproductive"},
                { "PriorResidueRemoval","None removed"},
                { "PriorResidueIncorporation","Full (Plough)"},
                { "CurrentCropNameFull","Barley Fodder General"},
                { "CurrentSaleableYield",8},
                { "CurrentFieldLoss",0},
                { "CurrentDressingLoss",0},
                { "CurrentMoistureContent",0},
                { "CurrentEstablishDate","17/10/2023"},
                { "CurrentEstablishStage","Seed"},
                { "CurrentHarvestDate","27/10/2023"},
                { "CurrentHarvestStage","EarlyReproductive"},
                { "CurrentResidueRemoval","None removed"},
                { "CurrentResidueIncorporation","Full (Plough)"},
                { "FollowingCropNameFull","Oat Fodder General"},
                { "FollowingSaleableYield",10},
                { "FollowingFieldLoss",0},
                { "FollowingDressingLoss",0},
                { "FollowingMoistureContent",0},
                { "FollowingEstablishDate","6/11/2023"},
                { "FollowingEstablishStage","Seed"},
                { "FollowingHarvestDate","16/11/2023"},
                { "FollowingHarvestStage","EarlyReproductive"},
                { "FollowingResidueRemoval","None removed"},
                { "FollowingResidueIncorporation","Full (Plough)"}
            };
    }
}
