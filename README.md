# CSCValidation

set up by running the following code on lxplus, el7@uscms, uaf@ucsd, .. 
```
wget https://raw.githubusercontent.com/joseph-crowley/CSCValidation/master/setup.sh
chmod u+x setup.sh
source setup.sh
```

you will be prompted for a GRID passphrase; this is the one for your voms proxy

this will run the CSC validation process on a dataset specified in setup.sh.

outputs are in $CMSSWVERSION/src/CSCValidation/outputs/

