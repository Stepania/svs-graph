using System;
using System.Collections.Generic;
using System.IO;
using Helper;

namespace SVSModel
{
    class NBalance
    {
        public static double[,] CalculateSoilNBalance(double[] Tt, Dictionary<string, object> Config)
        {
            DateTime[] simDates = Functions.SimDates((DateTime)Config["StartDate"], (DateTime)Config["EndDate"]);
            
            //Initialise SoilN array
            Dictionary<DateTime,double> soilN = Functions.dictMaker(simDates, new double[simDates.Length]);
            soilN[(DateTime)Config["StartDate"]] = (double)Config["InitialN"];
            
            //Calculate Crop N uptake
            Dictionary<DateTime, double> NUptake = Functions.dictMaker(simDates, new double[simDates.Length]);
            foreach (string p in Constants.cropPositions()) //Step through each crop position
            {
                Dictionary<string, object> sCropConfig = Constants.CropConfigStrings; //Set blank crop specific config dict
                foreach(KeyValuePair<string,object> c in sCropConfig)
                {
                    sCropConfig[c.Key] = Config[p + c.Key]; // get crop position specific values from config for each value
                }
                Dictionary<string, double> dCropConfig = Constants.CropConfigDoubles; //Set blank crop specific config dict
                foreach (KeyValuePair<string, object> c in sCropConfig)
                {
                    sCropConfig[c.Key] = Config[p + c.Key]; // get crop position specific values from config for each value
                }

                //Calculate crop uptake and write into sim length dict
                Dictionary<DateTime, double> cropsNUptake = (Dictionary<DateTime, double>)CropModel.CalculateCropOutputs(Tt, dCropConfig, sCropConfig);
                foreach(KeyValuePair<DateTime,double> d in cropsNUptake)
                {
                    NUptake[d.Key] = cropsNUptake[d.Key];
                }
            }
           


            double[,] soilNarry = new double[simDates.Length, 2];
            
            return soilNarry;
        }

    }
}
