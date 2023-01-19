using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Helper
{
    public class Functions
    {
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
        public static void packRows(int colInd, double[] column, ref object[,] df)
        {
            for (int currentRow = 0; currentRow < column.Length; currentRow++)
            {
                df[currentRow + 1, colInd] = column[currentRow];
            }
        }
    }
}
