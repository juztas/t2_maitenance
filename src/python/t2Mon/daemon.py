#!/usr/bin/env python
""" Daemonize services """
import sys
import os
import time
import atexit
from signal import SIGTERM

def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

class Daemon(object):
    """
    A generic daemon class.
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        stdi = file(self.stdin, 'r')
        stdo = file(self.stdout, 'a+')
        stde = file(self.stderr, 'a+', 0)
        os.dup2(stdi.fileno(), sys.stdin.fileno())
        os.dup2(stdo.fileno(), sys.stdout.fileno())
        os.dup2(stde.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        """ Delete pid file """
        os.remove(self.pidfile)

    def start(self, runTimer):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pidf = file(self.pidfile, 'r')
            pid = int(pidf.read().strip())
            pidf.close()
        except IOError:
            pid = None

        if pid and check_pid(pid):
            message = "pidfile %s already exist and service is running.\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        elif pid:
            message = "pidfile %s already exists, but service is not running.\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run(runTimer)

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pidf = file(self.pidfile, 'r')
            pid = int(pidf.read().strip())
            pidf.close()
            if not check_pid(pid):
                print 'PID exists, but process is not running'
                sys.exit(1)
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def status(self):
        """
        Daemon status
        """
        try:
            pidf = file(self.pidfile, 'r')
            pid = int(pidf.read().strip())
            print 'PID %s' % pid
            pidf.close()
        except IOError:
            pid = None
            print 'Is application running?'
            sys.exit(1)

    def restart(self, runTimer):
        """
        Restart the daemon
        """
        self.stop()
        self.start(runTimer)

    def run(self, runTimer):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
# START WILL FAIL IF LOG DIR IS NOT SET!!!
