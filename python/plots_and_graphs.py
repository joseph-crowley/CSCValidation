#! /usr/bin/env python3

import os
import sys
import time

#make the plots
curtime = time.strftime("[%Y/%m/%d %H:%M:%S]", time.localtime())
print(f"Start making plots for run RUN_REPLACETAG\nStart: {curtime}", file=sys.stderr)
os.system("root -l -q -b makePlots.C")
os.system("root -l -q -b makeGraphs.C")

print "made plots for run RUN_REPLACETAG"

#make the web page
web_dir = "/eos/cms/store/group/dpg_csc/comm_csc/cscval/www"

print(f"Start moving plots for runRUN_REPLACETAG to eos\nStart: {curtime}", file=sys.stderr)
os.system("mkdir -p {0}/results/runRUN_REPLACETAG/SingleMuon/Site".format(web_dir))
os.system("mkdir -p {0}/results/runRUN_REPLACETAG/SingleMuon/Site/PNGS".format(web_dir))
os.system("cp Summary.html {0}/results/runRUN_REPLACETAG/SingleMuon/Site".format(web_dir))
os.system("cp validation_RUN_REPLACETAG_cfg.py {0}/results/runRUN_REPLACETAG/SingleMuon/Site/PNGS/config.py".format(web_dir))
os.system("mv *.png {0}/results/runRUN_REPLACETAG/SingleMuon/Site/PNGS".format(web_dir))

# Keep updating the website on AFS
print(f"Start moving plots for run355870 to AFS\nStart: {curtime}", file=sys.stderr)
afsloc = "/afs/cern.ch/cms/CAF/CMSCOMM/COMM_CSC/CSCVAL/results"
os.system("mkdir -p {0}/results/runRUN_REPLACETAG/".format(afsloc))
os.system("cp -r {0}/results/runRUN_REPLACETAG/SingleMuon/ {1}/results/runRUN_REPLACETAG/SingleMuon/".format(web_dir, afsloc))
