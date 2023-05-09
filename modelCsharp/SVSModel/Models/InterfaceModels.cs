using System;
using System.Collections.Generic;

namespace SVSModel.Models
{
    public class CropCoefficient
    {
        public string UniqueName { get; set; }
        public int Index { get; set; }
        public string EndUse { get; set; }
        public string Group { get; set; }
        public string ColloquialName { get; set; }
        public string Type { get; set; }
        public string Family { get; set; }
        public string Genus { get; set; }
        public string SpecificEpithet { get; set; }
        public string SubSpecies { get; set; }
        public string SpeciesName { get; set; }
        public string EpithetAndSubSpecies { get; set; }
        public string TypicalEstablishStage { get; set; }
        public string TypicalEstablishMonth { get; set; }
        public string TypicalHarvestStage { get; set; }
        public string TypicalHarvestMonth { get; set; }
        public double TypicalYield { get; set; }
        public string TypicalYieldUnits { get; set; }
        public string YieldType { get; set; }
        public double TypicalPopulationPerHa { get; set; }
        public string TotalOrDry { get; set; }
        public double TypicalDressingLossPercent { get; set; }
        public double TypicalFieldLossPercent { get; set; }
        public double TypicalHI { get; set; }
        public double HIRange { get; set; }
        public double MoisturePercent { get; set; }
        public double PRoot { get; set; }
        public double MaxRD { get; set; }
        public double ACover { get; set; }
        public double RCover { get; set; }
        public double RootN { get; set; }
        public double StOverN { get; set; }
        public double ProductN { get; set; }
    }

    public class WeatherStationData
    {
        public int DOY { get; set; }
        public double MeanT { get; set; }
        public double Rain { get; set; }
        public double MeanPET { get; set; }
    }

    public class MetDataDictionaries
    {
        public Dictionary<DateTime, double> MeanT { get; set; }
        public Dictionary<DateTime, double> Rain { get; set; }
        public Dictionary<DateTime, double> MeanPET { get; set; }
    }
}
