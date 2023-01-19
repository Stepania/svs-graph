using ExcelDna.Integration;
using GenericParsing;
using Microsoft.Data.Analysis;
using System;
using System.Collections.Generic;
using System.Data;
using SVSModel;

namespace Helper
{
    public class MyFunctions
    {
        [ExcelFunction(Description = "My first .NET function")]
        public static double SumArray(double[] tempData)
        {
            double sum = 0;
            for (int i = 0; i < tempData.Length; i++)
                sum += tempData[i];
            return sum;
        }

        public static double[] MultiplyMembers(double[] tempData, double factor)
        {
            for (int i = 0; i < tempData.Length; i++)
                tempData[i] *= factor;
            return tempData;
        }

        public static object[,] GetDailyCropData(double[] Tt, object[,] Config, object[,] Params)
        {
            Dictionary<string, object> config = Functions.dictMaker(Config);
            
            Dictionary<string, object> _params = Functions.dictMaker(Params);

            return CropModel.CalculateCropOutputs(Tt, config, _params);
        }


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