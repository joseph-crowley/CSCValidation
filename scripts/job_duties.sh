#!/bin/bash 

CMSSWVERSION=$1
SCRAMARCH=$2
JOBTAG=$3
USER=$4
RUN=$5

OUTDIR="/eos/cms/store/group/dpg_csc/comm_csc/cscval/condor_output/$USER/$JOBTAG"
SITEDIR="/eos/cms/store/group/dpg_csc/comm_csc/cscval/www/results/runRUN_REPLACETAG/STREAM_REPLACETAG/Site"
IMGDIR="$SITEDIR/PNGS"

# set up environment
export SCRAM_ARCH=$SCRAMARCH
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 project CMSSW $CMSSWVERSION`
cd $CMSSWVERSION/src
eval `scramv1 runtime -sh`
git cms-addpkg RecoLocalMuon/CSCValidation
scramv1 b -j 1
cd - 

mkdir RUNDIR
mv validation_cfg.py RUNDIR/
mv plots_and_graphs.py RUNDIR/
mv $CMSSW_BASE/src/RecoLocalMuon/CSCValidation/macros/makePlots.C RUNDIR/  
mv $CMSSW_BASE/src/RecoLocalMuon/CSCValidation/macros/myFunctions.C RUNDIR/  
mv copyFromCondorToSite.sh RUNDIR/
cd RUNDIR

# execute the validation
cmsRun validation_cfg.py

# make the plots with the output
root -b -l -q makePlots.C( "validation_histograms.root" )

# Validation script produces ROOT files, copy them to eos
./copyFromCondorToSite.sh $(pwd) validation_histograms.root eoscms.cern.ch $OUTDIR valHists_$RUN.root 

# plots_and_graphs produces lots of images and a summary
./copyFromCondorToSite.sh $(pwd) Summary.html eoscms.cern.ch $SITEDIR Summary.html
./copyFromCondorToSite.sh $(pwd) validation_cfg.py eoscms.cern.ch $IMGDIR config.py
for img in $(ls *.png); do ./copyFromCondorToSite.sh $(pwd) $img eoscms.cern.ch $IMGDIR $img; done
