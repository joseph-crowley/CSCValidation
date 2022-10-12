#! /usr/bin/env python3

import os
import sys
import time

#make the plots
curtime = time.strftime("[%Y/%m/%d %H:%M:%S]", time.localtime())
print(f"Start making plots for run RUN_REPLACETAG\nStart: {curtime}", file=sys.stderr)
os.system("root -l -q -b makePlots.C")
os.system("root -l -q -b makeGraphs.C")

print("Made plots for run RUN_REPLACETAG")

##make the web page
#web_dir = "/eos/cms/store/group/dpg_csc/comm_csc/cscval/www"
#
#print(f"Moving plots for runRUN_REPLACETAG to eos\nStart: {curtime}", file=sys.stderr)
#os.system(f"mkdir -p {web_dir}/results/runRUN_REPLACETAG/STREAM_REPLACETAG/Site")
#os.system(f"mkdir -p {web_dir}/results/runRUN_REPLACETAG/STREAM_REPLACETAG/Site/PNGS")
#os.system(f"cp Summary.html {web_dir}/results/runRUN_REPLACETAG/STREAM_REPLACETAG/Site")
#os.system(f"cp validation_RUN_REPLACETAG_cfg.py {web_dir}/results/runRUN_REPLACETAG/STREAM_REPLACETAG/Site/PNGS/config.py")
#os.system(f"mv *.png {web_dir}/results/runRUN_REPLACETAG/STREAM_REPLACETAG/Site/PNGS")
#
## Keep updating the website on AFS
#print(f"Start moving plots for run RUN_REPLACETAG to AFS\nStart: {curtime}", file=sys.stderr)
#afsloc = "/afs/cern.ch/cms/CAF/CMSCOMM/COMM_CSC/CSCVAL/results"
#os.system(f"mkdir -p {afsloc}/results/runRUN_REPLACETAG/")
#os.system("cp -r {web_dir}/results/runRUN_REPLACETAG/STREAM_REPLACETAG/ {afsloc}/results/runRUN_REPLACETAG/STREAM_REPLACETAG/")
