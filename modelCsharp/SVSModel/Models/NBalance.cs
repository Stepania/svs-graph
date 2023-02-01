using System;
using System.Collections.Generic;
using System.IO;
using Helper;

namespace SVSModel
{
    class NBalance
    {
        public static object[,] CalculateSoilNBalance(double[] tt, object[,] con, object[,] testResults)
        {
            //Dictionary<string, object> config = Functions.dictMaker(con);
            Config config = new Config(con);
            DateTime[] simDates = Functions.SimDates(config.Prior.EstablishDate, config.Following.HarvestDate);
            Dictionary<DateTime, double> Tt = Functions.dictMaker(simDates, tt);
            Dictionary<string, double> RotationCropValues = Constants.RotationCropValues;
       
            //Calculate Crop N uptake
            Dictionary<DateTime, double> NUptake = Functions.dictMaker(simDates, new double[simDates.Length]);
            foreach (Crop crop in config.Rotation) //Step through each crop position
            {
                DateTime[] cropDates = Functions.SimDates(crop.EstablishDate, crop.HarvestDate);
                Dictionary<DateTime, double> AccTt = Functions.AccumulateTt(cropDates, Tt);
  
                //Calculated outputs for each crop
                object[,] cropsOutPuts = CropModel.CalculateOutputs(AccTt, crop);

                //write to N uptake dict for rotation
                Dictionary<DateTime, double> cropsNUptake = Functions.dictMaker(cropsOutPuts, "CropUptakeN");
                foreach (KeyValuePair<DateTime, double> d in cropsNUptake)
                {
                    NUptake[d.Key] = cropsNUptake[d.Key];
                }

                //write final crop variables to field config dict
                
                crop.ResRoot = Functions.GetFinal(cropsOutPuts, "RootN");
                crop.ResStover = Functions.GetFinal(cropsOutPuts, "StoverN");
                crop.ResFieldLoss = Functions.GetFinal(cropsOutPuts, "FieldLossN");
                crop.NUptake = Functions.GetFinal(cropsOutPuts, "CropUptakeN");
            }

            // Calculate residue mineralisation
            Dictionary<DateTime, double> NResidues = ResidueMineralisationModel.CalculateOutputs(simDates, Tt, config);

            // Calculate soil OM mineralisation
            Dictionary<DateTime, double> NSoilOM = SOMMineralisationModel.CalculateOutputs(simDates, Tt, config);

            //Calculate basic soil N
            Dictionary<DateTime, double> SoilN = MineralNCalculations.Initial(simDates, config.field.InitialN, NUptake, NResidues, NSoilOM);

            //Reset soil N with test valaues
            Dictionary<DateTime, double> TestResults = Functions.dictMaker(testResults,"Test");
            MineralNCalculations.TestCorrection(TestResults, ref SoilN);

            //Calculate 
            Dictionary<DateTime, double> Fertiliser = MineralNCalculations.DetermineFertRequirements(ref SoilN, NResidues, NSoilOM, NUptake, TestResults, config);
            

            // Pack Daily State Variables into a 2D array so they can be output
            object[,] soilNarry = new object[simDates.Length + 1, 5];

            soilNarry[0, 0] = "Date"; Functions.packRows(0, simDates, ref soilNarry);
            soilNarry[0, 1] = "SoilMineralN"; Functions.packRows(1, SoilN, ref soilNarry);
            soilNarry[0, 2] = "UptakeN"; Functions.packRows(2, NUptake, ref soilNarry);
            soilNarry[0, 3] = "ResidueN"; Functions.packRows(3, NResidues, ref soilNarry);
            soilNarry[0, 4] = "SoilOMN"; Functions.packRows(4, NSoilOM, ref soilNarry);

            return soilNarry;
        }

    }
}
