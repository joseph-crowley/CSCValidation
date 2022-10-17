from cmseostools import cmsFileManip
import pandas as pd 

def get_files(dataset='', command='', runs=[]):
    runner = cmsFileManip()
    command = '/cvmfs/cms.cern.ch/common/dasgoclient --limit=0 --query="file,run,lumi,events dataset=' + str(dataset) 
    if runs:
        command += ' run in '
        command += str(runs)
    command += '"'
    result = runner.runCommand(command)
    #print(f'result from runner: \n\n{result}\n\n')
    results = result[0].decode('ascii').split('\n')
    results = [r for r in results if "jsonparser" not in r and "error" not in r and r]
    r_keys = "file,run,lumi,events,dataset".split(',')
    retval = []
    for r in results:
        res = dict(zip(r_keys, r.split(' ')))
        if 'events' in res.keys():
            retval.append(res)
    return retval

def get_blocks(dataset='', command='', min_cdate=''):
    # min_cdate is given as an integer of the previous runtime 
    runner = cmsFileManip()
    command = '/cvmfs/cms.cern.ch/common/dasgoclient --limit=0 --query="block dataset=' + str(dataset) 
    #if min_cdate:
    #    date = pd.to_datetime(min_cdate, unit='s').strftime('%Y%m%d')
    #    today = pd.Timestamp.today().floor('D').strftime('%Y%m%d')
    #    command += ' date between [' + date + ', ' + today + ']' 
    command +=  '"'
    #print(command)
    result = runner.runCommand(command)
    #print(f'result from runner: \n\n{result}\n\n')
    results = result[0].decode('ascii').split('\n')
    #print(f'results from decode: \n\n{results}\n\n')
    results = [r for r in results if "jsonparser" not in r and "error" not in r and r]
    #print(f'results from error filter: \n\n{results}\n\n')
    return results

def get_runs(dataset='', command='', block=''):
    runner = cmsFileManip()
    command = '/cvmfs/cms.cern.ch/common/dasgoclient --limit=0 --query="run block=' + str(block) + '"'
    #print(command)
    result = runner.runCommand(command)
    #print(f'result from runner: \n\n{result}\n\n')
    results = result[0].decode('ascii').split('\n')
    #print(f'results from decode: \n\n{results}\n\n')
    results = [int(r) for r in results if "jsonparser" not in r and "error" not in r and r]
    #print(f'results from error filter: \n\n{results}\n\n')
    return results



if __name__ == '__main__':
    print("Testing get_files: ")
    retval = get_files(dataset = '/Muon/Run2022D-v1/RAW')
    print(retval[0])
    #print("\n\nTesting get_blocks: ")
    #retval = get_blocks(dataset = '/Muon/Run2022D-v1/RAW', min_cdate='1663878194.0989656')
    #print(retval[0])
    #print("\n\nTesting get_runs: ")
    #retval = get_runs(block = retval[0])
    #print(retval)
    #print("\n\nTesting get_files with runs: ")
    #retval = get_files(dataset = '/Muon/Run2022D-v1/RAW',runs = retval)
    #print(retval)
