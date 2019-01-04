#!/usr/bin/python
import json
import subprocess

def parseNumeric(inputDict, metricKey):
    out = {}
    for key, value in inputDict.items():
        if isinstance(value, (int, float)):
            out['hadoop.%s.%s' % (metricKey, key)] = value
    return out


def appender(inDict, appendTag):
    out = {}
    for key, val in inDict.items():
        if isinstance(val, (int, float)):
            out['hadoop.%s.%s' % (appendTag, key)] = val
    return out

def getUniqKey(typeName):
    if 'name=' in typeName:
        return typeName.split('name=')[-1:][0]
    else:
        return typeName.split('type=')[-1:][0]

def gethdfsOut(url):
    command = "curl -q '%s' -m 10 -connect-timeout 10" % (url)
    print command
    d = {}
    try:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()
        d = json.loads(out[0])
    except:
        print 'There was error getting info...'
    return d
