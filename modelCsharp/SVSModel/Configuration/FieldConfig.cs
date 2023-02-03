using System;
using System.Collections.Generic;

namespace Helper
{
    /// <summary>
    /// Class that stores the configuration information for a rotation of 3 crops in the correct type.  
    /// I.e constructor takes all config settings as objects and converts them to appropriates types
    /// </summary>
    public class Field
    {
        public double InitialN { get; private set; }
        public double HWEON { get; private set; }
        public double EstablishFertN { get; private set; }
        public double Trigger { get; private set; }
        public double Efficiency { get; private set; }
        public int Splits { get; private set; }
        public Field(Dictionary<string, object> c)
        {
            InitialN = Functions.Num(c["InitialN"]);
            HWEON = Functions.Num(c["HWEON"]);
            EstablishFertN = Functions.Num(c["EstablishN"]);
            Trigger = Functions.Num(c["Trigger"]);
            Efficiency = Functions.Num(c["Efficiency"])/100;
            Splits = int.Parse(c["Splits"].ToString());
        }
    }
}
