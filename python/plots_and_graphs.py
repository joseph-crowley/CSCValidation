#! /usr/bin/env python3

import os
import sys
import time

#make the plots
curtime = time.strftime("[%Y/%m/%d %H:%M:%S]", time.localtime())
print(f"Start making plots for run RUN_REPLACETAG\nStart: {curtime}", file=sys.stderr)

os.system('root -b -l -q makePlots.C( \"validation_histograms.root\" )')

print("Made plots for run RUN_REPLACETAG")
