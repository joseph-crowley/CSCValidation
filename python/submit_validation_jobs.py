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

from validation_processes import build_runlist, merge_outputs, make_plots
from validation_processes import get_from_dataset, initialize_validation, run_validation

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
    MINRUN = config['minrun']
    time0 = time.time()

    [stream, eventContent] = get_from_dataset(dataset) 

    # set up directories, check previous runs
    initialize_validation(stream)

    # run each individual validation
    if singleRun:
        files = use_dbs.get_files(dataset=dataset, runs=[singleRun])
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
            config_tmp = config.copy()
            config_tmp.update({"runNumber":str(run)})
            config_tmp.update({"n_events":str(eventRunMap[run])})
            config_tmp.update({"input_files":fileRunMap[run]})
            print(f"Processing run {run}")
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
