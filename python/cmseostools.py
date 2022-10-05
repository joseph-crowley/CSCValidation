#!/usr/bin/env python3
"""
Some tools to handle accesing datasets information on dbs and files on eos
Modified from https://github.com/CERN-PH-CMG/cmg-cmssw/blob/CMGTools-from-CMSSW_7_4_0/CMGTools/Production/python/eostools.py,
and CMGTools.Production.datasetToSource,
and, yet again, ZZAnalysis.
"""

import sys
import os
import re
import FWCore.ParameterSet.Config as cms
import subprocess


class cmsFileManip:
    """A class to interact with files/directories"""
    def runCommand( self, cmd, setShell=True ) :
        myCommand = subprocess.Popen( cmd,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,shell=setShell )
        ( out, err ) = myCommand.communicate()
        if myCommand.returncode != 0:
            print("Command (%s) failed with return code: %d" % ( cmd, myCommand.returncode ), file=sys.stderr) 
            print(err, file=sys.stderr)

        return out,err,myCommand.returncode


def setCAFPath():
    """Hack to get the CAF scripts on the PYTHONPATH"""
    caf = '/afs/cern.ch/cms/caf/python'

    if caf not in sys.path:
        sys.path.append(caf)
setCAFPath()


def runXRDCommand(path, cmd, *args):
    """Run an xrd command.
    """

    lfn = eosToLFN(path)
    command = ['xrd', 'eoscms', cmd, lfn]
    command.extend(args)
    runner = cmsFileManip()
    # print ' '.join(command)
    return runner.runCommand(command, False) # fails when shell=True


def eosToLFN( path ):
    """Converts a EOS PFN to an LFN.
    Just strip out /eos/cms from path.
    If this string is not found, return path.
    ??? Shouldn't we raise an exception instead?"""
    return path.replace('root://eoscms.cern.ch/', '').replace('/eos/cms','')


def lfnToPFN( path, tfcProt = 'rfio'):
    """Converts an LFN to a PFN. For example:
    /store/cmst3/user/cbern/CMG/TauPlusX/Run2011A-03Oct2011-v1/AOD/V2/PAT_CMG_V2_4_0/H2TAUTAU_Nov21
    ->
    root://eoscms//eos/cms/store/cmst3/user/cbern/CMG/TauPlusX/Run2011A-03Oct2011-v1/AOD/V2/PAT_CMG_V2_4_0/H2TAUTAU_Nov21?svcClass=cmst3&stageHost=castorcms
    This function only checks path, and does not access the storage system.
    If the path is in /store/cmst3, it assumes that the CMST3 svcClass is to be used.
    Otherwise, is uses the default one.
    """

    if path.startswith("/store/"):
        path = path.replace("/store/","root://eoscms.cern.ch//eos/cms/store/")
    if path.startswith("/pnfs/psi.ch/cms/trivcat/"):
        path = path.replace("/pnfs/psi.ch/cms/trivcat/","root://t3se01.psi.ch//")
    #print "path to cmsFile():", path
    entity = cmsIO.cmsFile( path, tfcProt )
#    tokens = cmsIO.splitPFN(entity.pfn)
    pfn = '%s://%s//%s/' % (entity.protocol,entity.host,entity.path)

    pfn = entity.pfn
    if tfcProt == 'rfio' and \
        entity.path.startswith("/eos/cms/") and \
                str(entity.stat()).startswith("Error 3011: Unable to stat"):

            pfn.replace("/eos/cms","/castor/cern.ch/cms")
            pfn.replace("eoscms","castorcms")
    return pfn

def runQuery(query, dataset = '', extra_args = ''):
    if dataset:
        query += f' {dataset=}'
    command = ['/cvmfs/cms.cern.ch/common/dasgoclient' , '--limit=0', '--query', query, extra_args]
    runner = cmsFileManip()
    run_command = ' '.join(command)
    return runner.runCommand(run_command)


def runDBS(dataset, instance = 'prod/global', query_type='file', extra_args=''):
    cmd = '"%s'%query_type+' dataset='+dataset +' instance=%s"'%instance

    command = ['/cvmfs/cms.cern.ch/common/dasgoclient' , '--limit=0', '--query', cmd, extra_args]
    runner = cmsFileManip()
    run_command = ' '.join(command)
    return runner.runCommand(run_command)


def findChildren(sample):
    res, _, _ = runDBS(sample, query_type='child')
    return res.strip().split('\n')


def findParent(sample):
    res, _, _ = runDBS(sample, query_type='parent')
    return res.strip().split('\n')


def findDatasets(sample):
    res, _, _ = runDBS(sample, query_type='')
    return res.strip().split('\n')


def listFiles(sample, path, rec = False, full_info = False, other_options=None):
    """Provides a list of files with different methods according to path. Valid paths: 'list', 'dbs', 'dbs-USER', a local filesystem path, an eos path
    other_options is a string that contains special directives. Currently, the following are supported:
      path='dbs':
       - prepend_cms_xrd: Prepends 'root://cms-xrd-global.cern.ch//' to the file path
    Example usage:
      listFiles('/ZZTo4L_13TeV_powheg_pythia8/RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/MINIAODSIM','dbs',True,other_options='prepend_cms_xrd')
    """
    result = []

    if other_options is not None:
       try: # check whether python knows about 'basestring'
           basestring
       except NameError: # no, it doesn't (it's Python3); use 'str' instead
           basestring=str
       if not isinstance(other_options, basestring):
          raise RuntimeError("listFiles: other_options has to be a string.")

    rundbs_extra_args = ''
    if other_options is not None:
       if 'output_json' in other_options.lower():
          rundbs_extra_args = '--json'

    # -- list from a local file --
    if path=="list" :
        with open(sample) as f:
            result = f.readlines()

    # -- listing from a comma-separated string --
    elif path=="csflist":
        result = sample.split(',')

    # -- listing from dbs --
    elif path=="dbs" :
        files, _, _ =runDBS(sample, extra_args=rundbs_extra_args)
        for line in files.split('\n'):
            if not line: continue
            if other_options is not None:
                if 'prepend_cms_xrd' in other_options.lower():
                    line = "root://cms-xrd-global.cern.ch//" + line
#            print line
            result.append(line)

    # -- listing from user dbs --
    elif path=="dbs-USER" :
        print('Querying USER db')
        files, _, _ =runDBS(sample, instance='prod/phys03', extra_args=rundbs_extra_args)
        for line in files.split('\n'):
            result.append(line)

    # -- listing from path=local dir -- untested!
    elif path=="local" :
        if os.path.isdir(sample):
            if not rec:
                # not recursive
                result = [ '/'.join([sample,file]) for file in os.listdir(sample)]
            else:
                # recursive, directories are put in the list first,
                # followed by the list of all files in the directory tree
                allFiles = []
                for root,dirs,files in os.walk(sample):
                    result.extend( [ '/'.join([root,dir]) for dir in dirs] )
                    allFiles.extend( [ '/'.join([root,file]) for file in files] )
                result.extend(allFiles)
        elif os.path.isfile(sample):
           result = [ sample ]
        result = [ "file://"+ff for ff in result if ff.endswith('.root') ]

    # -- listing from EOS (path = eos path prefix, normally "/eos/cms/")
    else:
        cmd = 'dirlist'
        if rec:
            cmd = 'dirlistrec'

        print(path+sample, cmd)
        files, _, _ = runXRDCommand(path+sample, cmd)

        for line in files.split('\n'):
            tokens = [t for t in line.split() if t]
            if tokens:
                #convert to an LFN
                if full_info:
                    result.append( tokens)
                else:
                    result.append( eosToLFN(tokens[4]) )

    result = [ s for s in result if s ]
    return result


def datasetToSource( prefix, dataset, pattern='', readCache=False, other_opts=None):
    """
    Example usage:
      src = datasetToSource('dbs','/ZZTo4L_13TeV_powheg_pythia8/RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1/MINIAODSIM',other_opts='prepend_cms_xrd')
    """

#    print user, dataset, pattern
    recursive=True #FIXME: this is needed for central production, but care is needed if other stuff is present in the EOS path

    data=listFiles(
        sample = dataset,
        path = prefix,
        rec = recursive,
        other_options = other_opts
        )

    rootre = re.compile('.*root')
    files = [f for f in data if rootre.match(f)]

#    print files

    source = cms.Source(
        "PoolSource",
        noEventSort = cms.untracked.bool(True),
        duplicateCheckMode = cms.untracked.string("noDuplicateCheck"),
        fileNames = cms.untracked.vstring(),
        secondaryFileNames = cms.untracked.vstring(),
        )

    source.fileNames.extend( files )

    return source

def testCases():
    print('Examples')
    print('-'*90)
    retval = runDBS(dataset="",query_type="", extra_args="-examples")
    print('\n'.join([r.decode('ascii') for r in retval[0].split(b'\n')]))
    print('-'*90)
    print('-'*90)
    print('\n'*3)
    ## "summary" mode example with file
    #mode = 'summary'
    #print(f'testing {mode} with file')
    #retval = runDBS(dataset="",query_type=mode, extra_args = '-file /store/data/Run2022D/Muon/RAW/v1/000/357/540/00000/68e942e4-30fd-4f6a-a392-986a0d273b82.root')
    #print('-'*90)
    #print('getting results')
    #print('-'*90)
    #print(retval)
    #print('-'*90)
    #print('decoding')
    #print(retval[0].split())
    ##results = eval(retval[0])
    ##dataset_dict = results[0]
    ##print(dataset_dict['nevents'])
    #print('-'*90)
    #
    ## "summary" mode example with dataset
    #print('\n\ntesting "summary" mode with dataset')
    #retval = runDBS(dataset="/Muon/Run2022D-v1/RAW",query_type="summary")
    #results = eval(retval[0])
    #dataset_dict = results[0]
    #print(dataset_dict['nevents'])
    #
    ## "file" mode example
    #print('\n\ntesting "file" mode')
    #retval = runDBS(dataset="/Muon/Run2022D-v1/RAW",query_type="file")
    #results = [r.decode('ascii') for r in retval[0].split()]
    #ex = results[0]
    #print(ex)

if __name__ == '__main__':
    testCases()
