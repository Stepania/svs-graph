using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using CsvHelper;
using SVSModel.Configuration;
using SVSModel.Models;

namespace SVSModel
{
    public interface IModelInterface
    {
        /// <summary>
        /// 
        /// </summary>
        /// <param name="weatherStation"></param>
        /// <param name="testResults"></param>
        /// <param name="nApplied"></param>
        /// <param name="config"></param>
        /// <returns></returns>
        object[,] GetDailyNBalance(string weatherStation, Dictionary<DateTime, double> testResults, Dictionary<DateTime, double> nApplied, Config config);

        /// <summary>
        /// Gets the crop data from the data file
        /// </summary>
        /// <returns>List of <see cref="InterfaceModels"/>s directly from the data file</returns>
        IEnumerable<CropCoefficient> GetCropCoefficients();

        object[,] GetDailyCropData(double[] Tt, object[,] Config);
    }

    public class ModelInterface : IModelInterface
    {
        public object[,] GetDailyNBalance(string weatherStation, Dictionary<DateTime, double> testResults, Dictionary<DateTime, double> nApplied, Config config)
        {
            var startDate = config.Prior.EstablishDate.AddDays(-1);
            var endDate = config.Following.HarvestDate.AddDays(2);
            var metData = BuildMetDataDictionaries(startDate, endDate, weatherStation);

            return Simulation.SimulateField(metData.MeanT, metData.Rain, metData.MeanPET, testResults, nApplied, config);
        }

        public IEnumerable<CropCoefficient> GetCropCoefficients()
        {
            var assembly = Assembly.GetExecutingAssembly();

            var stream = assembly.GetManifestResourceStream("SVSModel.Data.CropCoefficientTableFull.csv");
            if (stream == null) return Enumerable.Empty<CropCoefficient>();

            using (var reader = new StreamReader(stream, Encoding.UTF8))
            using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
            {
                var cropData = csv.GetRecords<CropCoefficient>();
                return cropData;
            }
        }

        private static IEnumerable<WeatherStationData> GetMetData(string weatherStation)
        {
            var assembly = Assembly.GetExecutingAssembly();

            var stream = assembly.GetManifestResourceStream($"SVSModel.Data.Met.{weatherStation}.csv");
            if (stream == null) return Enumerable.Empty<WeatherStationData>();

            using (var reader = new StreamReader(stream, Encoding.UTF8))
            using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
            {
                var data = csv.GetRecords<WeatherStationData>();
                return data;
            }
        }

        private static MetDataDictionaries BuildMetDataDictionaries(DateTime startDate, DateTime endDate, string weatherStation)
        {
            var metData = GetMetData(weatherStation).ToList();

            var meanT = new Dictionary<DateTime, double>();
            var rain = new Dictionary<DateTime, double>();
            var meanPET = new Dictionary<DateTime, double>();

            var currDate = new DateTime(startDate.Year, startDate.Month, startDate.Day);
            while (currDate < endDate)
            {
                var doy = currDate.DayOfYear;
                var values = metData.FirstOrDefault(m => m.DOY == doy);

                meanT.Add(currDate, values?.MeanT ?? 0);
                rain.Add(currDate, values?.Rain ?? 0);
                meanPET.Add(currDate, values?.MeanPET ?? 0);

                currDate = currDate.AddDays(1);
            }

            return new MetDataDictionaries { MeanT = meanT, Rain = rain, MeanPET = meanPET };
        }

        /// <summary>
        /// Takes daily mean temperature 2D array format with date in the first column, calculates variables for a single crop and returns them in a 2D array)
        /// </summary>
        /// <param name="Tt">Array of daily thermal time over the duration of the crop</param>
        /// <param name="Config">2D aray with parameter names and values for crop configuration parameters</param>
        /// <returns>Dictionary with parameter names as keys and parameter values as values</returns>
        public object[,] GetDailyCropData(double[] Tt, object[,] Config)
        {
            Dictionary<string, object> c = Functions.dictMaker(Config);
            CropConfig config = new CropConfig(c, "Current");
            DateTime[] cropDates = Functions.DateSeries(config.EstablishDate, config.HarvestDate);
            Dictionary<DateTime, double> tt = Functions.dictMaker(cropDates, Tt);
            Dictionary<DateTime, double> AccTt = Functions.AccumulateTt(cropDates, tt);
            return Crop.Grow(AccTt, config);
        }
    }
}
