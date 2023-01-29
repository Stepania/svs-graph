using Microsoft.Data.Analysis;
using SVSModel;
using System;
using System.Collections.Generic;

namespace Helper
{
    public class MyFunctions
    {


        /// <summary>
        /// Function that takes input data in 2D array format calculates a N balance for all the crops specified (up to 3) and returns N balance variables in 2D array format
        /// </summary>
        /// <param name="Tt">Array of daily thermal time over the duration of the rotation</param>
        /// <param name="config">2D aray with parameter names and values for crop field configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyNBalance(double[] tt, object[,] config)
        {
            return NBalance.CalculateSoilNBalance(tt, config);
        }


        /// <summary>
        /// Takes theremal time and config data in 2D array format, calculates variables for a single crop and returns them in a 2D array)
        /// </summary>
        /// <param name="Tt">Array of daily thermal time over the duration of the crop</param>
        /// <param name="Config">2D aray with parameter names and values for crop configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyCropData(double[] Tt, object[,] Config)
        {
            Dictionary<string, object> config = Functions.dictMaker(Config);
            DateTime[] cropDates = Functions.SimDates(config["EstablishDate"], config["HarvestDate"]);
            Dictionary<DateTime, double> tt = Functions.dictMaker(cropDates, Tt);
            Dictionary<DateTime, double> AccTt = Functions.AccumulateTt(cropDates, tt);
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
                    dCropConfig[k] = Constants.UnitConversions[config[k].ToString()];
                }
            }

            return (object[,])CropModel.CalculateOutputs(AccTt, dCropConfig, sCropConfig);
        }
    }
}