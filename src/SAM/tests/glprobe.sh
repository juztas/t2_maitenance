#! /bin/bash

function add2buffer {
    echo $1
}

function do_print {
    echo $1
    echo "summary: $1"
}

# Change to test directory
cd `dirname $0`

# parse arguments
verbosity="1"
while getopts  "v:H:t:" flag
do
  case "$flag" in
      v) verbosity=$OPTARG;;
      H) host=$OPTARG;;
      t) timeout=$OPTARG;;
  esac
done

exitcode=$NAG_OK

# Print environment information
now="`date -u +'%F %T'` UTC"
now_local="`date`"
currdir=$PWD
host=`uname -n`
pilotid=`/usr/bin/id`
pilotidu=`/usr/bin/id -u`
pilotidg=`id -G | tr ' ' '\n' | sort -n | tr '\n' ' '`
add2buffer "Ran at $now ($now_local) on host $host as user:"
add2buffer "$pilotid" 

# Check that $X509_USER_PROXY points to an existing file
if [ -z "$X509_USER_PROXY" ]; then
    do_print "Error: X509_USER_PROXY is not defined"
    exit $NAG_CRITICAL
fi

add2buffer ""
add2buffer "Pilot Information:"

if [ -f "$X509_USER_PROXY" ]; then
    add2buffer "X509_USER_PROXY=$X509_USER_PROXY"
else
    do_print "Error: X509_USER_PROXY points to a non existing location"
    exit $NAG_CRITICAL
fi


# Setup the grid environment:
if [ -n "$OSG_GRID" ] ; then
    # workaround to suppress voms errors on OSG
    export VOMS_PROXY_INFO_DONT_VERIFY_AC="1"
    [ -f $OSG_GRID/setup.sh ] && source $OSG_GRID/setup.sh
fi

dn=`voms-proxy-info --identity`
fqan=`voms-proxy-info --fqan | head -1`
add2buffer "DN: $dn"
add2buffer "Primary FQAN: $fqan"

add2buffer ""
add2buffer "Environment information:"

# Set the CMS environment
if [ -n "$VO_CMS_SW_DIR" ]; then
    SW_DIR=$VO_CMS_SW_DIR
    add2buffer "VO_CMS_SW_DIR=$VO_CMS_SW_DIR"
elif [ -n "$OSG_APP" ] ; then
    SW_DIR=$OSG_APP/cmssoft/cms
    if [ ! -d $SW_DIR ] ; then
	SW_DIR=$OSG_APP
        add2buffer "OSG_APP=$OSG_APP"
    else
        add2buffer "OSG_APP/cmssoft/cms=$OSG_APP/cmssoft/cms"
    fi
elif [ -n "$CVMFS" ] ; then
    SW_DIR=$CVMFS/cms.cern.ch
    add2buffer "CVMFS (via env)=$CVMFS/cms.cern.ch"
elif [ -e "/cvmfs/cms.cern.ch" ] ; then
    SW_DIR=/cvmfs/cms.cern.ch
    add2buffer "CVMFS=/cvmfs/cms.cern.ch"
else
    do_print "Error: None of OSG_APP, VO_CMS_SW_DIR, or CVMFS are present."
    exit $NAG_CRITICAL
fi

if [ ! -f $SW_DIR/cmsset_default.sh ]; then
    do_print "Error: cmssw setup file $SW_DIR/cmsset_default.sh not existing"
    exit $NAG_CRITICAL
fi
add2buffer "CMS configuration file: $SW_DIR/cmsset_default.sh"

export SCRAM_ARCH=slc5_amd64_gcc434
source $SW_DIR/cmsset_default.sh
err=$?
if [ $err != 0 ]; then
    do_print "Error: CMS software initialisation script cmsset_default.sh failed"
    exit $NAG_CRITICAL
fi

if [ -z $CMS_PATH ]; then
    do_print "Error: CMS_PATH not defined"
    exit $NAG_CRITICAL
fi

if [ ! -d $CMS_PATH ] ; then
    do_print "Error: CMS_PATH directory $CMS_PATH not existing"
    exit $NAG_CRITICAL
fi

# Parse the local config file and find site name
if [ ! -d $CMS_PATH/SITECONF/local/JobConfig ] ; then
    do_print "Error: JobConfig directory $CMS_PATH/SITECONF/local/JobConfig not existing"
    exit $NAG_CRITICAL
fi

ConfigFile=${CMS_PATH}/SITECONF/local/JobConfig/site-local-config.xml
if [ ! -f $ConfigFile ] ; then
    do_print "Error: Local Configuration file site-local-config.xml not existing"
    exit $NAG_CRITICAL
fi
add2buffer "Local configuration file: $ConfigFile"

grep -q "site name" $ConfigFile
err=$?
if [ $err != 0 ] ; then
    do_print "Error: site name string missing in config file"
    exit $NAG_CRITICAL
fi

siteName=`grep "site name" $ConfigFile | grep -v "subsite name" | cut -d'"' -f2`
add2buffer "Site name: $siteName"

tier=`grep "site name" $ConfigFile | grep -v "subsite name" | cut -d'"' -f2 | cut -d '_' -f1`
if [ -f $currdir/payloadproxy-t2 ]; then
    mv -f $currdir/payloadproxy-t2 $currdir/payloadproxy
    add2buffer "Using standard cms proxy for the payload"
fi

# Check that the payload proxy is available
if [ -f "$currdir/payloadproxy" ]; then
    chmod 600 $currdir/payloadproxy
    export GLEXEC_CLIENT_CERT=$currdir/payloadproxy
    add2buffer "GLEXEC_CLIENT_CERT: $GLEXEC_CLIENT_CERT"
else
    do_print "Error: payloadproxy not found"
    exit $NAG_CRITICAL
fi

add2buffer ""
add2buffer "Payload information:"
dn=`voms-proxy-info -file $currdir/payloadproxy --identity`
fqan=`voms-proxy-info -file $currdir/payloadproxy --fqan | head -1`
timeleft=`voms-proxy-info -file $currdir/payloadproxy --timeleft`
actimeleft=`voms-proxy-info -file $currdir/payloadproxy --actimeleft`
add2buffer "Payload DN: $dn"
add2buffer "Payload Primary FQAN: $fqan"
add2buffer "There are $timeleft seconds until the payload proxy expires ($actimeleft until the VOMS extension expires)"

add2buffer ""
add2buffer "Glexec Invocation:"

# finding the glexec environment
glexec=${OSG_GLEXEC_LOCATION:-${GLEXEC_LOCATION:-${GLITE_LOCATION:-/usr}}/sbin/glexec}
if [ -f "$glexec" ]; then
    add2buffer "Using glexec at $glexec"
    glexec_ver=`$glexec -v`
    add2buffer "$glexec_ver"
else
    do_print "Error: No files found at $glexec"
    exit $NAG_CRITICAL
fi
glexecdir=`dirname $glexec`

# workaround for glexev older than 0.7
export GLEXEC_SOURCE_PROXY=${GLEXEC_CLIENT_CERT}
add2buffer "GLEXEC_SOURCE_PROXY: $GLEXEC_SOURCE_PROXY"
export GLEXEC_TARGET_PROXY="/tmp/x509up_u`id -u`.glexec.${RANDOM}"
add2buffer "GLEXEC_TARGET_PROXY: $GLEXEC_TARGET_PROXY"

# run a bare glexec test and verify that the uid/gid is changed
payloadid=`$glexec /usr/bin/id -u`
err=$?
if [ $err -ne 0 ]; then
    do_print "Error: error $err executing $glexec getting payload uid"
    exit $NAG_CRITICAL
fi

if [ -z "$payloadid" ]; then
    do_print "Error: /usr/bin/id -u returned an empty string for the payload"
    exit $NAG_CRITICAL
fi

if [ "X$payloadid" == "X$pilotidu" ]; then

    # In this case, test the GIDs
    payloadidg=`$glexec /usr/bin/id -G | tr ' ' '\n' | sort -n | tr '\n' ' '`

    err=$?
    if [ $err -ne 0 ]; then
        do_print "Error: error $err executing $glexec getting payload gid"
        exit $NAG_CRITICAL
    fi

    if [ -z "$payloadidg" ]; then
        do_print "Error: /usr/bin/id -G returned an empty string for the payload"
        exit $NAG_CRITICAL
    fi

    if [ "X$payloadidg" == "X$pilotidg" ]; then
        add2buffer "Warning: Same /usr/bin/id for payload and pilot"
        exitcode=$NAG_WARNING
    fi

fi
add2buffer "Payload id: $payloadid"

# find mkgltempdir and create a termporary directory for payload execution
if [ -f "$glexecdir/mkgltempdir" ]; then
    mkgltempdir=$glexecdir/mkgltempdir
else
    mkgltempdir=$currdir/mkgltempdir
fi
add2buffer "Using mkgltempdir at $mkgltempdir"

stickydir=`$mkgltempdir`
err=$?
if [ $err -ne 0 ]; then
    do_print "Warning: error $err executing $mkgltempdir"
    exit $NAG_WARNING
fi
add2buffer "stickydir: $stickydir"
tmpdir=`dirname $stickydir`

# copy the payload executable to the payload execution directory
cp $currdir/payload.sh $tmpdir
chmod 755 $tmpdir/payload.sh
$glexec /bin/cp $tmpdir/payload.sh $stickydir
rm $tmpdir/payload.sh

# create a job wrapper and copy it to the payload execution directory
cat > $tmpdir/wrapper.sh << EOF
#! /bin/bash
cd $stickydir
./payload.sh > payload.out 2> payload.err
# Make the output readable by the pilot
chmod a+rx .
chmod a+r ./*
EOF
chmod 755 $tmpdir/wrapper.sh
$glexec /bin/cp $tmpdir/wrapper.sh $stickydir
rm $tmpdir/wrapper.sh

# execute the payload (payload identity) and move the output to the current directory
$glexec $stickydir/wrapper.sh
err=$?
if [ $err -eq 0 ]; then
    cp $stickydir/payload.out $currdir
    cp $stickydir/payload.err $currdir
else 
    add2buffer "Warning: error $err executing the payload"
    exitcode=$NAG_WARNING
fi

# cleanup the execution directory tree
$glexec /bin/rm $stickydir/*
$mkgltempdir -r $stickydir

# Check payload output for "Hello world"
if [ `grep -q "Hello world" payload.out; echo $?` -ne 0 ]; then
    add2buffer "Warning: payload stdout appears incorrect."
    exitcode=$NAG_WARNING
fi

# Print payload output
add2buffer "payload.out:"
cat $currdir/payload.out
add2buffer "payload.err:"
cat $currdir/payload.err
add2buffer "Test finished"

# exit
if [ $exitcode -ne 0 ]; then
    do_print "Warning: execution contains warnings"
else
    do_print "Success"
fi
exit $exitcode
