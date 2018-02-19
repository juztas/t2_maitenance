#!/usr/bin/python
import subprocess
import shlex
#import psutil


def externalCommand(command, newEnv=None):
    command = shlex.split(command)
    proc = None
    if newEnv:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=newEnv)
    else:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.communicate(), proc.returncode

def tryConvertToNumeric(value):
    floatVal = None
    intVal = None
    try:
        floatVal = float(value)
    except ValueError:
        return value
    try:
        intVal = int(value)
    except ValueError:
        return floatVal if floatVal else value
    return intVal

def run_pipe_cmd(cmd1, cmd2):
    cmd1 = shlex.split(cmd1)
    cmd2 = shlex.split(cmd2)
    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    return p2.communicate()


def getItemPos(item, inList):
    for i, j in enumerate(inList):
        if j == item:
            return i
    return -1

# 
# def getProcInfo(procPID):
#     procS = psutil.Process(int(procPID))
#     itemOut = {}
#     itemOut['CreateTime'] = procS.create_time()
#     ioCounters = procS.io_counters()
#     itemOut['ReadCount'] = ioCounters.read_count
#     itemOut['WriteCount'] = ioCounters.write_count
#     itemOut['ReadBytes'] = ioCounters.read_bytes
#     itemOut['WriteBytes'] = ioCounters.write_bytes
#     itemOut['ReadChars'] = ioCounters.read_chars
#     itemOut['WriteChars'] = ioCounters.write_chars
#     itemOut['NumFds'] = procS.num_fds()
#     memInfo = procS.memory_full_info()
#     memUsageProc = itemOut.setdefault('MemoryUsage', {})
#     memUsageProc['Rss'] = memInfo.rss
#     memUsageProc['Vms'] = memInfo.vms
#     memUsageProc['Shared'] = memInfo.shared
#     memUsageProc['Text'] = memInfo.text
#     memUsageProc['Lib'] = memInfo.lib
#     memUsageProc['Data'] = memInfo.data
#     memUsageProc['Dirty'] = memInfo.dirty
#     memUsageProc['Uss'] = memInfo.uss
#     memUsageProc['Pss'] = memInfo.pss
#     memUsageProc['Swap'] = memInfo.swap
#     itemOut['Connections'] = {}
#     for item in procS.connections():
#         if item.status not in itemOut['Connections'].keys():
#             itemOut['Connections'][item.status] = 0
#         itemOut['Connections'][item.status] += 1
#     return itemOut
