using Helper;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SVSModel
{
    class MineralN
    {
        public static Dictionary<DateTime, double> CalculateOutputs(DateTime[] simDates, double initialN, Dictionary<DateTime, double> uptake, Dictionary<DateTime, double> residue)
        {
            Dictionary<DateTime, double> minN = Functions.dictMaker(simDates, new double[simDates.Length]);

            foreach (DateTime d in simDates)
            {
                try { minN[d] = minN[d.AddDays(-1)]; }
                catch { minN[simDates[0]] = initialN; }
                minN[d] += residue[d];
                minN[d] -= uptake[d];
            }
            return minN;
        }
    }
}
