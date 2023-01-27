using Microsoft.Data.Analysis;
using SVSModel;
using System.Collections.Generic;

namespace Helper
{
    public class MyFunctions
    {
        /// <summary>
        /// Returns an accumulation of Thermal time over the duration of the dialy input values
        /// </summary>
        /// <param name="Tt">array of daily average temperatures</param>
        /// <returns>Array of accumulated thermal time</returns>
        public static double[] AccumulateTtt(double[] Tt)
        {
            double[] tt = new double[Tt.Length];
            tt[0] = Tt[0];
            for (int d = 1; d < Tt.Length; d++)
                tt[d] = tt[d - 1] + Tt[d];
            return tt;
        }

        /// <summary>
        /// Function that takes input data in 2D array format calculates a N balance for all the crops specified (up to 3) and returns N balance variables in 2D array format
        /// </summary>
        /// <param name="Tt">Array of accumulated thermal time over the duration of the crop</param>
        /// <param name="config">2D aray with parameter names and values for crop configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyNBalance(double[] Tt, object[,] Config)
        {
            Dictionary<string, object> config = Functions.dictMaker(Config);

            return NBalance.CalculateSoilNBalance(Tt, config);
        }


        /// <summary>
        /// Takes theremal time and config data in 2D array format, calculates variables for a single crop and returns them in a 2D array)
        /// </summary>
        /// <param name="Tt">Array of accumulated thermal time over the duration of the crop</param>
        /// <param name="Config">2D aray with parameter names and values for crop configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyCropData(double[] Tt, object[,] Config)
        {
            Dictionary<string, object> config = Functions.dictMaker(Config);

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

            return (object[,])CropModel.CalculateOutputs(AccumulateTtt(Tt), dCropConfig, sCropConfig);
        }
    }
}