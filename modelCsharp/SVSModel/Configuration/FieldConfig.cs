using System;
using System.Collections.Generic;

namespace Helper
{
    public class Field
    {
        public double InitialN { get; private set; }
        public double HWEON { get; private set; }
        
        public Field(Dictionary<string, object> c)
        {
            InitialN = Functions.Num(c["InitialN"]);
            HWEON = Functions.Num(c["HWEON"]);
        }
    }
}
