using Helper;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SVSModel
{
    class MineralNCalculations
    {
        public static Dictionary<DateTime, double> Initial(DateTime[] simDates, double initialN, Dictionary<DateTime, double> uptake,
                                                                    Dictionary<DateTime, double> residue, Dictionary<DateTime, double> som)
        {
            Dictionary<DateTime, double> minN = Functions.dictMaker(simDates, new double[simDates.Length]);

            foreach (DateTime d in simDates)
            {
                try { minN[d] = minN[d.AddDays(-1)]; }
                catch { minN[simDates[0]] = initialN; }
                minN[d] += residue[d];
                minN[d] += som[d];
                minN[d] -= uptake[d];
            }
            return minN;
        }

        public static void TestCorrection(Dictionary<DateTime, double> testResults, ref Dictionary<DateTime, double> soilN)
        {
            foreach (DateTime d in testResults.Keys)
            {
                double correction = soilN[d] - testResults[d];
                DateTime[] simDatesToCorrect = Functions.SimDates(d, soilN.Keys.Last());
                foreach (DateTime c in simDatesToCorrect)
                {
                    soilN[c] += correction;
                }
            }

        }

        public static Dictionary<DateTime, double> DetermineFertRequirements(ref Dictionary<DateTime, double> soilN, Dictionary<DateTime, double> residueMin, 
                                                                             Dictionary<DateTime, double> somN, Dictionary<DateTime, double> cropN,
                                                                             Dictionary<DateTime, double> testResults, Config config)
        {
            
            Dictionary<DateTime, double> fert = Functions.dictMaker(soilN.Keys.ToArray(), new double[soilN.Keys.Count()]);
            DateTime[] cropDates = Functions.SimDates(config.Current.EstablishDate, config.Current.HarvestDate);
            DateTime startSchedulleDate = config.Current.EstablishDate;
            if (testResults.Keys.Count() < 0)
                startSchedulleDate = testResults.Keys.Last();
            DateTime[] schedullingDates = Functions.SimDates(startSchedulleDate, config.Current.HarvestDate);
            //Apply Planting N
            fert[config.Current.EstablishDate] = config.field.EstablishFertN;
            AddFertiliser(ref soilN, config.field.EstablishFertN, config.Current.EstablishDate, config);
            //Calculate further N requirements
            double mineralisation = 0;
            foreach (DateTime d in cropDates)
            {
                mineralisation += residueMin[d];
                mineralisation += somN[d];
            }
            double CropN = cropN[startSchedulleDate] - cropN[config.Current.HarvestDate];
            double trigger = config.field.Trigger;
            double NFertReq = (CropN + trigger) - soilN[config.Current.EstablishDate] - mineralisation;
            double efficiency = config.field.Efficiency;
            NFertReq = NFertReq * 1 / efficiency;
            int splits = config.field.Splits;
            double NAppn = Math.Ceiling(NFertReq / splits);
            double FertApplied = 0;
            int FertAppNo = 0;
            if (splits > 0)
            {
                foreach (DateTime d in schedullingDates)
                {
                    if ((soilN[d] < trigger) && (FertApplied < NFertReq))
                    {
                        AddFertiliser(ref soilN, NAppn * efficiency, d, config);
                        fert[d] = NAppn;
                        FertApplied += NAppn;
                    }
                }
            }
            return fert;
        }

        public static void AddFertiliser(ref Dictionary<DateTime, double> soilN, double fertN, DateTime fertDate, Config config)
        {
            DateTime[] datesFollowingFert = Functions.SimDates(fertDate, config.Following.HarvestDate);
            foreach (DateTime d in datesFollowingFert)
            {
                soilN[d] += fertN;
            }
         }

    }
}
