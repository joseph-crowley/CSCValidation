#! /usr/bin/env python3

##########################################################################################
# Processes for populating the CSCValidation website
#     URL: https://cms-conddb.cern.ch/eosweb/csc/
#
# Authors
#   Joe Crowley, UC Santa Barbara
##########################################################################################
import json
import time
import subprocess
import os
from parsingtools import parse_summary_html

def build_runlist(web_dir = 'root://eoscms.cern.ch//store/group/dpg_csc/comm_csc/cscval/www',runs_to_update=[]):
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
    if runs_to_update:
        unlisted_dirs = runs_to_update
    else:
        cmd = f'{use_proxy} gfal-ls {web_dir}/results | grep "run[0-9][0-9]"'
        run_dirs = subprocess.check_output(cmd,shell=True).decode('ascii').split('\n')

        # TODO: smart building of runlist by runXXXXX/datasets/dataset
        #unlisted_dirs = [d for d in run_dirs if d[3:] not in run_list.keys()]
        unlisted_dirs = run_dirs
    
    # make the json file
    # first sort out which dirs to add to the runlist
    RUN3_BEGIN = 352319
    MAX_RUNNUM = 400000

    dirs_to_list = []
    for u in unlisted_dirs:
        if not u: continue
        if not len(u)==9: continue

        try:
            run_number = int(u[3:])
        except (ValueError, TypeError) as err:
            print(f'{err.args[0]}')
            run_number = 0

        if RUN3_BEGIN < run_number < MAX_RUNNUM:
            dirs_to_list.append(u)
        
    create_runlist_json(dirs_to_list, web_dir, use_proxy)

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

        print(f'    excluding datasets {exclude}')

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

            run_list.update({run_number:{"directory":run_number, "datasets":updated_summary}})

        # dump runlist json
        with open('run_list.json','w') as f:
            json.dump(run_list, f, indent=4)

# TODO:
def merge_outputs(config):
    pass

# TODO:
def make_plots(config):
    pass

def new_runs_list():
    '''
    builds a local run list
    run inside the same folder that setup.sh was run in 
    '''
    
    cscvaldir = os.getenv('CSCVALDIR')
    cmd = f'find {cscvaldir} |grep summary.json | tee new_runs'
    files = subprocess.check_output(cmd,shell=True).decode('ascii').split('\n')

    new_run_list = {}
    for f in files:
        if not f: continue
        tmp = {}
    
        with open(f,'r') as summary:
            tmp = json.load(summary)
        
        # why would anyone choose this format?
        # TODO: declutter the json files
        runnum = str(tmp["runnum"])
        datasetname = tmp["datasetname"].split("/")[1]
        
        # get the old data, update the old data with new data  (overwrite for same run/dataset)
        old_data = {runnum : new_run_list.get(runnum, {'directory':runnum, 'datasets':{}})}
        print(old_data)
        old_data[runnum]['datasets'].update({datasetname:tmp})
        new_run_list.update(old_data)
        
        
    with open('updated_run_list.json','w') as f:
        json.dump(new_run_list,f, indent=4)

def merge_runlist(web_dir = 'root://eoscms.cern.ch//store/group/dpg_csc/comm_csc/cscval/www'):
    '''
    given a local updated_run_list.json, retrieve the runlist.json and merge the lists, saving
    the new runlist as updated_run_list.json at web_dir
    '''
    # get a voms proxy
    import getVOMSProxy as voms
    X509_USER_PROXY, username = voms.getVOMSProxy()
    use_proxy = f'env -i X509_USER_PROXY={X509_USER_PROXY}'

    ## retrieve the runlist and last run time

    cmd = f'{use_proxy} gfal-copy -f {web_dir}/js/runlist.json runlist.json'
    os.system(cmd)
 
    with open('runlist.json','r') as f:
        tmp = f.read()

    runlist = json.loads(tmp[14:])
    

    with open('updated_run_list.json','r') as f:
        new_runs = json.load(f)

    runlist.update(new_runs)
    
    with open('updated_run_list.json','w') as f:
        f.write('var runData = ') # TODO: declutter the json files
        json.dump(runlist,f,indent = 4)
    
    # TODO: change the permissions of runlist.json to copy directly there
    date_format = "%Y%m%d_%H%M%S"
    t0 = time.strftime(date_format)
    cmd = f'{use_proxy} gfal-copy -f updated_run_list.json {web_dir}/js/updated_run_list_{t0}.json'
    os.system(cmd)

if __name__ == '__main__':
    new_runs_list()
    merge_runlist()
