using System;
using System.Collections.Generic;

namespace Helper
{
    /// <summary>
    /// Class that stores the configuration information for a rotation of 3 crops in the correct type.  
    /// I.e constructor takes all config settings as objects and converts them to appropriates types
    /// </summary>
    public class FieldConfig
    {
        public double InitialN { get; private set; }
        public double HWEON { get; private set; }
        public double Trigger { get; private set; }
        public double Efficiency { get; private set; }
        public int Splits { get; private set; }
        public double AWC { get; private set; }
        public double PrePlantRainFactor { get; private set; }
        public double InCropRainFactor {get; private set;}
        public double IrrigationTrigger { get; private set; }
        public double IrrigationRefill { get; private set; }
        public FieldConfig(Dictionary<string, object> c)
        {
            InitialN = Functions.Num(c["InitialN"]);
            HWEON = Functions.Num(c["HWEON"]);
            Trigger = Functions.Num(c["Trigger"]);
            Efficiency = Functions.Num(c["Efficiency"])/100;
            Splits = int.Parse(c["Splits"].ToString());
            AWC = Functions.Num(c["AWC"]);
            PrePlantRainFactor = Constants.RainFactors[c["PrePlantRain"].ToString()];
            InCropRainFactor = Constants.RainFactors[c["PrePlantRain"].ToString()];
            IrrigationRefill = Constants.IrrigationRefull[c["Irrigation"].ToString()];
            IrrigationTrigger = Constants.IrrigationTriggers[c["Irrigation"].ToString()];
        }
    }
}
