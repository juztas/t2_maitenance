import os
import sys
# Find out which deamon we talk about
# Available options:
#    gridftp;
#    xrootd;
#    namenode;
#    datanode;
#    future - htcondor;
#    future - xrootd-cache;
def getDaemon(daemonName):
    if daemonName == 'xrootd':
        from t2Mon.xrootd.xrootd import MyDaemon
    elif daemonName == 'gridftp':
        from t2Mon.gridftp.gridftp import MyDaemon
    elif daemonName == 'namenode':
        from t2Mon.hdfs.namenode import MyDaemon
    elif daemonName == 'datanode':
        from t2Mon.hdfs.datanode import MyDaemon
    else:
        print "Unknown Daemon. Available: xrootd, gridftp, namenode, datanode"
        sys.exit(2)
    return MyDaemon('/tmp/daemon-%s.pid' % daemonName,
                    stdout='/var/log/t2Mon/%s/std.out' % daemonName,
                    stderr='/var/log/t2Mon/%s/std.err' % daemonName)  # pass stdout, stderr

if __name__ == "__main__":
    daemonName = sys.argv[1]
    daemon = getDaemon(daemonName)
    if len(sys.argv) == 3:
        if sys.argv[2] == 'start':
            daemon.start()
        elif sys.argv[2] == 'stop':
            daemon.stop()
        elif sys.argv[2] == 'restart':
            daemon.restart()
        elif sys.argv[2] == 'status':
            daemon.status()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|status|restart" % sys.argv[0]
        sys.exit(2)