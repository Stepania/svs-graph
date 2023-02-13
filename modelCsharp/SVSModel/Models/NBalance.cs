using System;
using System.Collections.Generic;
using System.IO;
using Helper;

namespace SVSModel
{
    class NBalance
    {
        /// <summary>
        /// Function that steps through each of the components of the N balance for a crop rotation and returns the results in 2D array format
        /// </summary>
        /// <param name="meanT">A date indexed dictionary of daily mean temperatures</param>
        /// <param name="config">A specific class that holds all the simulation configuration data in the correct types for use in the model</param>
        /// <param name="testResults">A date indexed dictionary with soil mineral N test results</param>
        /// <returns>A 2D array of N balance variables</returns>
        public static object[,] CalculateSoilNBalance(Dictionary<DateTime, double> meanT,
                                                      Dictionary<DateTime, double> meanRain,
                                                      Dictionary<DateTime, double> meanPET,
                                                      Config config, 
                                                      Dictionary<DateTime, double> testResults, 
                                                      Dictionary<DateTime, double> nAapplied)
        {
            DateTime[] simDates = Functions.DateSeries(config.Prior.HarvestDate.AddDays(-1), config.Following.HarvestDate);

            //Run crop model for each crop in rotation to calculate CropN (total standing in in crop) and Nuptake (Daily N removal from the soil by the crop)
            Dictionary<DateTime, double> NUptake = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> CropN = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> ProductN = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> LostN = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> Cover = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> RSWC = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> Drainage = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> Irrigation = Functions.dictMaker(simDates, new double[simDates.Length]);
            
            foreach (Crop crop in config.Rotation) //Step through each crop position
            {
                //Make date series for duraion of the crop and accumulate thermal time over that period
                DateTime[] cropDates = Functions.DateSeries(crop.EstablishDate, crop.HarvestDate);
                Dictionary<DateTime, double> AccTt = Functions.AccumulateTt(cropDates, meanT);

                //Calculated outputs for each crop
                object[,] cropsOutPuts = CropModel.CalculateOutputs(AccTt, crop);

                //Pack Crop N and N uptake results for each crop into the corresponding variables for the rotation (i.e stick all crops together to form the rotation)
                Dictionary<DateTime, double> cropsNUptake = Functions.dictMaker(cropsOutPuts, "CropUptakeN");
                Dictionary<DateTime, double> totalCropN = Functions.dictMaker(cropsOutPuts, "TotalCropN");
                Dictionary<DateTime, double> productN = Functions.dictMaker(cropsOutPuts, "SaleableProductN");
                Dictionary<DateTime, double> cover = Functions.dictMaker(cropsOutPuts, "Cover");
                foreach (DateTime d in cropsNUptake.Keys)
                {
                    if (d >= simDates[0])
                    {
                        NUptake[d] = cropsNUptake[d];
                        CropN[d] = totalCropN[d];
                        ProductN[d] = productN[d];
                        Cover[d] = cover[d];
                    }
                }

                //Pack final crop variables to field config dict for use in other parts of the N balance
                crop.ResRoot = Functions.GetFinal(cropsOutPuts, "RootN");
                crop.ResStover = Functions.GetFinal(cropsOutPuts, "StoverN") * crop.ResidueFactRetained;
                crop.ResFieldLoss = Functions.GetFinal(cropsOutPuts, "FieldLossN") * crop.ResidueFactRetained;
                crop.NUptake = Functions.GetFinal(cropsOutPuts, "TotalCropN");
            }

            // Calculate soil water content and drainage
            SoilWater.Balance(ref RSWC, ref Drainage, ref Irrigation, meanRain, meanPET, Cover, config);
            
            // Calculate residue mineralisation
            Dictionary<DateTime, double> NResidues = ResidueMineralisationModel.CalculateOutputs(simDates, meanT, config);

            // Calculate soil OM mineralisation
            Dictionary<DateTime, double> NSoilOM = SOMMineralisationModel.CalculateOutputs(simDates, meanT, config);

            //Calculate soil N estimated without fertiliser or soil test results
            Dictionary<DateTime, double> SoilN = MineralNCalculations.Initial(simDates, config.field.InitialN, NUptake, NResidues, NSoilOM);

            //Add fertiliser that has already been applied to the N balance
            Dictionary<DateTime, double> FertiliserN = MineralNCalculations.ApplyExistingFertiliser(simDates, nAapplied, testResults, ref SoilN, ref LostN, config);

            //Reset soil N with test valaues
            MineralNCalculations.TestCorrection(testResults, ref SoilN);

            //Calculate Fertiliser requirements and add into soil N
            MineralNCalculations.DetermineFertRequirements(ref FertiliserN, ref SoilN, ref LostN, NResidues, NSoilOM, CropN, testResults, config);

            //Pack Daily State Variables into a 2D array so they can be output
            object[,] outputs = new object[simDates.Length + 1, 13];

            outputs[0, 0] = "Date"; Functions.packRows(0, simDates, ref outputs);
            outputs[0, 1] = "SoilMineralN"; Functions.packRows(1, SoilN, ref outputs);
            outputs[0, 2] = "UptakeN"; Functions.packRows(2, NUptake, ref outputs);
            outputs[0, 3] = "ResidueN"; Functions.packRows(3, NResidues, ref outputs);
            outputs[0, 4] = "SoilOMN"; Functions.packRows(4, NSoilOM, ref outputs);
            outputs[0, 5] = "FertiliserN"; Functions.packRows(5, FertiliserN, ref outputs);
            outputs[0, 6] = "CropN"; Functions.packRows(6, CropN, ref outputs);
            outputs[0, 7] = "ProductN"; Functions.packRows(7, ProductN, ref outputs);
            outputs[0, 8] = "LostN"; Functions.packRows(8, LostN, ref outputs);
            outputs[0, 9] = "RSWC"; Functions.packRows(9, RSWC, ref outputs);
            outputs[0, 10] = "Drainage"; Functions.packRows(10, Drainage, ref outputs);
            outputs[0, 11] = "Irrigation"; Functions.packRows(11, Irrigation, ref outputs);
            outputs[0, 12] = "Green cover"; Functions.packRows(12, Cover, ref outputs);

            return outputs;
        }
    }
}
