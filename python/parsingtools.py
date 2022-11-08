#! /usr/bin/env python3

##########################################################################################
# Parsing tools for use with CSCValidation: 
#     command line arguments 
#     html summary files 
#
# Authors
#   Joe Crowley, UC Santa Barbara
##########################################################################################

import sys
import argparse

def parse_command_line(argv):
    # create a namespace with default values
    # example:
    #     Namespace(dataset='/SingleMuon/Run2022D-v1/RAW', globalTag='auto:run3', 
    #               runNumber=0, retrieveOutput=False, buildRunlist=False, 
    #               dryRun=False, force=False, triggers=[], maxJobNum=200)

    parser = argparse.ArgumentParser(description="Submit CSCValidation Jobs")


    parser.add_argument('dataset', type=str, help='/*/*/* (stream and event content)')
    parser.add_argument('globaltag', type=str, help='promptrecoGlobalTag for Era (see "full configuration" on "CMSTalk post)"')
    parser.add_argument('-rn', '--runNumber', type=int, default=0, help='Process a specific run (defaults to all runs).')
    parser.add_argument('-ro', '--retrieveOutput', action='store_true',help='Retrieve the output of a previous run and produce the HTML.')
    parser.add_argument('-br', '--buildRunList', action='store_true',help='Build the runlist.json file for the website.')
    parser.add_argument('-dr', '--dryRun', action='store_true',help='Don\'t submit, just create the objects')
    parser.add_argument('-f','--force', action='store_true', help='Force a recipe (even if already processed).')
    parser.add_argument('-t','--triggers', nargs='*', help='Optionally run on additional triggers.')
    parser.add_argument('-mj','--maxJobNum', type=int, default=200, help='Can use to control the total number of batch jobs submitted out of all of the different files for a run (specified by LFN), as seen on DAS.')
    parser.add_argument('-mr','--minrun', type=int, default=300576, help='minimum run to validate')
    parser.add_argument('-jt','--jobtag', type=str, default='test', help='unique tagname for job')

    args = parser.parse_args(argv)
    return args

def parse_args(return_dict=False):
    argv = sys.argv[1:]
    args = parse_command_line(argv)

    if not args.triggers:
        args.triggers = []

    dataset = args.dataset.split('/')[1:]

    if len(dataset) != 3:
        msg = 'Invalid dataset. Argument should be in the form of a DAS query (/*/*/*).'
        raise Exception(msg)

    if return_dict:
        return dict(args.__dict__)

    return args

from html.parser import HTMLParser
from html.entities import name2codepoint
import string

class MyHTMLParser(HTMLParser):
    def handle_data(self, data):
        if data.strip() and data[0] != '<':
            self.summary_str += data
            self.summary_str += ','
            self.summary_str = self.summary_str.replace(':,',':')

    summary_str = ''
    keymap = {
                "Release" : "release",
                "Dataset" : "datasetname",
                "Run" : "runnum",
                "# of Events Processed" : "events",
                "Using GlobalTag" : "globaltag",
                "CSCValidation was run on " : "rundate"
             }

def parse_summary_html(html_str): 
    parser = MyHTMLParser()
    parser.feed(html_str)
    
    summary = parser.summary_str
    summary_dict = {}
    horrible_choice = 'CSCValidation was run on '
    for s in summary.split(','):
        if not s: continue

        ss = s.split(':')
        if horrible_choice in s:  
            v = s.replace(horrible_choice,'')
            summary_dict.update({parser.keymap[horrible_choice]:v})
        elif ss[0] in parser.keymap.keys():
            summary_dict.update({parser.keymap[ss[0]]:ss[1]})
    return summary_dict


if __name__ == '__main__':
    args = parse_args()
    print(args)

