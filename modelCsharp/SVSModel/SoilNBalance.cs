using System;
using System.Collections.Generic;
using Helper;

namespace SVSModel
{
    class SoilNBalance
    {
        public static double[,] CalculateSoilNBalance(double[] Tt, Dictionary<string, object> Config, Dictionary<string, object> Params)
        {
            DateTime[] simDates = Functions.SimDates((DateTime)Config["StartDate"], (DateTime)Config["EndDate"]);
            
            //Initialise SoilN array
            Dictionary<DateTime,double> soilN = Functions.dictMaker(simDates, new double[simDates.Length]);
            soilN[(DateTime)Config["StartDate"]] = (double)Config["InitialN"];

            
            double[,] soilNarry = new double[simDates.Length, 2];
            
            return soilNarry;
        }

    }
}
