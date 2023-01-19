using System;
using System.Collections.Generic;
using System.Linq;
using Helper;

namespace SVSModel
{
    public class CropModel
    {
        /// <summary>
        /// Returns daily N uptake over the duration of the Tt input data for Root, Stover, Product and loss N as well as cover and root depth
        /// </summary>
        /// <param name="Tt">An array containing the accumulated thermal time for the duration of the crop</param>
        /// <param name="Config">A dictionary containing configuration information such as crop type and harvest stage</param>
        /// <param name="Params"></param>
        /// <returns>A 2D array of crop model outputs</returns>
        public static object[,] CalculateCropOutputs(double[] Tt, Dictionary<string, object> Config, Dictionary<string, object> Params)
        {
            int durat = Tt.Length;
            // Derive Crop Parameters
            double Tt_Harv = Tt.Last();
            double Tt_estab = Tt_Harv * (Constants.PropnTt[Config["EstablishStage"].ToString()] / Constants.PropnTt[Config["HarvestStage"].ToString()]);
            double Xo_Biomass = (Tt_Harv + Tt_estab) * .45 * (1 / Constants.PropnTt[Config["HarvestStage"].ToString()]);
            double b_Biomass = Xo_Biomass * .25;
            double T_mat = Xo_Biomass * 2.2222;
            double T_maxRD = Constants.PropnTt["EarlyReproductive"] * T_mat;
            double T_sen = Constants.PropnTt["MidReproductive"] * T_mat;
            double Xo_cov = Xo_Biomass * 0.4 / (double)Params["rCover"];
            double b_cov = Xo_cov * 0.2;
            double a_harvestIndex = (double)Params["Typical HI"] - (double)Params["HI Range"];
            double b_harvestIndex = (double)Params["HI Range"] / (double)Params["Typical Yield"];
            double stageCorrection = 1 / Constants.PropnMaxDM[Config["HarvestStage"].ToString()];

            // derive crop Harvest State Variables 
            double fSaleableYieldDwt = (double)Config["SaleableYield"];
            double fFieldLossPct = (double)Config["FieldLoss"];
            double fFreshTotalProductWt = fSaleableYieldDwt * (1 / (1 - fFieldLossPct / 100)) * (1 / (1 - (double)Config["DressingLoss"] / 100));
                  // Crop Failure.  If yield is very low or field loss is very high assume complete crop failure.  Uptake equation are too sensitive saleable yields close to zero and field losses close to 100
            if ((((double)Config["SaleableYield"] * (double)Config["Units"]) < ((double)Params["Typical Yield"] * 0.05)) || ((double)Config["FieldLoss"] > 95))
            {
                fFieldLossPct = 100;
                fFreshTotalProductWt = (double)Params["Typical Yield"] * (1 / (1 - (double)Params["Typical Dressing Loss %"] / 100));
            }
            double fTotalProductDwt = fFreshTotalProductWt * (double)Config["Units"] * (1 - (double)Config["MoistureContent"] / 100);
            double fFieldLossDwt = fTotalProductDwt * fFieldLossPct / 100;
            double fFieldLossN = fFieldLossDwt * (double)Params["Product [N]"] / 100;
            double fDressingLossDwt = fTotalProductDwt * (double)Config["DressingLoss"] / 100;
            double fDressingLossN = fDressingLossDwt * (double)Params["Product [N]"] / 100;
            double fSaleableProductDwt = fTotalProductDwt - fFieldLossDwt - fDressingLossDwt;
            double fSaleableProductN = fSaleableProductDwt * (double)Params["Product [N]"] / 100;
            double HI = a_harvestIndex + fFreshTotalProductWt * b_harvestIndex;
            double fStoverDwt = fTotalProductDwt * 1 / HI - fTotalProductDwt;
            double fStoverN = fStoverDwt * (double)Params["Stover [N]"] / 100;
            double fRootDwt = (fStoverDwt + fTotalProductDwt) * (double)Params["P Root"];
            double fRootN = fRootDwt * (double)Params["Root [N]"] / 100;
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

            // Pack Daily State Variables into a 2D array so they can be output
            object[,] ret = new object[durat + 1, 9];
            ret[0, 0] = "RootN"; Functions.packRows(0, RootN, ref ret);
            ret[0, 1] = "StoverN"; Functions.packRows(1, StoverN, ref ret);
            ret[0, 2] = "SaleableProductN"; Functions.packRows(2, SaleableProductN, ref ret);
            ret[0, 3] = "FieldLossN"; Functions.packRows(3, FieldLossN, ref ret);
            ret[0, 4] = "DressingLossN"; Functions.packRows(4, DressingLossN, ref ret);
            ret[0, 5] = "TotalCropN"; Functions.packRows(5, TotalCropN, ref ret);
            ret[0, 6] = "CropUptakeN"; Functions.packRows(6, CropUptakeN, ref ret);
            ret[0, 7] = "Cover"; Functions.packRows(7, Cover, ref ret);
            ret[0, 8] = "RootDepth"; Functions.packRows(8, RootDepth, ref ret);

            return ret;
        }
    }
}

