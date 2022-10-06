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

# TODO: remove unnecessary stuff, only merge outputs here. 
# TODO: make a template for each script.
def merge_outputs(config):
    '''
    Script to retrieve and merge the histograms
    '''
    dataset = config['dataset']
    globaltag = config['globaltag']
    runN = config['runNumber']
    maxJobNum = config['maxJobNum']
    force = config['force']
    dryRun = config['dryRun']
    triggers = config['triggers']
    num = config['n_events']
    input_files = config['input_files']

    [stream, eventContent] = get_from_dataset(dataset) 

    CONDOR_PATH = '/eos/cms/store/group/dpg_csc/comm_csc/cscval/condor_output'

    # No run numbers below MINRUN will be processed
    # This parameter is ignored if the "-rn" option is specified on the command line
    MINRUN = 300576 # test

    os.chdir(stream)
  
    if not maxJobNum:
        maxJobNum = 200

    runCrab = False

    runsToPlot = []

    if force: print('Forcing remerging')
    # get available runs in eos
    for job in subprocess.Popen(f'ls {CONDOR_PATH}/{stream}', shell=True,stdout=pipe).communicate()[0].splitlines():
        # go to working area
        [runStr,runEventContent] = job.split('_')
        run = runStr[3:]

        # TODO: seems like this conditional can be cleaned up. but if it ain't broke.. 
        # runN is the run number if option "-rn" is specified
        if runN:
            if str(runN) != run: continue
        else:
            if int(run)<MINRUN: continue

        # dont rerun if current merge
        if "Job <%s_%smerge> is not found" % (run,stream) not in subprocess.Popen("unbuffer bjobs -J %s_%smerge" % (run,stream), shell=True,stdout=pipe).communicate()[0].splitlines():
            print('Run %s %s not finished' % (run,stream))
            continue

        rundir = 'run_%s' % run
        os.mkdirs(rundir)
        os.chdir(rundir)

        tpeOut = 'TPEHists.root'
        valOut = {}
        valOut['All'] = 'valHists_run%s_%s.root' % (run, stream)
        for trigger in triggers:
            valOut[trigger] = '%s_valHists_run%s_%s.root' % (trigger, run, stream)

        if runCrab:
            # get last job (in case we reprocessed)
            jobVersion = ''
            for jv in subprocess.Popen('eos ls %s/%s/%s' % (CRAB_PATH,stream,job), shell=True,stdout=pipe).communicate()[0].splitlines():
                jobVersion = jv
            fileDir = '%s/%s/%s/%s/0000' % (CRAB_PATH,stream,job,jobVersion)
        elif runCondor:
            jobVersion = 'job'
            fileDir = '%s/%s/%s' % (CONDOR_PATH,stream,job)
        else:
            jobVersion = 'job'
            fileDir = '%s/%s/%s' % (BATCH_PATH,stream,job)
        tpeFiles = []
        valFiles = {}
        valFiles['All'] = []
        for trigger in triggers:
            valFiles[trigger] = []

        # clean fileDir for files under 512 first, but skip TPEHists
        subprocess.check_call("find %s -name \"*run*.root\" -size -1b -delete" % fileDir, shell=True)
        for file in subprocess.Popen('eos ls %s' % (fileDir), shell=True,stdout=pipe).communicate()[0].splitlines():
            if file[0:3]=='TPE': tpeFiles += [file]
            if file[0:3]=='val': valFiles['All'] += [file]
            for trigger in triggers:
                if file.startswith('%s_val' % trigger): valFiles[trigger] += [file]
        nFiles = len(valFiles['All'])
        if len(tpeFiles) == 0 or float(nFiles)/len(tpeFiles) < 0.7:
            print("Less than 7/10 of Validation root files out of the total number of batch jobs got through")
            print("May need to re-do the validation for run #%s..." % run )

        # see if we need to remerge things
        processedString = '%s_%i' %(jobVersion, nFiles)
        fname = 'out.txt'
        open(fname, 'a').close()
        with open(fname,'r') as file:
            oldProcessedString = file.readline().rstrip()

        if not force:
            if oldProcessedString == processedString:
                os.chdir('../')
                continue

        print("Processing %s run %s" % (stream, run))

        with open(fname,'w') as file:
            file.write(processedString)

        # and merge them
        #nFiles is the total number of validation CSC DQM ROOT files
        maxJobSize = 400
        nMerges = nFiles / maxJobSize + 1
        for imerge in range(0, nMerges):
            if imerge > 1: continue      # effectively set maximum files to 2*maxJobSize
            # prepare remerge string
            remergeString =  '[[ ! $? ]] && echo "Merge failed, try remerging"\n'
            remergeString += 'failstr=$(grep "hadd exiting" mergeout_%s.txt)\n' % imerge
            remergeString += 'while [[ $failstr ]]; do\n'
            remergeString += '    badfile=$(echo $failstr | cut -c30-)\n'
            remergeString += '    echo "Removing bad file $badfile" >&2\n'
            remergeString += '    rm $badfile\n'
            remergeString += '    $valfiles=${valfile/$badfile/}\n'
            remergeString += '    mv mergeout_{}.txt $baseDir/mergeout_$(date +"%H%M%S").txt\n'.format(imerge)
            remergeString += '    hadd -T -k -n 100 -f $target $valfiles > mergeout_%s.txt 2>&1\n' % imerge
            remergeString += '    failstr=$(grep "hadd exiting" mergeout_%s.txt)\n' % imerge
            remergeString += 'done\n'
            # remergeString += 'failstr=$(grep "error reading all" mergeout_%s.txt)\n' % imerge
            remergeString += 'failstr=$(grep "error" mergeout_%s.txt)\n' % imerge
            remergeString += '[[ ! -z $failstr ]] && mv mergeout_{}.txt $baseDir/mergefailed_$(date +"%H%M%S").txt\n'.format(imerge)

            mergeScriptStr  = "#!/bin/bash \n"
            mergeScriptStr += "aklog \n"
            mergeScriptStr += 'source /afs/cern.ch/cms/cmsset_default.sh \n'
            rundir = subprocess.Popen("pwd", shell=True,stdout=pipe).communicate()[0]
            rundir = rundir.decode('ascii').rstrip("\n")
            mergeScriptStr += "cd "+rundir+" \n"
            mergeScriptStr += "eval `scramv1 runtime -sh` \n"
            mergeScriptStr += "cd - \n"
            mergeScriptStr += "baseDir=%s\n" % rundir
            mergeScriptStr += "cd %s\n" % fileDir

            sh = open("merge_val_%s.sh" % imerge, "w")
            sh.write(mergeScriptStr)
            if valFiles['All']:
                print("\nMerging valHists")
                sh.write("cd %s\n" % fileDir)
                valfiles = valFiles['All'][imerge*maxJobSize : (imerge+1)*maxJobSize]
                valMergeString  = 'target=merge_valHists_%s.root\n' % imerge
                valMergeString += 'valfiles="'
                for val in valfiles:
                    valMergeString += ' %s' % val
                valMergeString += '"\n'
                valMergeString += 'hadd -T -k -j 4 -f $target $valfiles > mergeout_%s.txt 2>&1\n' % imerge
                # valMergeString += 'root -l -b -q replaceTreeWithGraphs.C"(\\"$target\\")" >> mergeout_%s.txt\n' % imerge
                sh.write(valMergeString+'\n')
                sh.write(remergeString)
                sh.write('mv mergeout_{}.txt $baseDir/mergeout_$(date +"%H%M%S").txt\n'.format(imerge))

            sh.write('cp merge_valHists_%s.root $baseDir\n' % imerge)
            sh.write('cd %s\n' % rundir)
            sh.close()
            if not dryRun: subprocess.check_call("LSB_JOB_REPORT_MAIL=N bsub -R \"pool>3000\" -q 8nh -J %s_%smerge_%s < merge_val_%s.sh" % (run,stream,imerge,imerge), shell=True)

            sh.write(mergeScriptStr)

            sh.write('cd %s\n' % rundir)
            sh.close()

        runsToPlot += [[run,job,nMerges]]

        os.chdir('../')

    updateRunlist = len(runsToPlot)
    # now plot the merges as they finish
    plot_config = config.copy()
    plot_config.update({"runsToPlot":runsToPlot})
    make_plots(plot_config)
    os.chdir('../')

    if updateRunlist and not force:
        build_runlist()

# TODO: fill in variables from merge_outputs
def make_plots(config):
    runsToPlot = config['runsToPlot']
    dataset = config['dataset']
    globaltag = config['globaltag']
    run = config['runNumber']
    maxJobNum = config['maxJobNum']
    force = config['force']
    dryRun = config['dryRun']
    triggers = config['triggers']
    num = config['n_events']
    input_files = config['input_files']

    [stream, eventContent] = get_from_dataset(dataset) 

    remainingJobs = runsToPlot
    while remainingJobs:
        runsToPlot = remainingJobs
        remainingJobs = []
        for run,job,nMerges in runsToPlot:
            # go to working area
            rundir = 'run_%s' % run
            python_mkdir(rundir)
            os.chdir(rundir)

            tpeOut = 'TPEHists.root'
            valOut = {}
            valOut['All'] = 'valHists_run%s_%s.root' % (run, stream)
            for trigger in triggers:
                valOut[trigger] = '%s_valHists_run%s_%s.root' % (trigger, run, stream)

            # TODO: is bjobs related to bsub? what does this get replaced with?
            # wait for job to finish then copy over
            print("Waiting on run %s" % run)
            runningMergeJobs = subprocess.Popen("bjobs -w | grep %s_%smerge" % (run,stream), shell=True,stdout=pipe).communicate()[0].splitlines()
            if runningMergeJobs:
                time.sleep(20)
                remainingJobs += [[run,job,nMerges]]
            else:
                if dryRun: continue
                print("Run %s merged" % run)
                valRet = subprocess.call('hadd -k -f %s `ls merge_valHists_*.root` ' % (valOut['All']), shell=True)
                # valRet = subprocess.call('mv merge_valHists_0.root %s' % (valOut['All']), shell=True) # temporary
                if valRet: valRet = subprocess.call('mv merge_valHists_0.root %s' % (valOut['All']), shell=True) # temporary
                if not valRet: os.system("./secondStep.py")
                #andrew -- comment out next line to keep merged rootfiles in work directory as well
                #subprocess.call('rm *.root', shell=True)

            os.chdir('../')

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

    [stream, eventContent] = get_from_dataset(dataset) 

    # Create working directory for specific run number
    basedir = '$CMSSW_BASE/src/CSCValidation'
    rundir = basedir+'/Outputs/tasks/{}/run_{}'.format(stream, run)
    os.mkdirs(rundir + "/Logs")
    os.chdir(rundir)
    os.system('ln -sf '+basedir+'/scripts/copyFromCondorToSite.sh {}/'.format(rundir))
    os.system('cp -f '+basedir+'/python/validation_cfg.py {}/'.format(rundir))

    # currently only support RAW eventContent
    if eventContent != 'RAW':
        print('Validation failed. Only eventContent currently supported is RAW')
        return 

    # replace template parameters in validation_cfg
    with open(basedir+'/python/validation_cfg.py','r') as f:
        validation_cfg = f.read()

    validation_cfg = validation_cfg.replace('CONDOROUTDIR_REPLACETAG',rundir)

    with open(rundir+'/validation_cfg.py','w') as f:
        f.write(validation_cfg)

    # replace template parameters in job.sub
    with open(basedir+'/scripts/job.sub','r') as f:
        job_sub = f.read()

    job_sub = job_sub.replace('CONDOROUTDIR_REPLACETAG',rundir)
    job_sub = job_sub.replace('HOME_REPLACETAG',os.path.expanduser("~"))
    job_sub = job_sub.replace('UID_REPLACETAG',os.getuid())

    with open(rundir+'/job.sub','w') as f:
        f.write(job_sub)

