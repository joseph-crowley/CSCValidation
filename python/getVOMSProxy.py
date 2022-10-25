#! /usr/bin/env python3

##########################################################################################
# Tool to retrieve a voms proxy via python
#
#
# Authors
#   Ulascan Sarica, UC Santa Barbara
#   Joe Crowley, UC Santa Barbara
##########################################################################################

import os
import subprocess

def getVOMSProxy(printenvinstr=False):
   grid_proxy = None
   grid_proxycheckfiles = [
      "{home}/x509up_u{uid}".format(home=os.path.expanduser("~"), uid=os.getuid()),
      "/tmp/x509up_u{uid}".format(uid=os.getuid())
   ]
   if os.getenv("X509_USER_PROXY") is None or not os.getenv("X509_USER_PROXY"):
      for grid_proxycheckfile in grid_proxycheckfiles:
         if os.path.exists(grid_proxycheckfile):
            grid_proxy = grid_proxycheckfile
            break
   else:
      grid_proxy = os.getenv("X509_USER_PROXY")

   time_left = -1
   if grid_proxy is None or not os.path.exists(grid_proxy):
      grid_proxy = grid_proxycheckfiles[0]
   else:
      time_left = subprocess.check_output("voms-proxy-info --timeleft --file={}".format(grid_proxy), shell=True)
      time_left = int(time_left.strip())

   proxy_valid_threshold=86400 # 1 day
   if time_left<=proxy_valid_threshold:
      os.system("voms-proxy-init -q -rfc -voms cms -hours 192 -valid=192:0 -out={}".format(grid_proxy))
      for grid_proxycheckfile in grid_proxycheckfiles:
         if grid_proxycheckfile!=grid_proxy:
            os.system("cp {} {}".format(grid_proxy, grid_proxycheckfile))

   grid_user = subprocess.check_output("voms-proxy-info -identity -file={} | cut -d '/' -f6 | cut -d '=' -f2".format(grid_proxy), shell=True)
   if not grid_user:
      grid_user = os.environ.get("USER")
   grid_user = grid_user.strip()

   if printenvinstr:
      if grid_proxy is not None:
         print("export X509_USER_PROXY={}".format(grid_proxy))

   return grid_proxy, grid_user
