import re
import time
import shlex
import subprocess
import os
import os.path
import sys
import urllib
import urllib2
import httplib
from urllib2 import HTTPError, URLError
import json
from Queue import Queue
from threading import Thread
import grp
import pwd
import os

#q = Queue(maxsize=0)
#num_threads = 10
#results = []



class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    """ HTTPS Client authentication Handler """
    def __init__(self, key, cert):
        urllib2.HTTPSHandler.__init__(self)
        self.key = key
        self.cert = cert

    def https_open(self, req):
        # Rather than pass in a reference to a connection class, we pass in
        # a reference to a function which, for all intents and purposes,
        # will behave as a constructor
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        """ Get connection to host """
        return httplib.HTTPSConnection(host, key_file=self.key, cert_file=self.cert)

def get_content(url, params=None):
    output = ""
    opener = urllib2.build_opener(HTTPSClientAuthHandler(os.getenv('X509_USER_PROXY'), os.getenv('X509_USER_PROXY')))
    try:
        if params:
            response = opener.open(url, params)
            output = response.read()
        else:
            response = opener.open(url)
            output = response.read()
    except HTTPError as ex:
        print 'The server couldn\'t fulfill the request'
        print 'Error code: ', ex.code
        sys.exit(1)
    except URLError as ex:
        print 'Failed to reach server'
        print 'Reason: ', ex.reason
        sys.exit(1)
    return output

def getSize(filename):
    st = os.stat(filename)
    return st.st_size

def getOwners(filename):
    stat_info = os.stat(filename)
    uid = stat_info.st_uid
    gid = stat_info.st_gid
    print uid, gid

    user = pwd.getpwuid(uid)[0]
    group = grp.getgrgid(gid)[0]
    print user, group
    return user, group


def getPhedexAdler(checksumIn):
    out = {}
    line = checksumIn.split(',')
    for item in line:
        new = item.split(':')
        out[new[0]] = new[1]
    return out

def xrdcpHandler(q, result):
    #while True:
    #    inpDict = q.get()
    #    q.task_done()
    # result.append({'nodeName': inpDict['nodeName'], 'failedVolumes': 0, 'failedtoRetrieve': 1})
    if len(q['fileLoc']) == 0:
        return
    if q['fileLoc'][0].startswith('193.58.172.14'):
        print 'Ignoring slow server: %s' % q
        return
    destDir = q['fileName'][1:]
    if not os.path.exists(os.path.dirname(destDir)):
        os.makedirs(os.path.dirname(destDir))
    retCode = -1
    if not os.path.isfile(q['fileName'][1:]):
        print "Execute: xrdcp -S 15 root://%s/%s %s " % (q['fileLoc'][0], q['fileName'], destDir)
        out, retCode = executeBashCommand("xrdcp -S 15 root://%s/%s %s " % (q['fileLoc'][0], q['fileName'], destDir))
    else:
        retCode = 0
    if retCode == 0:
        downSize = getSize(destDir)
        downadler, retCodeAdler = executeBashCommand('xrdadler32 %s' % destDir)
        downadler = list(downadler)[0].split(' ')[0]
        print downSize, downadler
        phedexSize = q['fileInfo']['bytes']
        phedexAdler = getPhedexAdler(q['fileInfo']['checksum'])
        if downSize == phedexSize:
            if phedexAdler['adler32'] == downadler:
                print 'Good to copy, info:'
                print 'System: %s %s' % (downSize, downadler)
                print 'Phedex: %s %s' % (phedexSize, phedexAdler['adler32'])
                user, group = getOwners('/mnt/hadoop/%s' % destDir)
                print 'Current owners: %s %s' % (user, group)
                mvout, mvRetCode = executeBashCommand('mv %s %s' % (destDir, "/mnt/hadoop/%s" % destDir))
                print 'Move finished: %s with exit %s' % (mvout, mvRetCode)
                chownout, chownRetCode = executeBashCommand('chown %s:%s %s' % (user, group, "/mnt/hadoop/%s" % destDir))
                print 'Chown finished: %s with exit %s' % (chownout, chownRetCode)

def executeBashCommand(command):
    try:
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = proc.communicate()
        return out, proc.returncode
    except:
        print 'There was error getting info...'
    return None

def run_pipe_cmd(cmd1, cmd2):
    cmd1 = shlex.split(cmd1)
    cmd2 = shlex.split(cmd2)
    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    return p2.communicate()

def getFileInfoFromPhedex(fileName):
    phedexOut = get_content("https://cmsweb.cern.ch/phedex/datasvc/json/prod/filereplicas?lfn=%s" % fileName)
    phedexOut = json.loads(phedexOut)
    if 'phedex' in phedexOut:
        if 'block' in phedexOut['phedex']:
            if len(phedexOut['phedex']['block']) != 1:
                print phedexOut
                print fileName
                print '==== Failure!!!!'
                return {}
            if 'file' in phedexOut['phedex']['block'][0]:
                if len(phedexOut['phedex']['block'][0]['file']) != 1:
                    print phedexOut
                    print fileName
                    print '---- Failure!!!!!'
                    return {}
                # Get Checksum, bytes, name. Later we might consider also replica and use gfal-copy directly.
                if phedexOut['phedex']['block'][0]['file'][0]['name'] == fileName:
                    return {'checksum': phedexOut['phedex']['block'][0]['file'][0]['checksum'],
                            'bytes': phedexOut['phedex']['block'][0]['file'][0]['bytes']}
    return {}

def getFileLocations(fileName, redirectors=['cmsxrootd.fnal.gov', 'xrootd-cms.infn.it']):
    foundLocations = []
    for redirector in redirectors:
        out, retCode = executeBashCommand("xrdfs %s locate %s" % (redirector, fileName))
        for line in out:
            allLines = line.split('\n')
            for mLine in allLines:
                matchObj = re.match(r'\[::([\d.]+)\]:(\d+\d+) .*', mLine)
                if matchObj:
                    foundIP = matchObj.group(1)
                    foundPort = matchObj.group(2)
                    if foundIP.startswith('192.84.86'):
                        continue
                    if foundIP.startswith('198.32.44'):
                        continue
                    if foundIP.startswith('128.227.22'):
                        continue
                    if foundIP.startswith('193.58.172'):
                        continue
                    if foundIP.startswith('129.93.239'):
                        continue
                    foundLocations.append('%s:%s' % (foundIP, foundPort))
    return foundLocations

def filterOutLfn(fileName):
    filtered = ['/store/admin/', '/store/backfill/', '/store/group/', '/store/PhEDEx_LoadTest07/', '/store/temp/', '/store/test/', '/store/unmerged/', '/store/user/', '/store/mc/DMWM_Test/']
    for filterlfn in filtered:
        if fileName.startswith(filterlfn):
            return True
    return False


def execute():
    startTime = int(time.time())
    # First of all, get all corrupted files;
    #out, proc = run_pipe_cmd("hdfs fsck /store/", "grep CORRUPT")
    #for line in out.split('\n'):
    #    print 'Got %s' % line
    content = []
    with open('corrupt', 'r') as fd:
        content = fd.readlines()
    content = [x.strip() for x in content]
    allChecks = {}
    countNTR = 0
    total = len(content)
    countQRT = 0
    for line in content:
        corrupt = line.split(':')
        if corrupt:
            corruptFile = corrupt[0]
            if filterOutLfn(corruptFile):
                countNTR += 1
                print 'NTR (%s/%s): %s' % (countNTR, total, corruptFile)
                continue
            allChecks[corruptFile] = {}
            countQRT += 1
            print 'QRT (%s/%s): %s' % (countQRT, total, corruptFile)
            # filter out all other starts (phedex load, user, unmerged, etc...
            if corruptFile:
                fileLoc = getFileLocations(corruptFile)
                fileInfo = getFileInfoFromPhedex(corruptFile)
                allChecks[corruptFile]['fileLoc'] = fileLoc
                allChecks[corruptFile]['fileInfo'] = fileInfo
                allChecks[corruptFile]['fileName'] = corruptFile
                print allChecks[corruptFile]
                #xrdcpHandler(allChecks[corruptFile], [])
                # qPut(allChecks[corruptFile])
    #print allChecks
    # xrdfs cmsxrootd.fnal.gov locate
    # filter out Caltech IPs
    # If there is more than 1, use first and get files;
    # query DAS to get adler32 checksum;
    # do adler32 checksum on file and compare with DAS output


#for i in range(num_threads):
#    worker = Thread(target=xrdcpHandler, args=(q, results))
#    worker.setDaemon(True)
#    worker.start()


if __name__ == "__main__":
    execute()
