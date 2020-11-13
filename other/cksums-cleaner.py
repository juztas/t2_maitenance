import os
from subprocess import Popen, PIPE


def callCommand(command):
    output = Popen(command, stdout=PIPE, shell=True)
    response = output.communicate()
    return response

CKSUMDIR = '/mnt/hadoop/cksums/store/'
SUBPATHS = [o for o in os.listdir(CKSUMDIR) if os.path.isdir(os.path.join(CKSUMDIR, o))]

for subdir in SUBPATHS:
    d1 = '/mnt/hadoop/cksums/store/%s' % subdir
    SUBPATHS1 = [o for o in os.listdir(d1) if os.path.isdir(os.path.join(d1, o))]
    for s1 in SUBPATHS1:
        ALL = 'find /mnt/hadoop/cksums/store/%s/%s -type f -follow -print' % (subdir, s1)
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
