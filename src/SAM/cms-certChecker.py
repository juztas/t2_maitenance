#!/usr/bin/python
import os
import sys
import subprocess
import time
import datetime

DAY = 24*60*60  # POSIX day in seconds
NOW = int(time.time())

# Check that environmental variable SAME_OK is set
#
if "SAME_OK" not in os.environ.keys():
    print "Error. SAME_OK not defined"
    sys.exit(1)
SAME_OK = int(os.environ["SAME_OK"])

if "SAME_ERROR" not in  os.environ.keys():
    print "Error. SAME_ERROR not defined"
    sys.exit(1)
SAME_ERROR = int(os.environ["SAME_ERROR"])

if "SAME_WARNING" not in  os.environ.keys():
    print "Error. SAME_WARNING not defined"
    sys.exit(1)
SAME_WARNING = int(os.environ["SAME_WARNING"])


def checkCert(fileLoc):
    if not os.path.isfile(fileLoc):
        return 0
    command = "openssl x509 -in %s -subject -issuer -dates -noout" % fileLoc
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    certDN = ''
    for line in p.stdout.readlines():
        if line.startswith('subject='):
            certDN = line.split('=', 1)[1].strip()
        elif line.startswith('notAfter='):
            certEndDate = line.split('=')[1].strip()
            dateF = datetime.datetime.strptime(certEndDate[:-4], "%b %d %H:%M:%S %Y")
            # Feb 26 07:28:02 2018 GMT # We remove GMT as we dont care of this and we check last 30days
            if int(dateF.strftime("%s")) < int(NOW + (30*DAY)):
                print 'It is time to update certificate at %s for %s DN' % (fileLoc, certDN)
                return SAME_WARNING
            print 'Certificate %s is still valid more than 30 days' % certDN
            print certEndDate
            return 0
    retval = p.wait()
    print 'Something wrong happened checking certs lifetime at %s for %s ' % (fileLoc, certDN)
    return SAME_ERROR

if __name__ == "__main__":
    certLoc = sys.argv[1]
    content = []
    with open(certLoc) as f:
        content = f.readlines()
    checkStatus = []
    for item in content:
        checkReturn = checkCert(item.strip())
        checkStatus.append(checkReturn)
    if SAME_ERROR in checkStatus:
        print 'There was a failure checking certificate lifetime...'
        sys.exit(SAME_ERROR)
    if SAME_WARNING in checkStatus:
        print 'There was warning raised checking certificate lifetime...'
        sys.exit(SAME_WARNING)
    sys.exit(SAME_OK)
