#!/bin/bash
# Originally from https://github.com/IvyFramework/IvyDataTools/blob/6dc22d4de18e1520b6c217c3146236fed0a51952/scripts/copyFromCondorToSite.sh
#
# Authors
#     Ulascan Sarica, UC Santa Barbara
#     Joe Crowley,    UC Santa Barbara




getFilePath(){
  local indir=$1
  local fname=$2
  local site=$3
  local res=""

  if [[ "${indir}" != "/"* ]]; then # Directory must be an absolute path!
    echo "getFilePath: Directory ${indir} must have been an absolute path!"
    exit 1
  fi

  if [[ "${site}" == "local" ]]; then
    res="file://${indir}/${fname}"
  elif [[ "${site}" == *"t2.ucsd.edu"* ]]; then
    res="davs://redirector.t2.ucsd.edu:${indir}/${fname}"
    res=${res/'/hadoop/cms'/'1094'} # Port for hadoop
    res=${res/'/ceph/cms'/'1095'} # Port for ceph
  elif [[ "${site}" == *"eoscms.cern.ch"* ]]; then
    res="root://eoscms.cern.ch${indir}/${fname}"
    res=${res/'/eos/cms'/''}
  elif [[ "${site}" == *"iihe.ac.be"* ]]; then
    res="srm://maite.iihe.ac.be:8443${indir}/${fname}"
    #res=${res/'/pnfs/iihe/cms'/''}
  elif [[ "${site}" == *"ihep.ac.cn"* ]]; then
    res="srm://srm.ihep.ac.cn:8443${indir}/${fname}"
    #res=${res/'/data/cms'/''}
  elif [[ "${site}" == *"m45.ihep.su"* ]]; then
    res="srm://dp0015.m45.ihep.su:8443${indir}/${fname}"
    #res=${res/'/pnfs/m45.ihep.su/data/cms'/''}
  else
    echo "getFilePath: Site ${site} is undefined."
    exit 1
  fi

  echo ${res}
  exit 0
}


INPUTDIR=$1
FILENAME=$2
OUTPUTSITE=$3 # e.g. 't2.ucsd.edu'
OUTPUTDIR=$4 # Must be absolute path
RENAMEFILE=$FILENAME
if [[ "$5" != "" ]]; then
  RENAMEFILE=$5
fi
INPUTSITE=local
if [[ "$6" != "" ]]; then
  INPUTSITE=$6
fi


echo "Copy from Condor is called with"
echo "INPUTDIR: ${INPUTDIR}"
echo "FILENAME: ${FILENAME}"
echo "OUTPUTSITE: ${OUTPUTSITE}"
echo "OUTPUTDIR: ${OUTPUTDIR}"
echo "RENAMEFILE: ${RENAMEFILE}"


if [[ "$INPUTDIR" == "" ]]; then #Input directory is empty, so assign pwd
  INPUTDIR=$(pwd)
elif [[ "$INPUTDIR" != "/"* ]]; then # Input directory is a relative path
  INPUTDIR=$(pwd)/${INPUTDIR}
fi

if [[ "$OUTPUTDIR" != "/"* ]]; then # Output directory must be an absolute path!
  echo "Output directory must be an absolute path! Cannot transfer the file..."
  exit 1
fi


if [[ ! -z ${FILENAME} ]]; then
  echo -e "\n--- begin copying output ---\n"

  echo "Sending output file ${FILENAME}"

  if [[ ! -e ${INPUTDIR}/${FILENAME} ]]; then
    echo "ERROR! Output ${FILENAME} doesn't exist"
    exit 1
  fi

  echo "Time before copy: $(date +%s)"

  echo "OUTPUTFILE: ${OUTPUTDIR}/${RENAMEFILE}"

  COPY_SRC="$( getFilePath ${INPUTDIR} ${FILENAME} ${INPUTSITE} )"
  if [[ $? -ne 0 ]]; then
    exit 1
  fi

  COPY_DEST="$( getFilePath ${OUTPUTDIR} ${RENAMEFILE} ${OUTPUTSITE} )"
  if [[ $? -ne 0 ]]; then
    exit 1
  fi

  runCmd="env -i X509_USER_PROXY=${X509_USER_PROXY} gfal-copy -p -f -t 14400 --verbose --checksum ADLER32 ${COPY_SRC} ${COPY_DEST}"
  echo "Running: ${runCmd}"
  declare -i itry=0
  declare -i COPY_STATUS=-1
  declare -i REMOVE_STATUS=-1
  while [[ $itry -lt 5 ]]; do
    echo " - Trial ${itry}:"
    ${runCmd}
    COPY_STATUS=$?
    if [[ $COPY_STATUS -eq 0 ]]; then
      break
    fi
    (( itry += 1 ))
  done
  if [[ $COPY_STATUS -ne 0 ]]; then
    echo "Removing output file because gfal-copy crashed with code $COPY_STATUS"
    env -i X509_USER_PROXY=${X509_USER_PROXY} gfal-rm -t 14400 --verbose ${COPY_DEST}
    REMOVE_STATUS=$?
    if [[ $REMOVE_STATUS -ne 0 ]]; then
        echo "gfal-copy crashed and then the gfal-rm also crashed with code $REMOVE_STATUS"
        echo "You probably have a corrupt file sitting on ${OUTPUTDIR} now."
        exit $REMOVE_STATUS
    fi
    exit $COPY_STATUS
  else
    echo "Time after copy: $(date +%s)"
    echo "Copied successfully!"
  fi

  echo -e "\n--- end copying output ---\n"
else
  echo "File name is not specified!"
  exit 1
fi
