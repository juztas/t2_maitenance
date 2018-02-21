#!/bin/bash
#
# CE-cms-env
#
# This test does the following things:
# - prints some preliminary information
# - checks that the WN complies with some CMS requirements
# - checks that a software area is defined and exists
# - checks that the software area is writable with the lcgadmin role, 
#   if the siteis not CERN and is not using CERNVM-FS
# - prints the type and version of middleware
# - the required version of lcg-cp is installed
# - checks for gfal-copy, informal print out only
# String exit codes:
# NO_CERT_DIR: did not find the X.509 certificate directory
# NO_PROXY: did not find the proxy
# CANT_CREATE_DIR: cannot create a subdirectory
# NO_COPY_PROXY: cannot copy proxy in subdirectory
# SW_DIR_UNDEF: location of CMS software directory undefined
# SW_DIR_NOT_READABLE: CMS software directory not existent or unreadable
# SW_DIR_NOT_WRITABLE: the CMS software area is not writable when it should
# WORKDIR_LOW_SPACE: less than 10 GB of free spae in working directory
# TMP_LOW_SPACE: less than 10 MB space in /tmp
# TMP_LOW_QUOTA: less than 10 GB of free quota
# STAGEOUT_CMD_INVALID: the version of the stageout command is too old
# OK: everything is OK

cat `dirname $0`/CMS-SAM-Banner.txt
export LANG=C

function check_df {
    dir=$1
    free=`df -P -B1MB $dir | awk '{if (NR==2) print $4}'`
    echo $free
    return 0
}

function check_quota {
    dir=$1
    fs=`df -kP $dir | awk '{if (NR==2) print $1}'`
    myquotastr=`quota 2>/dev/null | awk '{if (NR>2) {if (NF==1) {n=$1; getline; print n " " $2-$1} else {print $1 " " $3-$2}}}' |grep $fs`
    if [ $? -eq 0 ]; then
	# check only if there are any quotas, else ignore
	myquota=`echo $myquotastr|awk '{print $2}'`
	let "quotagb=$myquota / (2 * 1000)"
	echo $quotagb
    fi
    echo -1
    return 0
}

warn=0
info=0

echo "Printing preliminary information..."
echo
echo -n "Sysinfo: "
uname -a
/usr/bin/lsb_release -idrc
echo -n "LocalDate: "
date
echo -n "UTCDate: "
date --utc
echo -n "UserId: "
id
cat /proc/meminfo | grep Mem

# Checking some X509 details
if [ -e "$X509_CERT_DIR" ]; then
    cert_dir=$X509_CERT_DIR
elif [ -e "$HOME/.globus/certificates/" ]; then
	  cert_dir=$HOME/.globus/certificates/
elif [ -e "/etc/grid-security/certificates/" ]; then
    cert_dir=/etc/grid-security/certificates/
else
    echo "ERROR: could not find X509 certificate directory"
    echo "summary: NO_CERT_DIR"
    exit $SAME_ERROR
fi
echo "CertDir: $cert_dir"

if [ -a "$X509_USER_PROXY" ]; then
    proxy=$X509_USER_PROXY
elif [ -a "/tmp/x509up_u`id -u`" ]; then
    proxy="/tmp/x509up_u`id -u`"
else
    echo "ERROR: could not find X509 proxy certificate"
    echo "summary: NO_PROXY"
    exit $SAME_ERROR
fi
echo "Proxy: $proxy"

# Check proxy copy as in glidein pilots
local_proxy_dir=`pwd`/ticket
mkdir $local_proxy_dir
if [ $? -ne 0 ]; then
    echo "ERROR: could not find create $local_proxy_dir"
    echo "summary: CANT_CREATE_DIR"
    exit $SAME_ERROR
fi
cp $X509_USER_PROXY $local_proxy_dir/myproxy
if [ $? -ne 0 ]; then
    echo "ERROR: could not copy proxy $X509_USER_PROXY"
    echo "summary: NO_COPY_PROXY"
    exit $SAME_ERROR
fi
rm -rf $local_proxy_dir

type -t voms-proxy-info > /dev/null
result=$?
if [ $result -eq 0 ] ; then
    isvoms=1
    echo -n "UserDN: "
    voms-proxy-info -identity
    l=`voms-proxy-info -timeleft`
    echo "Timeleft: $l s"
    fqan=`voms-proxy-info -fqan`
    echo "FQAN:"
    echo "$fqan"
else
    isvoms=0
    echo "WARNING: voms-proxy-info not found"
fi
if [ $isvoms -eq 1 -a $l -lt 21600 ] ; then
    echo "WARNING: proxy shorther than 6 hours"
fi    

# Test of the local worker node environment
echo
echo "Checking local worker node environment..."
echo

# Software area definition and existence
isEGEE=0
if [ -n "$OSG_GRID" ] ; then
    [ -f $OSG_GRID/setup.sh ] && source $OSG_GRID/setup.sh
    if [ -d $OSG_APP/cmssoft/cms ] ;then
        SW_DIR=$OSG_APP/cmssoft/cms
    elif [ -d $CVMFS/cms.cern.ch ] ; then
        SW_DIR=$CVMFS/cms.cern.ch
    elif [ -d /cvmfs/cms.cern.ch ] ; then
        SW_DIR=/cvmfs/cms.cern.ch
    else
        echo "ERROR: Cannot find CMS software in OSG node"
	echo "summary: SW_DIR_UNDEF"
        exit $SAME_ERROR
    fi
    echo "SwArea: $SW_DIR"
elif [ -n "$VO_CMS_SW_DIR" ] ; then
    isEGEE=1
    SW_DIR=$VO_CMS_SW_DIR
    echo "SwArea: $SW_DIR"
else
    SW_DIR=/cvmfs/cms.cern.ch
fi
if [ ! -d $SW_DIR -o ! -r $SW_DIR ] ; then
    echo "ERROR: software directory non existent or non readable"
    echo "summary: SW_DIR_NOT_READABLE"
    exit $SAME_ERROR
fi

# Software area space
hasCVMFS=0
if [ -d $SW_DIR ] ; then
  if [ "`echo $SW_DIR | cut -d / -f 2`" == "afs" ]; then
    SPACE=`fs lq $SW_DIR | tail -1 | awk '{print (\$2-\$3)/1000000 }'`
  elif [ "`echo $SW_DIR | cut -d / -f 2`" == "cvmfs" ]; then
    hasCVMFS=1
  else
    SPACE=`df -k -P $SW_DIR | tail -1 | awk '{print \$4/1000000}'`
  fi
  if [ $hasCVMFS == 0  ]; then
    echo "FreeSWAreaSpace: $SPACE GB"
  fi
fi

# Check for free space on current directory and /tmp
space=`check_df $SAME_SENSOR_HOME`
echo "WorkDirSpace: $space MB"
if [ $space -lt 10000 ] ; then
    echo "WARNING: less than 10 GB of free space in working directory"
    summary="summary: WORKDIR_LOW_SPACE"
    warn=1
fi

space=`check_df /tmp`
echo "TmpSpace: $space MB"
if [ $space -lt 10 ] ; then
    echo "WARNING: less than 10 MB of free space in /tmp"
    summary="summary: TMP_LOW_SPACE"
    warn=1
fi

# Check quota, if any
space=`check_quota .`
if [ $space -ne -1 ] ; then
    echo "Quota: $space MB"
    if [ $space -lt 10000 ] ; then
	echo "WARNING: too little quota"
	summary="summary: TMP_LOW_QUOTA"
	warn=1
    fi
fi

# check for SL5
echo
echo "Checking OS version from $SW_DIR/common/cmsos and architecture from $SW_DIR/common/cmsarch..."
echo
slVersion="unknown"
if [ -f $SW_DIR/common/cmsos ] ; then
 osVersion=`$SW_DIR/common/cmsos`
 echo "osVersion: " $osVersion
 cmsarch=`$SW_DIR/common/cmsarch`
 echo "scram_arch: " $cmsarch
 slVersion=`echo $cmsarch|cut -d'_' -f1`
fi
echo "slVersion: " $slVersion

echo
echo "Checking middleware installation..."
echo
mw=0
if type -f glite-version > /dev/null 2>&1; then
    type="gLite"
    mwver=`glite-version`
    mw=1
elif [ -f /etc/emi-version ] ; then
    type="EMI"
    mwver=`cat /etc/emi-version`
    mw=1
elif [ -f $EMI_UI_CONF/etc/emi-version ] ; then
    type="EMI"
    mwver=`cat $EMI_UI_CONF/etc/emi-version`
    mw=1
elif type -f lcg-version > /dev/null 2>&1; then
    type="LCG"
    mwver=`lcg-version`
    mw=1
fi
if [ $mw == 1 ] ; then
    echo "Middleware: $type $mwver"
else
    echo "WARNING: Cannot find middleware stack type and version"
fi
echo

type -t lcg-cp > /dev/null
result=$?
stageout=1
if [ $result -ne 0 ] ; then
    echo "WARNING: lcg-cp not in the PATH"
else
    lcgutilver=`lcg-cp --version | grep lcg_util | sed 's/lcg_util-//'`
    echo "lcg_util: $lcgutilver"
    gfalver=`lcg-cp --version | grep GFAL-client | sed 's/GFAL-client-//'`
    echo "GFAL-client: $gfalver"
    lver=(`echo $lcgutilver | awk -F . '{print $1*10000+$2*100+$3}'`)
    echo -n "Minimum version of lcg-cp: 1.6.7: "
    if [ $lver -ge 10607 ] ; then
	stageout=0
	echo "OK"
    else
	echo
	echo "WARNING: lcg-cp older than 1.6.7"
    fi
fi

type -t gfal-copy > /dev/null
result=$?
if [ $result -ne 0 ] ; then
    echo "WARNING: gfal-copy not in the PATH"
else
    gfalver=`gfal-copy -V 2>&1`
    echo "GFAL2 clients: $gfalver"
    stageout=0
fi
if [ $stageout == 1 ] ; then
    echo "ERROR: no valid command for remote stageout"
    echo "summary: STAGEOUT_CMD_INVALID"
    exit $SAME_ERROR
fi
echo
if [ $warn == 1 ] ; then
    echo $summary
    exit $SAME_WARNING
fi
if [ $info == 1 ] ; then
    echo $summary
    exit $SAME_OK
fi
echo "All checks OK"
echo "summary: OK"
exit $SAME_OK

