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

CMSSWVERSION="CMSSW_12_4_9"
DATASET="/Muon/Run2022E-v1/RAW"
GLOBALTAG="124X_dataRun3_Prompt_v4"

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
python3 python/submit_validation_jobs.py $DATASET $GLOBALTAG

# build runlist
export CSCVALDIR=$(pwd)
python3 python/webtools.py
