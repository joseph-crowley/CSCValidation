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

def get_from_dataset(dataset, streamQ=True, versionQ=False, eventContentQ=True):
    [stream, version, eventContent] = dataset.split('/')[1:]
    if "GEN" in dataset: 
        stream = stream+version.replace("_","")
    return [s for s, b in zip([stream,version,eventContent], [streamQ,versionQ,eventContentQ]) if b]

def build_runlist(web_dir = 'root://eoscms.cern.ch//store/group/dpg_csc/comm_csc/cscval/www'):
    '''
    Check the files on eos to determine which runs have been processed, and update the 
    runlist.json file. 
    '''
    # get a voms proxy
    import getVOMSProxy as voms
    X509_USER_PROXY, username = voms.getVOMSProxy()
    use_proxy = f'env -i X509_USER_PROXY={X509_USER_PROXY}'

    ## retrieve the runlist and last run time

    # set up last run time, set new time to now
    cmd = f'{use_proxy} gfal-copy -f {web_dir}/js/last_run.json last_run.json'
    os.system(cmd)
    with open('last_run.json', 'r') as f:
        lastrun = json.load(f)
    date_format = "%Y/%m/%d %H:%M:%S"
    default_start_time = '2022/10/24 16:20:00'
    start_time = time.strftime(date_format)
    last_run_time = lastrun.get('lastrun', default_start_time)
    print(f'Last web update: {last_run_time}')

    # set up the runlist
    cmd = f'{use_proxy} gfal-copy -f {web_dir}/js/run_list.json run_list.json'
    os.system(cmd)
    with open('run_list.json','r') as f:
        run_list = json.load(f)

    ## check eos for processed runs not in the runlist
    cmd = f'{use_proxy} gfal-ls {web_dir}/results | grep "run[0-9][0-9]"'
    run_dirs = subprocess.check_output(cmd,shell=True).decode('ascii').split('\n')

    # TODO: smart building of runlist by runXXXXX/datasets/dataset
    #unlisted_dirs = [d for d in run_dirs if d[3:] not in run_list.keys()]
    unlisted_dirs = run_dirs
    
    # make the json file
    create_runlist_json([u for u in unlisted_dirs if u], web_dir, use_proxy)

    # reset the last run time to now
    with open('last_run.json','w') as f:
        lastrun.update({'lastrun':start_time})
        json.dump(lastrun, f, indent=4)

    # copy the lastrun file back over to the website
    cmd = f'{use_proxy} gfal-copy -f last_run.json {web_dir}/js/last_run.json'
    print(cmd)
    #os.system(cmd)

    cmd = f'{use_proxy} gfal-copy -f run_list.json {web_dir}/js/run_list.json'
    print(cmd)
    #os.system(cmd)

def create_runlist_json(runs, web_dir, use_proxy):
    from parsingtools import parse_summary_html

    # load runlist json
    with open('run_list.json','r') as f:
        run_list = json.load(f)

    for run in runs[::-1]:
        run_number = run[3:]
        print(f'\nBuilding summary for run {run_number}')

        summary = {}
        if run_number in run_list.keys():
            exclude = run_list[run_number]["datasets"].keys()
            print(f'    Found existing summaries for datasets {list(exclude)}. Will not overwrite.')
        else:
            exclude = []

        cmd = f'{use_proxy} gfal-ls {web_dir}/results/{run}/'
        datasets = [d for d in subprocess.check_output(cmd,shell=True).decode('ascii').split('\n')[:-1] if d not in exclude and 'tar' not in d]

        for dataset in datasets:
            dataset_path = f'{web_dir}/results/{run}/{dataset}'

            print(f'    dataset {dataset_path}')

            # check if there are any CSC plots with an example
            cscplot = f'{dataset_path}/Site/PNGS/hORecHitsSerial.png'
            cmd = f'{use_proxy} gfal-ls {cscplot}'

            try:
                cscplots = subprocess.check_output(cmd,shell=True).decode('ascii').split('\n')[:-1]
            except subprocess.CalledProcessError:
                print(f'    Error: could not find CSC plots for run {run_number}. skip to next run.')
                cscplots = []

            if not cscplots: continue

            # check if the summary exists
            # summary can be json,html, or both, so filetype is excluded from path
            summary_remotefilepath = f'{dataset_path}/Site'
            summary_fname = f'summary_{dataset}_{run}'

            cmd = f'{use_proxy} gfal-ls {summary_remotefilepath} | grep Summary'
            try:
                summary_files = subprocess.check_output(cmd,shell=True).decode('ascii').split('\n')[:-1]
            except subprocess.CalledProcessError as err:
                print(f'Error: {err.args[0]}')
                summary_files = []

            for summary_file in summary_files:
                cmd = f'{use_proxy} gfal-copy -f {summary_remotefilepath}/{summary_file} {summary_fname}.{summary_file[-4:]}'
                os.system(cmd)

            if os.path.exists(f'{summary_fname}.json'):
                with open(fname+'.json', 'r') as f:
                    summary = json.load(f)

            elif os.path.exists(f'{summary_fname}.html'):
                with open(f'{summary_fname}.html', 'r') as f:
                    summary_str  = f.read()
                summary = parse_summary_html(summary_str)

            else:
                print(f'Directory {run} has no summary file and will be skipped.')
                continue

            # update with new runs
            
            # check if there exists a dataset summary already
            try:
                existing_summary = run_list[run_number]['datasets']
            except KeyError as err:
                existing_summary = {}
            
            # rewrite existing summary for re-run dataset
            # add summary for new dataset
            updated_summary = {}
            updated_summary.update(existing_summary)
            updated_summary.update({dataset:summary})

            run_list.update({run_number:{"datasets":updated_summary}})

        # dump runlist json
        with open('run_list.json','w') as f:
            json.dump(run_list, f, indent=4)

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
    summary_html = summary_html.replace('DATEIME_REPLACETAG', time.strftime("%a, %d %b %Y %H:%M:%S"))

    with open(rundir+'/Summary.html','w') as f:
        f.write(summary_html)
    
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

