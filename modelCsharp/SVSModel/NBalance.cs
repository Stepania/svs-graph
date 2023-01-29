﻿using System;
using System.Collections.Generic;
using System.IO;
using Helper;

namespace SVSModel
{
    class NBalance
    {
        public static object[,] CalculateSoilNBalance(double[] tt, object[,] Config)
        {
            Dictionary<string, object> config = Functions.dictMaker(Config);
            DateTime[] simDates = Functions.SimDates(config["PriorEstablishDate"], config["FollowingHarvestDate"]);
            Dictionary<DateTime, double> Tt = Functions.dictMaker(simDates, tt);
            Dictionary<string, double> RotationCropValues = Constants.RotationCropValues;

            //Calculate Crop N uptake
            Dictionary<DateTime, double> NUptake = Functions.dictMaker(simDates, new double[simDates.Length]);
            foreach (string p in Constants.cropPositions()) //Step through each crop position
            {
                DateTime[] cropDates = Functions.SimDates(config[p+"EstablishDate"], config[p+"HarvestDate"]);
                Dictionary<DateTime, double> AccTt = Functions.AccumulateTt(cropDates, Tt);
                Dictionary<string, object> sCropConfig = Constants.CropConfigStrings; //Set blank crop specific config dict
                List<string> skeys = new List<string>(sCropConfig.Keys);
                foreach (string k in skeys)
                {
                    sCropConfig[k] = config[p + k]; // get crop position specific values from config for each value
                }
                Dictionary<string, double> dCropConfig = Constants.CropConfigDoubles; //Set blank crop specific config dict
                List<string> dkeys = new List<string>(dCropConfig.Keys);
                foreach (string k in dkeys)
                {
                    if (k != "Units") //
                    {
                        dCropConfig[k] = double.Parse(config[p + k].ToString()); // get crop position specific values from config for each value
                    }
                    else
                    {
                        dCropConfig[k] = Constants.UnitConversions[config[p + k].ToString()];
                    }
                }

                //Calculated outputs for each crop
                object[,] cropsOutPuts = CropModel.CalculateOutputs(AccTt, dCropConfig, sCropConfig);

                //write to N uptake dict for rotation
                Dictionary<DateTime, double> cropsNUptake = Functions.dictMaker(cropsOutPuts, "CropUptakeN");
                foreach (KeyValuePair<DateTime, double> d in cropsNUptake)
                {
                    NUptake[d.Key] = cropsNUptake[d.Key];
                }

                //write final crop variables to field config dict
                RotationCropValues[p + "ResRoot"] = Functions.GetFinal(cropsOutPuts, "RootN");
                RotationCropValues[p + "RsStover"] = Functions.GetFinal(cropsOutPuts, "StoverN");
                RotationCropValues[p + "ResFieldLoss"] = Functions.GetFinal(cropsOutPuts, "FieldLossN");
                RotationCropValues[p + "EstablishDate"] = dCropConfig["EstablishDate"];
                RotationCropValues[p + "HarvestDate"] = dCropConfig["HarvestDate"];
            }

            // Calculate residue mineralisation
            Dictionary<DateTime, double> NResudues = ResidueMineralisationModel.CalculateOutputs(simDates, Tt, config, RotationCropValues);

            // Calculate soil OM mineralisation
            Dictionary<DateTime, double> NSoilOM = SOMMineralisationModel.CalculateOutputs(simDates, Tt, config);

            //Initialise SoilN array
            Dictionary<DateTime, double> soilN = MineralN.CalculateOutputs(simDates, (double)config["InitialN"], NUptake, NResudues, NSoilOM);
            

            // Pack Daily State Variables into a 2D array so they can be output
            object[,] soilNarry = new object[simDates.Length + 1, 5];

            soilNarry[0, 0] = "Date"; Functions.packRows(0, simDates, ref soilNarry);
            soilNarry[0, 1] = "SoilMineralN"; Functions.packRows(1, soilN, ref soilNarry);
            soilNarry[0, 2] = "UptakeN"; Functions.packRows(2, NUptake, ref soilNarry);
            soilNarry[0, 3] = "ResidueN"; Functions.packRows(3, NResudues, ref soilNarry);
            soilNarry[0, 4] = "SoilOMN"; Functions.packRows(4, NSoilOM, ref soilNarry);

            return soilNarry;
        }

    }
}
