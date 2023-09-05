using SVSModel;
using SVSModel.Configuration;
using SVSModel.Models;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace ConsoleApp1
{
    public class Class1
    {
        public static void testConfig(Dictionary<string, object> _configDict)

        {

            Config _config = new Config(_configDict);

            Dictionary<DateTime, double> testResults = new Dictionary<DateTime, double>();
            Dictionary<DateTime, double> nApplied = new Dictionary<DateTime, double>();

            MetDataDictionaries metData = ModelInterface.BuildMetDataDictionaries(_config.Prior.EstablishDate, _config.Following.HarvestDate, "Ashburton");

            object[,] output = Simulation.SimulateField(metData.MeanT, metData.Rain, metData.MeanPET, testResults, nApplied, _config);

            //as a try?
            string jsonConfig = JsonSerializer.Serialize(output);
            Trace.WriteLine("wwwI am here");

        }
        

    }
}
