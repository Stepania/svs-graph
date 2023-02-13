using Helper;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace SVSModel
{
    class SoilWater
    {
        /// <summary>
        /// Calculates the soil water content and leaching risk daily leaching risk
        /// </summary>
        /// <param name="simDates">series of dates over the duration of the simulation</param>
        /// <param name="meanT">A date indexed dictionary of daily mean temperatures</param>
        /// <param name="config">A specific class that holds all the simulation configuration data in the correct types for use in the model</param>
        /// <returns>Date indexed series of daily N mineralised from residues</returns>
        public static void Balance(ref Dictionary<DateTime, double> RSWC,
                                   ref Dictionary<DateTime, double> Drainage,
                                   ref Dictionary<DateTime, double> Irrigation,
                                   Dictionary<DateTime, double> meanRain, 
                                   Dictionary<DateTime, double> meanPET, 
                                   Dictionary<DateTime, double> cover, 
                                   Config config)
        {
            DateTime[] simDates = RSWC.Keys.ToArray();
            Dictionary<DateTime, double> SWC = Functions.dictMaker(simDates, new double[simDates.Length]);
            double dul = config.field.AWC;
            foreach (DateTime d in simDates)
            {
                if (d == simDates[0])
                {
                    SWC[simDates[0]] = dul * config.field.PrePlantRainFactor;
                    RSWC[simDates[0]] = SWC[simDates[0]] / dul;
                }
                else
                {
                    DateTime yest = d.AddDays(-1);
                    double T = Math.Min(SWC[yest] * 0.1, meanPET[d] * cover[d]);
                    double E = meanPET[d] * (1 - cover[d]) * RSWC[yest];
                    SWC[d] = SWC[yest] + meanRain[d] - T - E;
                    if (SWC[d]>dul)
                    {
                        Drainage[d] = SWC[d] - dul;
                        SWC[d] = dul;
                    }
                    else
                    {
                        Drainage[d] = 0.0;
                        if (SWC[d]/dul < config.field.IrrigationTrigger)
                        {
                            double apply = dul * (config.field.IrrigationRefill - config.field.IrrigationTrigger);
                            SWC[d] += apply;
                            Irrigation[d] = apply;
                        }
                    }
                }
                RSWC[d] = SWC[d] / dul;
            }
        }
    }
}
