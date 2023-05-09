using System;
using System.Collections.Generic;

namespace SVSModel.Configuration
{
    /// <summary>
    /// Class that stores the configuration information in the correct type for a specific crop .  
    /// I.e constructor takes all config settings as objects and converts them to appropriates types
    /// </summary>
    public class CropConfig
    {
        public string CropNameFull { get; set; }
        public string EstablishStage { get; set; }
        public string HarvestStage { get; set; }
        public double SaleableYield { get; set; }
        public string Units { get; set; }
        public double ToKGperHA { get { return Constants.UnitConversions[Units]; } }
        public double FieldLoss { get; set; }
        public double DressingLoss { get; set; }
        public double MoistureContent { get; set; }
        public DateTime EstablishDate { get; set; }
        public DateTime HarvestDate { get; set; }
        public double ResidueFactRetained { get; set; }
        public double ResidueFactIncorporated { get; set; }
        public double ResRoot { get; set; }
        public double ResStover { get; set; }
        public double ResFieldLoss { get; set; }
        public double NUptake { get; set; }

        public CropConfig() { }

        public CropConfig(Dictionary<string, object> c, string pos)
        {
            CropNameFull = c[pos + "CropNameFull"].ToString();
            EstablishStage = c[pos + "EstablishStage"].ToString();
            HarvestStage = c[pos + "HarvestStage"].ToString();
            SaleableYield = Functions.Num(c[pos + "SaleableYield"]) * 1000; //UI sends yield in t/ha but model works in kg/ha so convert here
            FieldLoss = Functions.Num(c[pos + "FieldLoss"]);
            DressingLoss = Functions.Num(c[pos + "DressingLoss"]);
            MoistureContent = Functions.Num(c[pos + "MoistureContent"]);
            EstablishDate = Functions.Date(c[pos + "EstablishDate"]);
            HarvestDate = Functions.Date(c[pos + "HarvestDate"]);
            ResidueFactRetained = Constants.ResidueFactRetained[c[pos + "ResidueRemoval"].ToString()];
            ResidueFactIncorporated = Constants.ResidueIncorporation[c[pos + "ResidueIncorporation"].ToString()];
        }
    }
}
