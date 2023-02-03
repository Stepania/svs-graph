using System;
using ExcelDna.Integration;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Data.Analysis;

namespace Helper
{
    class Meterological
    {
        /// <summary>
        /// Not currently used in model, meanT data is passed in and is not doing water balance yet so not needed.
        /// </summary>
        /// <param name="Start"></param>
        /// <param name="End"></param>
        /// <param name="Met"></param>
        /// <returns></returns>
        public static object[,] TestCSharpReturn()
        {
            //return Met;

            DataFrame data = DataFrame.LoadCsv("C:\\GitHubRepos\\Weather\\Broadfields\\LincolnCSV.met");

            int rowCount = (int)data.Rows.Count;
            int columnCount = (int)data.Columns.Count;
            object[,] ret = new object[rowCount + 1, columnCount];
            for (int currentColumn = 0; currentColumn < columnCount; currentColumn++)
            {
                ret[0, currentColumn] = data.Columns[currentColumn].Name;
                for (int currentRow = 0; currentRow < rowCount; currentRow++)
                {
                    ret[currentRow + 1, currentColumn] = data.Rows[currentRow][currentColumn];
                }
            }
            return ret;
        }
    }
}
