using Helper;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SVSModel
{
    /// <summary>
    /// Model to predict mineralisation for previous crop residues
    /// </summary>
    class ResidueMineralisationModel
    {
        public static Dictionary<DateTime, double> CalculateOutputs(DateTime[] simDates, Dictionary<DateTime, double> Tt, Dictionary<string, object> config, Dictionary<string, double> cropProduction)
        {
            int durat = simDates.Length;
            Dictionary<DateTime, double> NResidues = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> PresRoot = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> PresStover = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> PresFieldLoss = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> CresRoot = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> CresStover = Functions.dictMaker(simDates, new double[simDates.Length]);
            Dictionary<DateTime, double> cresFieldLoss = Functions.dictMaker(simDates, new double[simDates.Length]);

            List<Dictionary<DateTime, double>> Residues = new List<Dictionary<DateTime, double>> { PresRoot, PresStover, PresFieldLoss, CresRoot, CresStover, cresFieldLoss };
            foreach (DateTime d in simDates)
            {
                //Decompose residues each day
                foreach (Dictionary<DateTime, double> res in Residues)
                {
                    try { res[d] = res[d.AddDays(-1)]; }
                    catch { res[d] = 0.2; }
                    double mineralisation = res[d] * 0.001 * Tt[d];
                    res[d] -= mineralisation;
                    NResidues[d] += mineralisation;
                }
                //Add residues to system at harvest
                if (d == DateTime.FromOADate((double)config["PriorHarvestDate"]))
                {
                    PresRoot[d] = cropProduction["PriorResRoot"];
                    PresStover[d] = cropProduction["PriorResStover"];
                    PresFieldLoss[d] = cropProduction["PriorResFieldLoss"];
                }
                if (d == DateTime.FromOADate((double)config["CurrentHarvestDate"]))
                {
                    PresRoot[d] = cropProduction["CurrentResRoot"];
                    PresStover[d] = cropProduction["CurrentResStover"];
                    PresFieldLoss[d] = cropProduction["CurrentResFieldLoss"];
                }
            }
            return NResidues;
        }
    }
}
