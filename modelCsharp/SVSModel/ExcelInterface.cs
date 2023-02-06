using Microsoft.Data.Analysis;
using SVSModel;
using System;
using System.Collections.Generic;

namespace Helper
{
    public class MyFunctions
    {


        /// <summary>
        /// Function that takes input data in 2D array format and calculates a N balance for a 3 crops rotation and returns N balance variables in 2D array format
        /// </summary>
        /// <param name="meanT">2D Array with dates in first column and daily mean temperature over the duration of the rotation in the second column</param>
        /// <param name="config">2D aray with parameter names and values for crop field configuration parameters</param>
        /// <param name="testResults">2D aray with parameter names and values for crop field configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyNBalance(object[,] meanT, object[,] config, object[,] testResults, object[,] nApplied)
        {
            Dictionary<DateTime, double> _tt = Functions.dictMaker(meanT, "MeanT");
            Config _config = new Config(config);
            Dictionary<DateTime, double> _testResults = Functions.dictMaker(testResults, "Value");
            Dictionary<DateTime, double> _nApplied = Functions.dictMaker(nApplied, "Amount");
            return NBalance.CalculateSoilNBalance(_tt, _config, _testResults, _nApplied);
        }


        /// <summary>
        /// Takes daily mean temperature 2D array format with date in the first column, calculates variables for a single crop and returns them in a 2D array)
        /// </summary>
        /// <param name="Tt">Array of daily thermal time over the duration of the crop</param>
        /// <param name="Config">2D aray with parameter names and values for crop configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyCropData(double[] Tt, object[,] Config)
        {
            Dictionary<string, object> c = Functions.dictMaker(Config);
            Crop config = new Crop(c, "Current");
            DateTime[] cropDates = Functions.DateSeries(config.EstablishDate, config.HarvestDate);
            Dictionary<DateTime, double> tt = Functions.dictMaker(cropDates, Tt);
            Dictionary<DateTime, double> AccTt = Functions.AccumulateTt(cropDates, tt);
            return CropModel.CalculateOutputs(AccTt, config);
        }


    }
}