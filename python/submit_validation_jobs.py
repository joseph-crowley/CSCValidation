#! /usr/bin/env python3

##########################################################################################
# CSCValidation job submission script
#
# Outputs are hosted at 
# http://cms-project-csc-validation.web.cern.ch/cms-project-csc-validation/
#
# Authors
#   Joe Crowley, UC Santa Barbara
##########################################################################################

import time
import os
import pandas as pd

from validation_processes import build_runlist, merge_outputs, make_plots
from validation_processes import get_from_dataset, run_validation

import use_dbs

def submit_validation_jobs(config):
    '''
      config parameters:
        parameter        type      default    comment
        dataset          str       ''         REQUIRED, /*/*/*
        globaltag        str       ''         REQUIRED, promptrecoGlobalTag for era
        runNumber        int       0          process a single run (default to all runs)
        force            bool      False      force the jobs to run
        dryRun           bool      False      create objects and do not submit jobs
        triggers         list(str) []         use multiple triggers
        maxJobNum        int       200        maximum number of jobs to submit
    '''
    dataset = config['dataset']
    globaltag = config['globaltag']
    singleRun = config['runNumber']
    force = config['force']
    dryRun = config['dryRun']
    maxJobNum = config['maxJobNum']
    time0 = time.time()

    [stream, eventContent] = get_from_dataset(dataset) 

    # setup working directory for stream
    if not os.path.exists(stream):
        os.makedirs(stream)

    # begin running
    start=time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
    print(f'CSCVal job initiated at {start}')
    os.chdir(stream)

    print('Reading previously processed runs')
    procFile = 'processedRuns.txt'
    procRuns = []
    if os.path.exists(procFile):
        with open(procFile, 'r') as file:
            procRuns = file.readlines()
    procRuns = [x.rstrip() for x in procRuns] # format: RUNUM_NUMEVTS

    print('Reading previous process time')
    timeFile = 'processTime.txt'
    procTimes = []
    if os.path.exists(timeFile):
        with open(timeFile, 'r') as file:
            procTimes = file.readlines()
    procTimes = [x.rstrip() for x in procTimes]
    prevTime = float(procTimes[-1]) - 12*60*60 if procTimes else float(time.time()) - 7*24*60*60 # default to 7 days before now or 12 hours before last run
    prevdate = pd.to_datetime(prevTime, unit='s').strftime("%Y/%m/%d %H:%M:%S")
    print(f'Last run: {prevdate}')

    # run each individual validation
    if singleRun:
        files = use_dbs.get_files(dataset=dataset)
        n_events = sum([sum(eval(f['events'])) for f in files])
        print(f"\nNumber of events in all files listed in DAS for this run/dataset:{n_events}")
        input_files = [f['file'] for f in files]
        config_tmp = config.copy()
        config_tmp.update({"n_events": n_events, "input_files": input_files})

        print(f"Processing run {singleRun}")
        run_validation(config_tmp)
    else:
        blocks = use_dbs.get_blocks(dataset=dataset)

        ## iterate over each block
        updatedRuns = set()
        for block in blocks:
            # get runs in block
            runs = use_dbs.get_runs(block=block)
            updatedRuns.update(set(runs))

        # iterate over runs
        updatedRuns = sorted(updatedRuns)
        fileRunMap = {}
        eventRunMap = {}
        files = use_dbs.get_files(dataset=dataset, runs=updatedRuns)
        if "GEN" in dataset: 
            updatedRuns = [1]
        for run in updatedRuns:
            eventRunMap[run] = sum([sum(eval(f['events'])) for f in files if int(f['run'])==run])
            fileRunMap[run] = [f['file'] for f in files if int(f['run'])==run]

        runsToUpdate = [run for run in updatedRuns if fileRunMap[run] and eventRunMap[run]>25000]
        if "GEN" in dataset: 
            runsToUpdate = [run for run in updatedRuns if fileRunMap[run]]

        print('Runs to update:')
        for run in runsToUpdate:
            print(f'    Run {run}: {len(fileRunMap[run])} files, {eventRunMap[run]} events')

        for run in runsToUpdate:
            if int(run)<MINRUN: continue
            print(f"Processing run {run}")
            config_tmp = config.copy()
            config_tmp.update({"runNumber":str(run)})
            config_tmp.update({"n_events":str(eventRunMap[run])})
            config_tmp.update({"input_files":fileRunMap[run]})
            run_validation(config_tmp)


def main():
    import parsingtools as parser
    config = parser.parse_args(return_dict=True)

    if config["buildRunList"]:
        build_runlist()
        return 

    if config["retrieveOutput"]:
        merge_outputs()
        make_plots()
        build_runlist()
        return 

    submit_validation_jobs(config)

if __name__ == "__main__":
    main()
