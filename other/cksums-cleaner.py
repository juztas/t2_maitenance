import os
from subprocess import Popen, PIPE


def callCommand(command):
    output = Popen(command,stdout=PIPE, shell=True)
    response = output.communicate()
    return response

#drwxr-xr-x   3 root nobody 4096 Aug 14 09:45 backfill
#drwxr-xr-x  52 root nobody 4096 Jul 20  2019 data
#drwxr-xr-x   6 root nobody 4096 Aug 14  2018 express
#drwxr-xr-x  12 root nobody 4096 Dec  1  2014 generator
#drwxr-xr-x   5 root nobody 4096 Dec 18  2019 group
#drwxr-xr-x  10 root nobody 4096 Mar 17  2019 hidata
#drwxr-xr-x  19 root nobody 4096 Oct  6  2019 himc
#drwxr-xr-x 271 root nobody 4096 Sep 30 10:57 mc
#drwxr-xr-x  55 root nobody 4096 Jul 31  2019 PhEDEx_LoadTest07
#drwxr-xr-x  22 root nobody 4096 Mar 31  2020 relval
#drwxr-xr-x   9 root nobody 4096 Jul 20  2019 results
#drwxr-xr-x   3 root nobody 4096 Feb  2  2020 temp
#drwxr-xr-x   4 root nobody 4096 Feb  1  2018 test
#drwxr-xr-x 118 root nobody 4096 Sep 30 02:33 unmerged
#drwxr-xr-x  18 root nobody 4096 Aug  1 09:11 user

d = '/mnt/hadoop/cksums/store/'
SUBPATHS  = [o for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]

for subdir in SUBPATHS:
    d1 = '/mnt/hadoop/cksums/store/%s' % subdir
    SUBPATHS1  = [o for o in os.listdir(d1) if os.path.isdir(os.path.join(d1,o))]
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

