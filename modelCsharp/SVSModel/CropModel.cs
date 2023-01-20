using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Helper;
using Microsoft.Data.Analysis;

namespace SVSModel
{
    public class CropModel
    {
        /// <summary>
        /// Returns daily N uptake over the duration of the Tt input data for Root, Stover, Product and loss N as well as cover and root depth
        /// </summary>
        /// <param name="Tt">An array containing the accumulated thermal time for the duration of the crop</param>
        /// <param name="sConfig">A dictionary containing configuration information such as crop type and harvest stage</param>
        /// <param name="Params"></param>
        /// <returns>A 2D array of crop model outputs</returns>
        public static object CalculateCropOutputs(double[] Tt, Dictionary<string, double> dConfig, Dictionary<string,object> sConfig, bool fullOutput =false)
        {
            DateTime[] cropDates = Functions.SimDates(dConfig["EstablishDate"],dConfig["HarvestDate"]);
            int durat = cropDates.Length;
            DataFrame data = DataFrame.LoadCsv("C:\\GitHubRepos\\SVS\\modelCsharp\\SVSModel\\CropCoefficientTable.csv");

            Dictionary<string, double> Params = new Dictionary<string, double>();

            int rowCount = (int)data.Rows.Count;
            for (int r = 1;r<rowCount;r++)
            {
                Params.Add(data["Key"][r].ToString(),Double.Parse(data[(string)sConfig["CropName"]][r].ToString()));
            }

            // Derive Crop Parameters
            double Tt_Harv = Tt.Last();
            double Tt_estab = Tt_Harv * (Constants.PropnTt[sConfig["EstablishStage"].ToString()] / Constants.PropnTt[sConfig["HarvestStage"].ToString()]);
            double Xo_Biomass = (Tt_Harv + Tt_estab) * .45 * (1 / Constants.PropnTt[sConfig["HarvestStage"].ToString()]);
            double b_Biomass = Xo_Biomass * .25;
            double T_mat = Xo_Biomass * 2.2222;
            double T_maxRD = Constants.PropnTt["EarlyReproductive"] * T_mat;
            double T_sen = Constants.PropnTt["MidReproductive"] * T_mat;
            double Xo_cov = Xo_Biomass * 0.4 / Params["rCover"];
            double b_cov = Xo_cov * 0.2;
            double a_harvestIndex = Params["Typical HI"] - Params["HI Range"];
            double b_harvestIndex = Params["HI Range"] / Params["Typical Yield"];
            double stageCorrection = 1 / Constants.PropnMaxDM[sConfig["HarvestStage"].ToString()];

            // derive crop Harvest State Variables 
            double fSaleableYieldDwt = Double.Parse(dConfig["SaleableYield"].ToString());
            double fFieldLossPct = dConfig["FieldLoss"];
            double fFreshTotalProductWt = fSaleableYieldDwt * (1 / (1 - fFieldLossPct / 100)) * (1 / (1 - dConfig["DressingLoss"] / 100));
                  // Crop Failure.  If yield is very low or field loss is very high assume complete crop failure.  Uptake equation are too sensitive saleable yields close to zero and field losses close to 100
            if (((dConfig["SaleableYield"] * dConfig["Units"]) < (Params["Typical Yield"] * 0.05)) || (dConfig["FieldLoss"] > 95))
            {
                fFieldLossPct = 100;
                fFreshTotalProductWt = Params["Typical Yield"] * (1 / (1 - Params["Typical Dressing Loss %"] / 100));
            }
            double fTotalProductDwt = fFreshTotalProductWt * dConfig["Units"] * (1 - dConfig["MoistureContent"] / 100);
            double fFieldLossDwt = fTotalProductDwt * fFieldLossPct / 100;
            double fFieldLossN = fFieldLossDwt * Params["Product [N]"] / 100;
            double fDressingLossDwt = fTotalProductDwt * dConfig["DressingLoss"] / 100;
            double fDressingLossN = fDressingLossDwt * Params["Product [N]"] / 100;
            double fSaleableProductDwt = fTotalProductDwt - fFieldLossDwt - fDressingLossDwt;
            double fSaleableProductN = fSaleableProductDwt * Params["Product [N]"] / 100;
            double HI = a_harvestIndex + fFreshTotalProductWt * b_harvestIndex;
            double fStoverDwt = fTotalProductDwt * 1 / HI - fTotalProductDwt;
            double fStoverN = fStoverDwt * Params["Stover [N]"] / 100;
            double fRootDwt = (fStoverDwt + fTotalProductDwt) * Params["P Root"];
            double fRootN = fRootDwt * Params["Root [N]"] / 100;
            double fCropN = fRootN + fStoverN + fFieldLossN + fDressingLossN + fSaleableProductN;
                        
            //Daily time-step, calculate Daily Scallers to give in crop patterns
            double[] biomassScaller = new double[durat];
            double[] coverScaller = new double[durat];
            double[] rootDepthScaller = new double[durat];
            for (int d = 0; d < durat; d++)
            {
                biomassScaller[d] = (1 / (1 + Math.Exp(-((Tt[d] - Xo_Biomass) / (b_Biomass)))));
                if (Tt[d] < T_maxRD)
                    rootDepthScaller[d] = Tt[d] / T_maxRD;
                else
                    rootDepthScaller[d] = 1;
                if (Tt[d] < T_sen)
                    coverScaller[d] = 1 / (1 + Math.Exp(-((Tt[d] - Xo_cov) / b_cov)));
                else
                    coverScaller[d] = Math.Max(0, (1 - (Tt[d] - T_sen) / (T_mat - T_sen)));
            }

            // Multiply Harvest State Variables by Daily Scallers to give Daily State Variables
            double[] RootN = Functions.scaledValues(biomassScaller, fRootN, stageCorrection);
            double[] StoverN = Functions.scaledValues(biomassScaller, fStoverN, stageCorrection);
            double[] SaleableProductN = Functions.scaledValues(biomassScaller, fSaleableProductN, stageCorrection);
            double[] FieldLossN = Functions.scaledValues(biomassScaller, fFieldLossN, stageCorrection);
            double[] DressingLossN = Functions.scaledValues(biomassScaller, fDressingLossN, stageCorrection);
            double[] TotalCropN = Functions.scaledValues(biomassScaller, fCropN, stageCorrection);
            double[] CropUptakeN = Functions.calcDelta(TotalCropN);
            double[] Cover = Functions.scaledValues(coverScaller, (double)Params["A cover"], 1.0);
            double[] RootDepth = Functions.scaledValues(rootDepthScaller, (double)Params["Max RD"], 1.0);

            if (fullOutput)
            {
                // Pack Daily State Variables into a 2D array so they can be output
                object[,] ret = new object[durat + 1, 10];
                ret[0, 0] = "Date"; Functions.packRows(0, cropDates, ref ret);
                ret[0, 1] = "RootN"; Functions.packRows(1, RootN, ref ret);
                ret[0, 2] = "StoverN"; Functions.packRows(2, StoverN, ref ret);
                ret[0, 3] = "SaleableProductN"; Functions.packRows(3, SaleableProductN, ref ret);
                ret[0, 4] = "FieldLossN"; Functions.packRows(4, FieldLossN, ref ret);
                ret[0, 5] = "DressingLossN"; Functions.packRows(5, DressingLossN, ref ret);
                ret[0, 6] = "TotalCropN"; Functions.packRows(6, TotalCropN, ref ret);
                ret[0, 7] = "CropUptakeN"; Functions.packRows(7, CropUptakeN, ref ret);
                ret[0, 8] = "Cover"; Functions.packRows(8, Cover, ref ret);
                ret[0, 9] = "RootDepth"; Functions.packRows(9, RootDepth, ref ret);
                return ret;
            }
            else
            {
                Dictionary <DateTime,double> ret = new Dictionary<DateTime, double>();
                ret = Functions.dictMaker(cropDates,CropUptakeN);
                return ret;
            }
        }
    }
}

