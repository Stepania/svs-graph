using Helper;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SVSModel
{
    class ResidueMineralisationModel
    {
        /// <summary>
        /// Calculates the daily nitrogen mineralised as a result of residue decomposition
        /// </summary>
        /// <param name="simDates">series of dates over the duration of the simulation</param>
        /// <param name="meanT">A date indexed dictionary of daily mean temperatures</param>
        /// <param name="config">A specific class that holds all the simulation configuration data in the correct types for use in the model</param>
        /// <returns>Date indexed series of daily N mineralised from residues</returns>
        public static Dictionary<DateTime, double> CalculateOutputs(DateTime[] simDates, Dictionary<DateTime, double> meanT, Config config)
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
                    if (d == simDates[0])
                    {
                        res[d] = 0.2;
                    }
                    else
                    {
                        res[d] = res[d.AddDays(-1)];
                    }
                    double mineralisation = res[d] * 0.001 * meanT[d];
                    res[d] -= mineralisation;
                    NResidues[d] += mineralisation;
                }
                //Add residues to system at harvest
                if (d == config.Prior.HarvestDate)
                {
                    PresRoot[d] = config.Prior.ResRoot;
                    PresStover[d] = config.Prior.ResStover;
                    PresFieldLoss[d] = config.Prior.FieldLoss;
                }
                if (d == config.Current.HarvestDate)
                {
                    PresRoot[d] = config.Current.ResRoot;
                    PresStover[d] = config.Current.ResStover;
                    PresFieldLoss[d] = config.Current.ResFieldLoss;
                }
            }
            return NResidues;
        }
    }
}
