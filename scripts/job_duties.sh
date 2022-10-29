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
#mv $JOBDIR/RecoLocalMuon/CSCValidation/macros/myFunctions.C RUNDIR/  
mv copyFromCondorToSite.sh RUNDIR/
mv Summary.html RUNDIR/
mv summary.json RUNDIR/
cd RUNDIR

# execute the validation
cmsRun validation_cfg.py

# make the plots with the output
#
##########################################################################################
## note: there are two forms of this depending on CMSSW version. 
##       this script will evaluate whichever it finds first
#
#cFile=$(ls makePlots.C | wc -l)
#shFile=$(ls makePlots.sh | wc -l)
#
#if [ $cFile -eq 1 ]; then
#  echo "Using makePlots.C"
#  root -b -l -q makePlots.C( "validation_histograms.root" )
#fi
#if [ $shFile -eq 1 ]; then 
#  echo "Using makePlots.sh"
#  ./makePlots.sh validation_histograms.root
#fi
#if [ $shFile -ne 1 && $cFile -ne 1]; then 
#  echo "No makePlots script found. Check RecoLocalMuon/CSCValidation/macros for the right file in $CMSSWVERSION"  
#fi
##########################################################################################

# fix the run bug in the myFunctions.C file
wget https://raw.githubusercontent.com/cms-sw/cmssw/master/RecoLocalMuon/CSCValidation/macros/myFunctions.C
#cat myFunctions.C | sed -e "s/t2 = t2 + \" (run \" + run + \")\";/t2 = t2 + \" (run \" + $RUN + \")\";/g" | tee myFunctions.C

./makePlots.sh validation_histograms.root

# Validation script produces ROOT files, copy them to eos
./copyFromCondorToSite.sh $(pwd) validation_histograms.root eoscms.cern.ch $OUTDIR valHists_$RUN.root 

# the job produces lots of images and a summary
./copyFromCondorToSite.sh $(pwd) Summary.html eoscms.cern.ch $SITEDIR Summary.html
./copyFromCondorToSite.sh $(pwd) summary.json eoscms.cern.ch $SITEDIR summary.json
./copyFromCondorToSite.sh $(pwd) validation_cfg.py eoscms.cern.ch $IMGDIR config.py
for img in $(ls *.png); do ./copyFromCondorToSite.sh $(pwd) $img eoscms.cern.ch $IMGDIR $img; done
