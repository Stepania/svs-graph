using System;
using System.Collections.Generic;

namespace Helper
{
    public class Functions
    {
        /// <summary>
        /// calculates the difference between daily values in an array
        /// </summary>
        /// <param name="integral">array of values to be differentiated to give delta</param>
        /// <returns>An array of deltas</returns>
        public static double[] calcDelta(double[] integral)
        {
            double prior = integral[0];
            double[] delta = new double[integral.Length];
            delta[0] = 0;
            for (int i = 1; i < integral.Length; i++)
            {
                delta[i] = integral[i] - prior;
                prior = integral[i];
            }
            return delta;
        }

        /// <summary>
        /// Function to convert a 2D array with a row of keys and a row of values into a dictionary
        /// </summary>
        /// <param name="arr">2D arry to be converted</param>
        /// <returns>dictionary converted from arr</returns>
        public static Dictionary<string, object> dictMaker(object[,] arr)
        {
            Dictionary<string, object> dict = new Dictionary<string, object>();
            int Nrows = arr.GetLength(0);
            for (int r = 0; r < Nrows; r++)
            {
                dict.Add(arr[r, 0].ToString(), arr[r, 1]);
            }
            return dict;
        }

        /// <summary>
        /// Function to convert a 2D array with a row of date keys and a row of values into a dictionary
        /// </summary>
        /// <param name="date">An array of DateTimes</param>
        /// <param name="values">An array of doubles</param>
        /// <returns>dictionary converted from arr</returns>
        public static Dictionary<DateTime, double> dictMaker(DateTime[] date, double[] values)
        {
            Dictionary<DateTime, double> dict = new Dictionary<DateTime, double>();
            for (int r = 0; r < date.Length; r++)
            {
                dict.Add(date[r], values[r]);
            }
            return dict;
        }
        
        /// <summary>
        /// Function that packs an array of variables into a specified column in a 2D array
        /// </summary>
        /// <param name="colInd">Name of the column to be packed</param>
        /// <param name="column">index position of the column</param>
        /// <param name="df">the 2D array that the column is to be packed into</param>
        public static void packRows(int colInd, double[] column, ref object[,] df)
        {
            for (int currentRow = 0; currentRow < column.Length; currentRow++)
            {
                df[currentRow + 1, colInd] = column[currentRow];
            }
        }
        
        /// <summary>
        /// Takes an array of daily scaller values (0-1) and multiplies them by the final value to give Daily State Variable values 
        /// </summary>
        /// <param name="scaller">2D array of daily values for 0-1 scaller</param>
        /// <param name="final">The Daily State Variable value on the last day of the simulation</param>
        /// <param name="correction">A factor to apply Stage of harvest correction</param>
        /// <returns>An array of Daily State Variables for the model</returns>
        public static double[] scaledValues(double[] scaller, double final, double correction)
        {
            double[] sv = new double[scaller.Length];
            for (int d = 0; d < sv.Length; d++)
                sv[d] = scaller[d] * final * correction;
            return sv;
        }

        /// <summary>
        /// Creates an array of dates for the duration of the simulation
        /// </summary>
        /// <param name="start">Date to start series</param>
        /// <param name="end">Date to end series</param>
        /// <returns>a continious array of dates between the start and end specified</returns>
        public static DateTime[] SimDates(DateTime start, DateTime end)
        {
            List<DateTime> ret = new List<DateTime>();
            for (DateTime d = start; d < end; d = d.AddDays(1))
                ret.Add(d);
            return ret.ToArray();
        }
    }
}
