#!/bin/bash 

CMSSWVERSION=$1
SCRAMARCH=$2
JOBTAG=$3
USER=$4
RUN=$5

JOBDIR=$(pwd)
OUTDIR="/eos/cms/store/group/dpg_csc/comm_csc/cscval/condor_output/$USER/$JOBTAG"
SITEDIR="/eos/cms/store/group/dpg_csc/comm_csc/cscval/www/results/runRUN_REPLACETAG/STREAM_REPLACETAG/Site"
IMGDIR="$SITEDIR/PNGS"

# set up environment
export SCRAM_ARCH=$SCRAMARCH
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 project CMSSW $CMSSWVERSION`
cd $CMSSWVERSION/src
eval `scramv1 runtime -sh`
tar -xf $JOBDIR/RecoLocalMuon.tar
scramv1 b -j 1
cp -r RecoLocalMuon/ $JOBDIR
cd $JOBDIR 

mkdir RUNDIR
mv validation_cfg.py RUNDIR/
mv $JOBDIR/RecoLocalMuon/CSCValidation/macros/makePlots.* RUNDIR/  
mv $JOBDIR/RecoLocalMuon/CSCValidation/macros/myFunctions.C RUNDIR/  
mv copyFromCondorToSite.sh RUNDIR/
cd RUNDIR

# execute the validation
cmsRun validation_cfg.py

# make the plots with the output
# note: there are two forms of this depending on CMSSW version. 
#       this script will evaluate whichever it finds first
cFile=$(ls makePlots.C | wc -l)
shFile=$(ls makePlots.sh | wc -l)

if [ $cFile -eq 1 ]; then
  echo "Using makePlots.C"
  root -b -l -q makePlots.C( "validation_histograms.root" )
elif [ $shFile -eq 1 ]; then 
  echo "Using makePlots.sh"
  ./makePlots.sh validation_histograms.root
else
  echo "No makePlots script found. Check RecoLocalMuon/CSCValidation/macros for the right file in $CMSSWVERSION"  
fi

# Validation script produces ROOT files, copy them to eos
./copyFromCondorToSite.sh $(pwd) validation_histograms.root eoscms.cern.ch $OUTDIR valHists_$RUN.root 

# plots_and_graphs produces lots of images and a summary
./copyFromCondorToSite.sh $(pwd) Summary.html eoscms.cern.ch $SITEDIR Summary.html
./copyFromCondorToSite.sh $(pwd) validation_cfg.py eoscms.cern.ch $IMGDIR config.py
for img in $(ls *.png); do ./copyFromCondorToSite.sh $(pwd) $img eoscms.cern.ch $IMGDIR $img; done
