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
        public static double[] AccumulateTt(double[] Tt)
        {
            double[] tt = new double[Tt.Length];
            tt[0] = Tt[0];
            for (int d = 1; d < Tt.Length; d++)
                tt[d] = tt[d - 1] + Tt[d];
            return tt;
        }

        /// <summary>
        /// Function that takes input data in 2D array format and packs in into a dictionary for use in model
        /// </summary>
        /// <param name="Tt">Array of accumulated thermal time over the duration of the crop</param>
        /// <param name="Config">2D aray with parameter names and values for field configuration parameters</param>
        /// <param name="Params">2D aray with parameter names and values for crop specific parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public static object[,] GetDailyCropData(double[] Tt, object[,] Config, object[,] Params)
        {
            Dictionary<string, object> config = Functions.dictMaker(Config);
            
            Dictionary<string, object> _params = Functions.dictMaker(Params);

            return CropModel.CalculateCropOutputs(AccumulateTt(Tt), config, _params);
        }
    }
}