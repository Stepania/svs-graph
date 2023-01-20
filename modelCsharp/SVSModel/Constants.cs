using System.Collections.Generic;


namespace Helper
{
    class Constants
    {
        /// <summary>Dictionary containing values for the proportion of maximum DM that occurs at each predefined crop stage</summary>
        public static Dictionary<string, double> PropnMaxDM = new Dictionary<string, double>() { { "Seed", 0.0066 },{ "Seedling", 0.015 },{ "Vegetative", 0.5},{ "EarlyReproductive",0.75},
            { "MidReproductive",0.86},{  "LateReproductive",0.95},{"Maturity",0.9933},{"Late",0.9995 } };

        /// <summary>Dictionary containing values for the proportion of thermal time to maturity that has accumulate at each predefined crop stage</summary>
        public static Dictionary<string, double> PropnTt = new Dictionary<string, double>() { { "Seed", 0 },{ "Seedling", 0.16 },{ "Vegetative", 0.5},{ "EarlyReproductive",0.61},
            { "MidReproductive",0.69},{  "LateReproductive",0.8},{"Maturity",1.0},{"Late",1.27} };

        /// <summary>blank Dictionary containing keys for specific crop configuration doubles</summary>
        public static Dictionary<string, double> CropConfigDoubles = new Dictionary<string, double>() {{"SaleableYield",new double()},{"Units",new double()},{"FieldLoss",new double()},
            {"DressingLoss",new double()},{"MoistureContent",new double()},{ "EstablishDate",new double()},{"HarvestDate",new double()}};

        /// <summary>blank Dictionary containing keys for specific crop configuration settings</summary>
        public static Dictionary<string, object> CropConfigStrings = new Dictionary<string, object>() {{ "CropName",new object()},
            {"EstablishStage",new object()},{"HarvestStage",new object()},{"ResidueTreatment",new object()}};
        public static System.Collections.IEnumerable cropPositions()
        {
            yield return "Prior";
            yield return "Current";
            yield return "Following";
        }

        /// <summary>Dictionary containing conversion from specified units to kg/ha which are the units that the model works in </summary>
        public static Dictionary<string, double> UnitConversions = new Dictionary<string, double>() { { "t/ha", 1000 }, { "kg/ha", 1.0 } };
    }
}
