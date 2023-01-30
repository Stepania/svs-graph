using System;
using System.Collections.Generic;

namespace Helper
{
    public class Crop
    {
        public string CropName { get; private set; }
        public string EstablishStage { get; private set; }
        public string HarvestStage { get; private set; }
        public double SaleableYield { get; private set; }
        public string Units { get; private set; }
        public double ToKGperHA { get { return Constants.UnitConversions[Units]; } }
        public double FieldLoss { get; private set; }
        public double DressingLoss { get; private set; }
        public double MoistureContent { get; private set; }
        public DateTime EstablishDate { get; private set; }
        public DateTime HarvestDate { get; private set; }
        public double ResRoot { get; set; }
        public double ResStover { get; set; }
        public double ResFieldLoss { get; set; }
        public Crop(Dictionary<string, object> c, string pos)
        {
            CropName = c[pos + "CropName"].ToString();
            EstablishStage = c[pos + "EstablishStage"].ToString();
            HarvestStage = c[pos + "HarvestStage"].ToString();
            SaleableYield = Functions.Num(c[pos + "SaleableYield"]);
            Units = c[pos + "Units"].ToString();
            FieldLoss = Functions.Num(c[pos + "FieldLoss"]);
            DressingLoss = Functions.Num(c[pos + "DressingLoss"]);
            MoistureContent = Functions.Num(c[pos + "MoistureContent"]);
            EstablishDate = Functions.Date(c[pos + "EstablishDate"]);
            HarvestDate = Functions.Date(c[pos + "HarvestDate"]);
        }
    }
}
