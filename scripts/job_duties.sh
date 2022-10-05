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
  localValHistsSum=$(md5 valHists.root)
  remoteValHistsSum=$(md5 $eosValHistsFileName)
  [[ $localValHistsSum -ne $remoteValHistsSum ]]
do gfal cp valHists.root $eosValHistsFileName; done

eosTPEHistsFileName="/eos/PATH/TO/FILE.root"
while
  localTPEHistsSum=$(md5 TPEHists.root)
  remoteTPEHistsSum=$(md5 $eosTPEHistsFileName)
  [[ $localTPEHistsSum -ne $remoteTPEHistsSum ]]
do gfal cp valHists.root $eosValHistsFileName; done
