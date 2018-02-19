#!/usr/bin/env python
"""
Tests the local FroNtier
"""
#
# Assumes:
#
#   1) environmental variables SAME_OK SAME_WARNING and SAME_ERROR are defined
#   2) environmental variable $CMS_PATH is defined
#   3) file $CMS_PATH/SITECONF/local/JobConfig/site-local-config.xml
#      contains the location of the local FroNtier squid server
#
__revision__ = "$Id: test_frontier.py,v 1.6 2012/10/24 13:32:19 asciaba Exp $"
import os
import sys
import urllib2
from xml.dom.minidom import parseString
from xml.dom.minidom import parse
import base64
import zlib 
import curses.ascii
import time
import string
#
# Print out node name
#
print "node: " + os.uname()[1] 
#
# Check that environmental variable SAME_OK is set
#
if not os.environ.has_key("SAME_OK"):
	print "test_frontier.py: Error. SAME_OK not defined"
	sys.exit(1)
same_ok = int(os.environ["SAME_OK"])    
#
# Check that environmental variable SAME_ERROR is set
#
if not os.environ.has_key("SAME_ERROR"):
	print "test_frontier.py: Error. SAME_ERROR not defined"
	sys.exit(1)
same_error = int(os.environ["SAME_ERROR"])    
#
# Check that envrionmental variable SAME_WARNING is set
#
if not os.environ.has_key("SAME_WARNING"):
	print "test_frontier.py: Error. SAME_WARNING not defined"
	sys.exit(1)
same_warning = int(os.environ["SAME_WARNING"])
#
# Check that environmental variable CMS_PATH is set
#
if not os.environ.has_key("CMS_PATH"):
	print "test_frontier.py: Error. CMS_PATH not defined"
	sys.exit(same_error)
#
# Check that file $CMS_PATH/SITECONF/local/JobConfig/site-local-config.xml
# exists
#
slcfil = os.environ["CMS_PATH"] + \
         "/SITECONF/local/JobConfig/site-local-config.xml"
if not os.path.exists(slcfil):
	print "test_frontier.py: Error. file " + slcfil + " does not exist"
	sys.exit(same_error)
#
# Print out site-local-config.xml
#
fileobj = open(slcfil,'r')
slcprint = fileobj.read()
slcprint = slcprint.replace('<','&lt;')
fileobj.close()
#
# Read and parse site-local-config.xml into a dom
# See http://docs.python.org/lib/module-xml.dom.minidom.html
#
slcdom = parse(slcfil)
#
# Work out site name from site-local-config.xml
#
silist = slcdom.getElementsByTagName("site")
if len(silist) == 0:
	site = "UNKNOWN"
else:
	stag = silist[0]
	site = stag.getAttribute("name")
print "site: " + site    
# 
# Check for at least one proxy or proxyconfig tag
#
prlist = [x.getAttribute('url') for x in slcdom.getElementsByTagName("proxy")]
if len(prlist) == 0:
	prcfglist = [x.getAttribute('url') for x in slcdom.getElementsByTagName("proxyconfig")]
	if len(prcfglist) == 0:
		print "test_frontier.py: Error. no proxy or proxyconfig tag in file " + slcfil
		sys.exit(same_error)    
	print
	print "test_frontier.py: only proxyconfig urls defined, skipping squid pings for now"
	print
#
# get pure squid site name
#
def getSNameFromURL(url):
	part   = string.split(url,'//')[1]
	sqname = string.split(part,':')[0]
	return sqname 
sqlist = map(getSNameFromURL,prlist) 
# 
# Check whether has load balance proxies from site-local-config.xml
# 
load = slcdom.getElementsByTagName("load")
if len(load) == 0:
	loadtag = "None"
else:
	loadtag = load[0].getAttribute("balance")
print "loadtag: " + loadtag
#
# Test access to squid
#

test_result = "Failed"
ever_warning = "False" 
ever_ok = "False"
exeception_list = ["nat005.gla.scotgrid.ac.uk"]
for squid in sqlist:	
	if squid not in exeception_list:
		sping = os.popen("ping -c3 " +squid,"r")
		while 1:
			line = sping.readline()
			if not line: break
			print line
		code = sping.close()
		if code != None :
			print "test_frontier.py: Failed ping from %s to %s failed with error %s"%(site,squid,code)
			ever_warning = "True"
			if ever_ok == "True": test_result = "Warning"
		else: 
			if ever_warning == "True": test_result = "Warning"
			else: 
				test_result = "OK"
				ever_ok = "True"
				if loadtag == "None": break
if test_result == "Failed" and ever_warning == "False": 
	test_result = "OK"
			
if test_result == "OK":
	print "OK"  		
	sys.exit(same_ok)
elif test_result == "Warning":
	print "Warning: there are proxy not responding on the chain of proxies"
	sys.exit(same_warning)	
else :
	print "test_frontier.py: Error: Failed ping with all the proxies on the chain"
	sys.exit(same_error)
