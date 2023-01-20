using System;
using System.Collections.Generic;
using System.IO;
using Helper;

namespace SVSModel
{
    class NBalance
    {
        public static object[,] CalculateSoilNBalance(double[] Tt, Dictionary<string, object> config)
        {
            DateTime[] simDates = Functions.SimDates((DateTime)config["StartDate"], (DateTime)config["EndDate"]);
            
            //Initialise SoilN array
            Dictionary<DateTime,double> soilN = Functions.dictMaker(simDates, new double[simDates.Length]);
            soilN[(DateTime)config["StartDate"]] = (double)config["InitialN"];
            
            //Calculate Crop N uptake
            Dictionary<DateTime, double> NUptake = Functions.dictMaker(simDates, new double[simDates.Length]);
            foreach (string p in Constants.cropPositions()) //Step through each crop position
            {
                Dictionary<string, object> sCropConfig = Constants.CropConfigStrings; //Set blank crop specific config dict
                List<string> skeys = new List<string>(sCropConfig.Keys);
                foreach (string k in skeys)
                {
                    sCropConfig[k] = config[k]; // get crop position specific values from config for each value
                }
                Dictionary<string, double> dCropConfig = Constants.CropConfigDoubles; //Set blank crop specific config dict
                List<string> dkeys = new List<string>(dCropConfig.Keys);
                foreach (string k in dkeys)
                {
                    if (k != "Units") //
                    {
                        dCropConfig[k] = double.Parse(config[k].ToString()); // get crop position specific values from config for each value
                    }
                    else
                    {
                        dCropConfig[k] = Constants.UnitConversions[k];
                    }
                }

                //Calculate crop uptake and write into sim length dict
                Dictionary<DateTime, double> cropsNUptake = (Dictionary<DateTime, double>)CropModel.CalculateCropOutputs(Tt, dCropConfig, sCropConfig);
                foreach(KeyValuePair<DateTime,double> d in cropsNUptake)
                {
                    NUptake[d.Key] = cropsNUptake[d.Key];
                }
            }


            // Pack Daily State Variables into a 2D array so they can be output
            object[,] soilNarry = new object[simDates.Length, 3];
            
            soilNarry[0, 0] = "Date"; Functions.packRows(0, simDates, ref soilNarry);
            soilNarry[0, 1] = "RootN"; Functions.packRows(1, soilN, ref soilNarry);
            soilNarry[0, 2] = "UptakeN"; Functions.packRows(1, NUptake, ref soilNarry);

            return soilNarry;
        }

    }
}
