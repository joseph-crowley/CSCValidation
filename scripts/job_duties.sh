#!/bin/bash 

CMSSWVERSION=$1
SCRAMARCH=$2
JOBTAG=$3
USER=$4

OUTDIR="/eos/cms/store/group/dpg_csc/comm_csc/cscval/condor_output/$USER/$JOBTAG"

# set up environment
export SCRAM_ARCH=$SCRAMARCH
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 project CMSSW $CMSSWVERSION`
eval `scramv1 runtime -sh`

mkdir RUNDIR
mv validation_cfg.py RUNDIR/
mv copyFromCondorToSite.sh RUNDIR/
cd RUNDIR

# execute the validation
cmsRun validation_cfg.py

# Validation script produces two ROOT files, copy them to eos
./copyFromCondorToSite.sh $(pwd) valHists.root eoscms.cern.ch $OUTDIR valHists_$JOBTAG.root 
./copyFromCondorToSite.sh $(pwd) TPEHists.root eoscms.cern.ch $OUTDIR TPEHists_$JOBTAG.root 
