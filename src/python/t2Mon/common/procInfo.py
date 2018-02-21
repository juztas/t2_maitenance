#!/usr/bin/python
import psutil

def getProcInfo(procPID):
    procS = psutil.Process(int(procPID))
    itemOut = {}
    itemOut['CreateTime'] = procS.create_time()
    ioCounters = procS.io_counters()
    itemOut['ReadCount'] = ioCounters.read_count
    itemOut['WriteCount'] = ioCounters.write_count
    itemOut['ReadBytes'] = ioCounters.read_bytes
    itemOut['WriteBytes'] = ioCounters.write_bytes
    itemOut['ReadChars'] = ioCounters.read_chars
    itemOut['WriteChars'] = ioCounters.write_chars
    itemOut['NumFds'] = procS.num_fds()
    memInfo = procS.memory_full_info()
    memUsageProc = itemOut.setdefault('MemoryUsage', {})
    memUsageProc['Rss'] = memInfo.rss
    memUsageProc['Vms'] = memInfo.vms
    memUsageProc['Shared'] = memInfo.shared
    memUsageProc['Text'] = memInfo.text
    memUsageProc['Lib'] = memInfo.lib
    memUsageProc['Data'] = memInfo.data
    memUsageProc['Dirty'] = memInfo.dirty
    memUsageProc['Uss'] = memInfo.uss
    memUsageProc['Pss'] = memInfo.pss
    memUsageProc['Swap'] = memInfo.swap
    itemOut['Connections'] = {}
    for item in procS.connections():
        if item.status not in itemOut['Connections'].keys():
            itemOut['Connections'][item.status] = 0
        itemOut['Connections'][item.status] += 1
    return itemOut
