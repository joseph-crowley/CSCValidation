#!/bin/bash 

CMSSWVERSION = $1

# set up environment
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 project CMSSW $CMSSWVERSION`
eval `scramv1 runtime -sh`
 
# execute the validation
cmsRun VALIDATION_SCRIPT.py

# Validation script produces two ROOT files, copy them to eos
eosValHistsFileName="/eos/PATH/TO/FILE.root"
while
  localValHistsSum=$(md5sum valHists.root)
  remoteValHistsSum=$(md5sum $eosValHistsFileName)
  [[ $localValHistsSum -ne $remoteValHistsSum ]]
do gfal cp valHists.root $eosValHistsFileName; done

eosTPEHistsFileName="/eos/PATH/TO/FILE.root"
while
  localTPEHistsSum=$(md5sum TPEHists.root)
  remoteTPEHistsSum=$(md5sum $eosTPEHistsFileName)
  [[ $localTPEHistsSum -ne $remoteTPEHistsSum ]]
do gfal cp valHists.root $eosValHistsFileName; done
