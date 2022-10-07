#! /usr/bin/env python3

##########################################################################################
# Processes for setting up and running CSCValidation 
#
# code refactored from original CSCVal submission script by:
#   Ben Knapp, Northeastern University
#   Devin Taylor, UW-Madison
#
# Authors
#   Joe Crowley, UC Santa Barbara
##########################################################################################

import time
import os
import pandas as pd

def get_from_dataset(dataset, streamQ=True, versionQ=False, eventContentQ=True):
    [stream, version, eventContent] = dataset.split('/')[1:]
    if "GEN" in dataset: 
        stream = stream+version.replace("_","")
    return [s for s, b in zip([stream,version,eventContent], [streamQ,versionQ,eventContentQ]) if b]

def build_runlist():
    # TODO: document and perhaps rename build_runlist

    Time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    tstamp = time.strftime("%H%M%S", time.localtime())

    print(f"[{Time}] Building runlist for afs", file=sys.stderr)
    os.system(f'bash generateRunList.sh /afs/cern.ch/cms/CAF/CMSCOMM/COMM_CSC/CSCVAL/results/results > temp_afs_runlist_{tstamp}.json')
    os.system('mv temp_afs_runlist_{tstamp}.json /afs/cern.ch/cms/CAF/CMSCOMM/COMM_CSC/CSCVAL/results/js/runlist.json')

    print("[{Time}] Building runlist for eos", file=sys.stderr)
    os.system(f'bash generateRunList.sh > temp_eos_runlist_{tstamp}.json')
    os.system(f'cat temp_eos_runlist_{tstamp}.json > /eos/cms/store/group/dpg_csc/comm_csc/cscval/www/js/runlist.json')
    os.system(f'rm temp_eos_runlist_{tstamp}.json')

    # create last run json
    with open('lastrun.json','w') as file:
        file.write('var lastrun = {\n  "lastrun" : "%s"\n}\n' % Time)

    os.system('cat lastrun.json > /eos/cms/store/group/dpg_csc/comm_csc/cscval/www/js/lastrun.json')
    os.system('mv lastrun.json /afs/cern.ch/cms/CAF/CMSCOMM/COMM_CSC/CSCVAL/results/js/')

# TODO:
def merge_outputs(config):
    pass

# TODO:
def make_plots(config):
    pass

def run_validation(config):
    '''
      Create output directory structure and execute step one of validation routine (producing root files)
      config parameters:
        parameter        type      default    comment
        dataset          str       ''         REQUIRED, /*/*/*
        globaltag        str       ''         REQUIRED, promptrecoGlobalTag for era
        runNumber        int       0          process a single run (default to all runs)
        force            bool      False      force the jobs to run
        dryRun           bool      False      create objects and do not submit jobs
        triggers         list(str) []         use multiple triggers
        maxJobNum        int       200        maximum number of jobs to submit
        jobtag           str       ''         unique tagname for jobs 
    '''
    dataset = config['dataset']
    globaltag = config['globaltag']
    run = config['runNumber']
    maxJobNum = config['maxJobNum']
    force = config['force']
    dryRun = config['dryRun']
    triggers = config['triggers']
    num = config['n_events']
    input_files = config['input_files']
    jobtag = config['jobtag']

    [stream, eventContent] = get_from_dataset(dataset) 

    # Create working directory for specific run number
    CMSSW_BASE = os.getenv('CMSSW_BASE')
    basedir = CMSSW_BASE + '/src/CSCValidation'
    rundir = basedir+'/outputs/tasks/{}/run_{}'.format(stream, run)
    os.system('mkdir -p '+rundir + "/logs")
    os.chdir(rundir)
    os.system('ln -sf '+basedir+'/scripts/copyFromCondorToSite.sh {}/'.format(rundir))
    os.system('cp -f '+basedir+'/scripts/job_duties.sh {}/'.format(rundir))
    os.system('cp -f '+basedir+'/python/validation_cfg.py {}/'.format(rundir))

    # currently only support RAW eventContent
    if eventContent != 'RAW':
        print(f'Validation for dataset {datset} failed. Only eventContent currently supported is RAW')
        return 

    # replace template parameters in validation_cfg
    with open(basedir+'/python/validation_cfg.py','r') as f:
        validation_cfg = f.read()
   
    # format the input files for the ESSource in the validation_cfg
    input_files_str = "', '".join(input_files)

    validation_cfg = validation_cfg.replace('GLOBALTAG_REPLACETAG',globaltag)
    validation_cfg = validation_cfg.replace('FILENAME_REPLACETAG', input_files_str)

    with open(rundir+'/validation_cfg.py','w') as f:
        f.write(validation_cfg)

    # replace template parameters in job.sub
    with open(basedir+'/scripts/job.sub','r') as f:
        job_sub = f.read()

    job_sub = job_sub.replace('CONDOROUTDIR_REPLACETAG',rundir)
    job_sub = job_sub.replace('UID_REPLACETAG',str(os.getuid()))

    # args for job_duties.sh
    job_sub = job_sub.replace('CMSSWVERSION_REPLACETAG',os.getenv("CMSSW_VERSION"))
    job_sub = job_sub.replace('SCRAMARCH_REPLACETAG',os.getenv("SCRAM_ARCH"))
    job_sub = job_sub.replace('USER_REPLACETAG',os.getlogin())
    job_sub = job_sub.replace('JOBTAG_REPLACETAG',jobtag)
    job_sub = job_sub.replace('RUN_REPLACETAG',run)

    with open(rundir+'/job.sub','w') as f:
        f.write(job_sub)
    
    # submit the job
    os.system('condor_submit '+rundir+'/job.sub')

def initialize_validation(stream):
    # setup working directory for stream
    CMSSW_BASE = os.getenv('CMSSW_BASE')
    basedir = CMSSW_BASE + '/src/CSCValidation'
    if not os.path.exists(basedir+'/'+stream):
        os.system('mkdir -p {}/outputs/processedRuns/{}'.format(basedir,stream))

    # begin running
    start=time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print(f'CSCVal job initiated at {start}')
    os.chdir(basedir + '/outputs/processedRuns')

    print('Reading previously processed runs')
    procFile = basedir + '/outputs/processedRuns/processedRuns.txt'
    procRuns = []
    if os.path.exists(procFile):
        with open(procFile, 'r') as file:
            procRuns = file.readlines()
    procRuns = [x.rstrip() for x in procRuns] # format: RUNUM_NUMEVTS

    print('Reading previous process time')
    timeFile = basedir + '/outputs/processedRuns/processTime.txt'
    procTimes = []
    if os.path.exists(timeFile):
        with open(timeFile, 'r') as file:
            procTimes = file.readlines()
    procTimes = [x.rstrip() for x in procTimes]
    prevTime = float(procTimes[-1]) - 12*60*60 if procTimes else float(time.time()) - 7*24*60*60 # default to 7 days before now or 12 hours before last run
    prevdate = pd.to_datetime(prevTime, unit='s').strftime("%Y/%m/%d %H:%M:%S")
    print(f'Last run: {prevdate}')

