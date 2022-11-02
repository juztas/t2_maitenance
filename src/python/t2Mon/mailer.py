#!/bin/python
#
import os
import json
import shutil
import subprocess
import time
import tempfile
import copy
import datetime

def getPrevStats(inputFile):
    return

def sizeConverter(inputVal):
    valType = ["Bytes (B)", "Kilobyte (KB)", "Megabyte (MB)", "Gigabyte (GB)", "Terabyte (TB)", "Petabyte (PB)", "Exabyte (EB)"]
    for val in valType:
        if inputVal < 1024:
            return round(inputVal, 2), val
        inputVal = inputVal / 1024.0
    return round(inputVal, 2), "Exabyte (EB)"


def runCommand(command):
    out = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = out.communicate()
    return stdout, stderr

def getDirStats(directory):
    hdfs_cmd = "sudo -u hdfs hadoop fs -du %s" % directory
    stdout, _stderr = runCommand(hdfs_cmd)
    all_Files = stdout.decode().split("\n")
    return all_Files

def printTabular(itemsDict, leftWidth, rightWidth, dirName, output):
    output += "\n" + str(dirName).center(leftWidth + rightWidth, '-') + "\n"
    for k, v in list(itemsDict.items()):
        output+= k.ljust(leftWidth, '.') + str(v).rjust(rightWidth) + '\n'
    output += '\n'
    return output


def execute():
    output=""
    print('Getting dir stats')
    now  = datetime.datetime.now()
    output += "[CITMon] Caltech Tier2 Storage information at %s\n" % now.strftime("%Y-%m-%d %H:%M")
    output+="This is an automated email from the Tier2 monitoring system. Do not reply to this email and if you have any question, please write to t2admin@hep.caltech.edu\n"
    output+="This message was generated automatically and is sent once per week. Generated at: %s \n" % now.strftime("%Y-%m-%d %H:%M") + '\n'
    for mainDir in ['/store/user/', '/store/group/', '/store/']:
        allDirStats = getDirStats(mainDir)
        dirDict = {}
        for direct in allDirStats:
            dirvals = [_f for _f in direct.split(' ') if _f]
            if dirvals:
                newSize, newSizeType = sizeConverter(int(dirvals[0]))
                dirDict[dirvals[2].split('/')[-1]] = "%s %s" % (newSize, newSizeType)
        #print 'Information on Hadoop storage usage at %s' % mainDir
        output = printTabular(dirDict, 20, 20, "Storage usage at %s" % mainDir, output)
    # HDFS Statistics
    output += "\nHDFS Statistics:\n"
    stdout, _stderr = runCommand("sudo -u hdfs hdfs dfsadmin -report")
    allLines = stdout.decode().split("\n")
    for line in allLines[:10]:
        output += line + "\n"

    output += "\n\n" + "-"*50 + "\n"
    output += "Monitoring links require login. If you are unable to login, please contact t2admin@hep.caltech.edu or ping admins on slack \n"
    output += "Storage Policy and Quota information: https://caltech.teamwork.com/#notebooks/144924\n"
    output += "Tier2 Storage monitoring: https://sensei3.hep.caltech.edu:3000/d/000000035/hdfs-mon?refresh=5m&orgId=1\n"
    output += "Tier2 CEPH Storage monitoring: https://sensei3.hep.caltech.edu:3000/d/6oPCwO9mk/ceph-cluster?refresh=1m&orgId=1\n"
    output += "Tier2 HTCondor queues monitoring: https://sensei3.hep.caltech.edu:3000/d/jL88TdcWz/condor?orgId=1\n"
    output += "Tier2 GPUs monitoring: https://sensei3.hep.caltech.edu:3000/d/XNi-A4Gik/gpus-mon?orgId=1\n"
    stdout, _stderr = runCommand("curl -X POST -H 'Content-type: application/json' --data \"{'text':'%s'}\" %s &> /dev/null" % (output, "https://hooks.slack.com/services/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"))
    print(output)
if __name__ == "__main__":
    execute()
