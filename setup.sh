#! /bin/bash
##########################################################################################
# setup.sh
#
# Example for running CSC Validation with a known dataset and globaltag
# outputs are in $CMSSW_BASE/src/CSCValidation/outputs
# 
# Requirements: 
#     must store git credentials in git configs for cms-addpkg to work
# 
# Authors
#   Joe Crowley, UC Santa Barbara
##########################################################################################

CMSSWVERSION="CMSSW_12_4_8"
DATASET="/Muon/Run2022D-v1/RAW"
GLOBALTAG="124X_dataRun3_Prompt_v4"

INITIALDIR=$(pwd)

source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 project CMSSW $CMSSWVERSION`
cd $CMSSWVERSION/src
eval `scramv1 runtime -sh`
voms-proxy-init --rfc --voms cms -valid 192:00

git cms-addpkg RecoLocalMuon/CSCValidation
scram b -j 1
tar -cf RecoLocalMuon.tar RecoLocalMuon/CSCValidation

git clone https://github.com/joseph-crowley/CSCValidation.git

cd CSCValidation
mv ../RecoLocalMuon.tar .

# submit validation jobs
if [ "$1" == "--local" ]; then
    git checkout local_run
    python3 python/submit_validation_jobs.py $DATASET $GLOBALTAG --dryRun
else 
    python3 python/submit_validation_jobs.py $DATASET $GLOBALTAG
fi

# build runlist
export CSCVALDIR=$(pwd)
python3 python/webtools.py
cp updated_run_list.json $INITIALDIR/updated_run_list_$CMSSWVERSION.json
