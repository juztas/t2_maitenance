import os
from subprocess import Popen, PIPE


def callCommand(command):
    output = Popen(command, stdout=PIPE, shell=True)
    response = output.communicate()
    return response

CKSUMDIR = '/mnt/hadoop/cksums/store/user/'
SUBPATHS = [o for o in os.listdir(CKSUMDIR) if os.path.isdir(os.path.join(CKSUMDIR, o))]

for subdir in SUBPATHS:
    d1 = '/mnt/hadoop/cksums/store/user/%s' % subdir
    SUBPATHS1 = [o for o in os.listdir(d1) if os.path.isdir(os.path.join(d1, o))]
    for s1 in SUBPATHS1:
        s2 = os.path.join(d1, s1)
        SUBPATHS2 = [o for o in os.listdir(s2) if os.path.isdir(os.path.join(s2, o))]
        for s3 in SUBPATHS2:
            s4 = os.path.join(s2, s3)
            ALL = 'find %s -type f -follow -print' % s4
            print ALL
            for fname in callCommand(ALL)[0].split('\n'):
                if fname.startswith('/mnt/hadoop/cksums'):
                    cksumsfile = fname
                    normalfile = '/mnt/hadoop/' + fname[19:]
                    if os.path.isfile(normalfile):
                        print normalfile
                    else:
                        print 'R:' + cksumsfile
                        os.remove(cksumsfile)
