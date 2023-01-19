using Microsoft.Data.Analysis;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Helper;
using static System.Math;

namespace SVSModel
{
    public class CropModel
    {
        static double[] scaledValues(double[] scaller, double final, double correction)
        {
            double[] sv = new double[scaller.Length];
            for (int d = 0; d < sv.Length; d++)
                sv[d] = scaller[d] * final * correction;
            return sv;
        }

        public static Dictionary<string, double> PropnMaxDM = new Dictionary<string, double>() { { "Seed", 0.0066 },{ "Seedling", 0.015 },{ "Vegetative", 0.5},{ "EarlyReproductive",0.75},
            { "MidReproductive",0.86},{  "LateReproductive",0.95},{"Maturity",0.9933},{"Late",0.9995 } };
        public static Dictionary<string, double> PropnTt = new Dictionary<string, double>() { { "Seed", 0 },{ "Seedling", 0.16 },{ "Vegetative", 0.5},{ "EarlyReproductive",0.61},
            { "MidReproductive",0.69},{  "LateReproductive",0.8},{"Maturity",1.0},{"Late",1.27} };

        public static object[,] CalculateCropOutputs(double[] Tt, Dictionary<string, object> Config, Dictionary<string, object> Params)
        {
            int durat = Tt.Length;
            double Tt_Harv = Tt.Last();
            double Tt_estab = Tt_Harv * (PropnTt[Config["EstablishStage"].ToString()] / PropnTt[Config["HarvestStage"].ToString()]);
            double Xo_Biomass = (Tt_Harv + Tt_estab) * .45 * (1 / PropnTt[Config["HarvestStage"].ToString()]);
            double b_Biomass = Xo_Biomass * .25;
            double T_mat = Xo_Biomass * 2.2222;
            double T_maxRD = PropnTt["EarlyReproductive"] * T_mat;
            double T_sen = PropnTt["MidReproductive"] * T_mat;
            double Xo_cov = Xo_Biomass * 0.4 / (double)Params["rCover"];
            double b_cov = Xo_cov * 0.2;
            double a_harvestIndex = (double)Params["Typical HI"] - (double)Params["HI Range"];
            double b_harvestIndex = (double)Params["HI Range"] / (double)Params["Typical Yield"];
            // Calculate fitted patterns
            double[] BiomassScaller = new double[durat];
            double[] CoverScaller = new double[durat];
            double[] RootDepthScaller = new double[durat];
            double fRootN = new double();
            double fStoverN = new double();
            double fSaleableProductN = new double();
            double fFieldLossN = new double();
            double fDressingLossN = new double();
            double fCropN = new double();
            double StageCorrection = new double();
            for (int d = 0; d < durat; d++)
            {
                BiomassScaller[d] = (1 / (1 + Math.Exp(-((Tt[d] - Xo_Biomass) / (b_Biomass)))));
                if (Tt[d] < T_maxRD)
                    RootDepthScaller[d] = Tt[d] / T_maxRD;
                else
                    RootDepthScaller[d] = 1;
                if (Tt[d] < T_sen)
                    CoverScaller[d] = 1 / (1 + Math.Exp(-((Tt[d] - Xo_cov) / b_cov)));
                else
                    CoverScaller[d] = (1 - (Tt[d] - T_sen) / (T_mat - T_sen));
                double fSaleableYieldDwt = (double)Config["SaleableYield"];
                double fFieldLossPct = (double)Config["FieldLoss"];
                double fFreshTotalProductWt = fSaleableYieldDwt * (1 / (1 - fFieldLossPct / 100)) * (1 / (1 - (double)Config["DressingLoss"] / 100));
                // Crop Failure.  If yield is very low or field loss is very high assume complete crop failure.  Uptake equation are too sensitive saleable yields close to zero and field losses close to 100
                if ((((double)Config["SaleableYield"] * (double)Config["Units"]) < ((double)Params["Typical Yield"] * 0.05)) || ((double)Config["FieldLoss"] > 95))
                {
                    fSaleableYieldDwt = (double)Params["Typical Yield"];
                    fFieldLossPct = 100;
                    fFreshTotalProductWt = (double)Params["Typical Yield"] * (1 / (1 - (double)Params["Typical Dressing Loss %"] / 100));
                }
                double fTotalProductDwt = fFreshTotalProductWt * (double)Config["Units"] * (1 - (double)Config["MoistureContent"] / 100);
                double fFieldLossDwt = fTotalProductDwt * fFieldLossPct / 100;
                fFieldLossN = fFieldLossDwt * (double)Params["Product [N]"] / 100;
                double fDressingLossDwt = fTotalProductDwt * (double)Config["DressingLoss"] / 100;
                fDressingLossN = fDressingLossDwt * (double)Params["Product [N]"] / 100;
                double fSaleableProductDwt = fTotalProductDwt - fFieldLossDwt - fDressingLossDwt;
                fSaleableProductN = fSaleableProductDwt * (double)Params["Product [N]"] / 100;
                double HI = a_harvestIndex + fFreshTotalProductWt * b_harvestIndex;
                double fStoverDwt = fTotalProductDwt * 1 / HI - fTotalProductDwt;
                fStoverN = fStoverDwt * (double)Params["Stover [N]"] / 100;
                double fRootDwt = (fStoverDwt + fTotalProductDwt) * (double)Params["P Root"];
                fRootN = fRootDwt * (double)Params["Root [N]"] / 100;
                fCropN = fRootN + fStoverN + fFieldLossN + fDressingLossN + fSaleableProductN;
                StageCorrection = 1 / PropnMaxDM[Config["HarvestStage"].ToString()];
            }
            double[] RootN = scaledValues(BiomassScaller, fRootN, StageCorrection);
            double[] StoverN = scaledValues(BiomassScaller, fStoverN, StageCorrection);
            double[] SaleableProductN = scaledValues(BiomassScaller, fSaleableProductN, StageCorrection);
            double[] FieldLossN = scaledValues(BiomassScaller, fFieldLossN, StageCorrection);
            double[] DressingLossN = scaledValues(BiomassScaller, fDressingLossN, StageCorrection);
            double[] TotalCropN = scaledValues(BiomassScaller, fCropN, StageCorrection);
            double[] CropUptakeN = Functions.calcDelta(TotalCropN);
            double[] Cover = scaledValues(CoverScaller, (double)Params["A cover"], 1.0);
            double[] RootDepth = scaledValues(RootDepthScaller, (double)Params["Max RD"], 1.0);
            /* if len(c["DefoliationDates"])>0:
            # CropN.sort_index(inplace=True)
            # for dd in Config["DefoliationDates"]:
            # StoverNtoRemove = (CropN.loc[('+ Stover',dd),'Values'].values[0] - CropN.loc[('Root',dd),'Values'].values[0]) * 0.7
            # TotalNtoRemove = StoverNtoRemove
            #if Params['Yield type'] == 'Standing DM':
            # StoverNtoRemove=0
            # TotalNtoRemove = (CropN.loc[('TotalCrop',dd),'Values'].values[0] - CropN.loc[('Root',dd),'Values'].values[0]) * 0.7
            # DefCovFact = 0.3
            # for d in Tt[dates][dd:].index:
            # CropN.loc[('+ Stover',d),'Values'] = CropN.loc[('+ Stover',d),'Values'] - StoverNtoRemove 
            # CropN.loc[('TotalCrop',d),'Values'] = CropN.loc[('TotalCrop',d),'Values'] - TotalNtoRemove
            # CropWater.loc[('Cover',d),'Values'] = CropWater.loc[('Cover',d),'Values'] * DefCovFact
            # DefCovFact = min(1.0,DefCovFact + Tt[d] * 0.00001) */

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

