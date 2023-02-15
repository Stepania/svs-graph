# SVS

The C# version of the N balance model is in the ModelCSharp dirrectory.

To use the prototype first build the solution.  This will make a number of files in the bin dirrectory, the key one being SVSModel-AddIn64.xll, which is the excel add-in containing the model code
Then Open Excel and click the "File" tab on the top tool strip.  At the bottom of this tab there is an "Options" button which will bring up an options box.

Choose the "Add-ins" tab.  There is a drop down at the bottom called "Manage".  Make sure "Excel Add-ins" is selected and click the "Go" button to bring up the Add-ins box.

On this box click the "Browse" button, navigate ..\SVS\ModelCSharp\bin and select SVSModel-AddIn64.xll and click "OK" to have it added to the list of Add-ins available

Still on the Add-ins box, make sure the tick box is checked beside the
SVSModel-AddIn64 and click "OK"

Now if you open the Prototype_V2.0.xlsm file in excel you should have a working copy of the tool prototype

