[![build solution](https://github.com/PlantandFoodResearch/SVS/actions/workflows/build-solution.yml/badge.svg)](https://github.com/PlantandFoodResearch/SVS/actions/workflows/build-solution.yml)

# SVS

The C# version of the N balance model is in the `ModelCSharp` dirrectory.

## Usage

To use the prototype, you first need to build the solution. This will create several files in the `bin` directory, including the Excel add-in `SVSModel-AddIn64.xll`, which contains the model code.

Next, open Microsoft Excel and click on the **File** tab in the top toolbar. At the bottom of the tab, you will see an **Options** button. Click on it to open the options dialog box.

In the options dialog box, choose the **Add-ins** tab. At the bottom, there is a drop-down menu called **Manage**. Select **Excel Add-ins** and click on the **Go** button to open the Add-ins dialog box.

In the Add-ins dialog box, click on the "Browse" button, navigate to the `..\SVS\ModelCSharp\bin` folder, and select `SVSModel-AddIn64.xll`. Click **OK** to add it to the list of available add-ins.

Still in the **Add-ins** dialog box, make sure the checkbox next to `SVSModel-AddIn64` is checked, and click **OK**.

Now you can open the `Prototype_V2.0.xlsm` file in Excel, and you should have a working copy of the tool prototype.

