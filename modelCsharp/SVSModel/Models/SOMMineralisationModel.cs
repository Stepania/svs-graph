using Helper;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SVSModel
{
    /// <summary>
    /// Model to predict daily N mineralisatin from soil organic matter
    /// </summary>
    class SOMMineralisationModel
    {
        public static Dictionary<DateTime, double> CalculateOutputs(DateTime[] simDates, Dictionary<DateTime, double> Tt, Config config)
        {
            int durat = simDates.Length;
            double hweon = config.field.HWEON;
            double swf = 1.0;
            double mrc = 0.005;

            Dictionary<DateTime, double> NSoilOM = Functions.dictMaker(simDates,new double[durat]);
            foreach (DateTime d in simDates)
            {
                double somMin = hweon* Tt[d] *swf * mrc;
                NSoilOM[d] = somMin;
            }
            return NSoilOM;
        }
    }
}
