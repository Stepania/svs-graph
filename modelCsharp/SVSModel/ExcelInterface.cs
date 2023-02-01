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
        public static object[,] GetDailyNBalance(double[] tt, object[,] config, object[,] testResults)
        {
            return NBalance.CalculateSoilNBalance(tt, config, testResults);
        }


        /// <summary>
        /// Takes theremal time and config data in 2D array format, calculates variables for a single crop and returns them in a 2D array)
        /// </summary>
        /// <param name="Tt">Array of daily thermal time over the duration of the crop</param>
        /// <param name="Config">2D aray with parameter names and values for crop configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyCropData(double[] Tt, object[,] Config)
        {
            Dictionary<string, object> c = Functions.dictMaker(Config);
            Crop config = new Crop(c,"Current");
            DateTime[] cropDates = Functions.SimDates(config.EstablishDate, config.HarvestDate);
            Dictionary<DateTime, double> tt = Functions.dictMaker(cropDates, Tt);
            Dictionary<DateTime, double> AccTt = Functions.AccumulateTt(cropDates, tt);
            return (object[,])CropModel.CalculateOutputs(AccTt, config);
        }
    }
}