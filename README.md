# CSCValidation

set up by running the following code on lxplus, el7@uscms, uaf@ucsd, .. 
Note: to just set up condor tasks without submitting, use the --local flag
```
wget https://raw.githubusercontent.com/joseph-crowley/CSCValidation/local_run/setup.sh
chmod u+x setup.sh
source setup.sh --local
```

you will be prompted for a GRID passphrase; this is the one for your voms proxy

this will run the CSC validation process on a dataset specified in setup.sh.
Note: for local runs, go to the $CMSSWVERSION/src/CSCValidation/outputs/tasks dir and choose a stream and run number. Run the job interactively using local_run.sh

outputs are in $CMSSWVERSION/src/CSCValidation/outputs/
plots are displayed at the [CSC validation website](https://cms-conddb.cern.ch/eosweb/csc/)

# documentation
[block diagram](https://drive.google.com/file/d/1X_CnJtG0em5o13slPdH0YF1PPipN2SkT/view?usp=sharing) for running CSC validation

cscval 2022 update [slides](https://docs.google.com/presentation/d/1xdZkySBoruQWN56ST2SQkPRaijjsJHeLGUNKfosaNlE/edit?usp=sharing)

prompt reconstruction global tag can be found [here](https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideFrontierConditions#Global_Tags_for_Data_Taking)

