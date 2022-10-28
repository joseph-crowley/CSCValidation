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
import subprocess
import json
import pandas as pd
date_format = "%Y/%m/%d %H:%M:%S"

def get_from_dataset(dataset, streamQ=True, versionQ=False, eventContentQ=True):
    [stream, version, eventContent] = dataset.split('/')[1:]
    if "GEN" in dataset: 
        stream = stream+version.replace("_","")
    return [s for s, b in zip([stream,version,eventContent], [streamQ,versionQ,eventContentQ]) if b]


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
    n_events = config['n_events']
    input_files = config['input_files']
    jobtag = config['jobtag']

    [stream, eventContent] = get_from_dataset(dataset) 

    # Create working directory for specific run number
    CMSSW_BASE = os.getenv('CMSSW_BASE')
    basedir = CMSSW_BASE + '/src/CSCValidation'
    rundir = basedir+'/outputs/tasks/{}/run_{}'.format(stream, run)
    os.system('mkdir -p '+rundir + "/logs")
    os.chdir(rundir)
    
    # copy over the necessary files
    os.system('ln -sf '+basedir+'/scripts/copyFromCondorToSite.sh {}/'.format(rundir))
    os.system('ln -sf '+basedir+'/RecoLocalMuon.tar {}/'.format(rundir))
    os.system('cp -f '+basedir+'/scripts/job_duties.sh {}/'.format(rundir))

    ## currently only support RAW eventContent
    #if eventContent != 'RAW':
    #    print(f'Validation for dataset {dataset} failed. Only eventContent currently supported is RAW')
    #    return 

    # fill the templates in the rundir for the job
    replace_template_parameters(basedir, input_files, dataset, globaltag, rundir, CMSSW_BASE, run, stream, jobtag)
    # submit the job
    os.system('condor_submit '+rundir+'/job.sub')

def replace_template_parameters(basedir, input_files, dataset, globaltag, rundir, CMSSW_BASE, run, stream, jobtag, n_events=100):
    # replace template parameters in validation_cfg
    with open(basedir+'/python/validation_cfg.py','r') as f:
        validation_cfg = f.read()
   
    # format the input files for the ESSource in the validation_cfg
    input_files_str = "', '".join(input_files)

    validation_cfg = validation_cfg.replace('GLOBALTAG_REPLACETAG', globaltag)
    validation_cfg = validation_cfg.replace('FILENAME_REPLACETAG', input_files_str)
    validation_cfg = validation_cfg.replace('RUN_REPLACETAG', run)
    validation_cfg = validation_cfg.replace('MAXEVENTS_REPLACETAG', str(n_events))

    with open(rundir+'/validation_cfg.py','w') as f:
        f.write(validation_cfg)

    # replace template parameters in job.sub
    with open(basedir+'/scripts/job_duties.sh','r') as f:
        job_duties = f.read()
   
    # format the input files for the ESSource in the validation_cfg
    input_files_str = "', '".join(input_files)

    job_duties = job_duties.replace('RUN_REPLACETAG', run)
    job_duties = job_duties.replace('STREAM_REPLACETAG', stream)

    with open(rundir+'/job_duties.sh','w') as f:
        f.write(job_duties)

    # replace template parameters in job.sub
    with open(basedir+'/scripts/job.sub','r') as f:
        job_sub = f.read()

    job_sub = job_sub.replace('CONDOROUTDIR_REPLACETAG', rundir)
    job_sub = job_sub.replace('UID_REPLACETAG', str(os.getuid()))

    # args for job.sub
    job_sub = job_sub.replace('CMSSWVERSION_REPLACETAG', os.getenv("CMSSW_VERSION"))
    job_sub = job_sub.replace('SCRAMARCH_REPLACETAG', os.getenv("SCRAM_ARCH"))
    job_sub = job_sub.replace('USER_REPLACETAG', os.getlogin())
    job_sub = job_sub.replace('JOBTAG_REPLACETAG', jobtag)
    job_sub = job_sub.replace('RUN_REPLACETAG', run)

    with open(rundir+'/job.sub','w') as f:
        f.write(job_sub)

    # replace template parameters in Summary.html
    with open(basedir+'/html/summary.html','r') as f:
        summary_html = f.read()

    summary_html = summary_html.replace('CMSSWVERSION_REPLACETAG', os.getenv("CMSSW_VERSION"))
    summary_html = summary_html.replace('DATASET_REPLACETAG', dataset)
    summary_html = summary_html.replace('RUN_REPLACETAG', run)
    summary_html = summary_html.replace('NEVENTS_REPLACETAG', str(n_events))
    summary_html = summary_html.replace('GLOBALTAG_REPLACETAG', globaltag)
    summary_html = summary_html.replace('DATETIME_REPLACETAG', time.strftime(date_format))

    with open(rundir+'/Summary.html','w') as f:
        f.write(summary_html)

    from parsingtools import parse_summary_html
    summary = parse_summary_html(summary_html)
    with open(rundir+'/summary.json','w') as f:
        json.dump(summary,f)
    
def initialize_validation(stream):
    # setup working directory for stream
    CMSSW_BASE = os.getenv('CMSSW_BASE')
    basedir = CMSSW_BASE + '/src/CSCValidation'
    if not os.path.exists(basedir+'/'+stream):
        os.system('mkdir -p {}/outputs/processedRuns/{}'.format(basedir,stream))

    # begin running
    start=time.strftime(date_format, time.localtime())
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
    prevdate = time.strftime(date_format, prevTime)
    print(f'Last run: {prevdate}')

