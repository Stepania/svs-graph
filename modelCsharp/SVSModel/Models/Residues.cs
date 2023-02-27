using Helper;
using System;
using System.Collections.Generic;
using System.Linq;

namespace SVSModel
{
    class Residues
    {
        /// <summary>
        /// Calculates the daily nitrogen mineralised as a result of residue decomposition
        /// </summary>
        /// <param name="meanT">A date indexed dictionary of daily mean temperatures</param>
        /// <param name="rswc">A date indexed dictionary of daily releative soil water content</param>
        /// <returns>Date indexed series of daily N mineralised from residues</returns>
        public static Dictionary<DateTime, double> Mineralisation(Dictionary<DateTime,double> rswc, 
                                                                  Dictionary<DateTime, double> meanT)
        {
            DateTime[] simDates = rswc.Keys.ToArray();
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
                    double mineralisation = res[d] * 0.012 * meanT[d] * rswc[d];
                    res[d] -= mineralisation;
                    NResidues[d] += mineralisation;
                }
                //Add residues to system at harvest
                if (d == Config.Prior.HarvestDate)
                {
                    PresRoot[d] = Config.Prior.ResRoot;
                    PresStover[d] = Config.Prior.ResStover;
                    PresFieldLoss[d] = Config.Prior.FieldLoss;
                }
                if (d == Config.Current.HarvestDate)
                {
                    PresRoot[d] = Config.Current.ResRoot;
                    PresStover[d] = Config.Current.ResStover;
                    PresFieldLoss[d] = Config.Current.ResFieldLoss;
                }
            }
            return NResidues;
        }
    }
}
