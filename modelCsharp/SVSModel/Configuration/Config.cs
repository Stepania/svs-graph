using System;
using System.Collections.Generic;

namespace Helper
{
    /// <summary>
    /// Class that stores all the configuration information for the simulation
    /// </summary>
    public class Config
    {
        public Crop Prior = null;
        public Crop Current = null;
        public Crop Following = null;

        public List<Crop> Rotation = new List<Crop>();

        public Field field = null;

        public Config(object[,] config)
        {
            Dictionary<string, object> c = Functions.dictMaker(config);
            Prior = new Crop(c, "Prior");
            Current = new Crop(c, "Current");
            Following = new Crop(c, "Following");
            Rotation = new List<Crop>() { Prior, Current, Following };
            field = new Field(c);
        }
    }     
} 
