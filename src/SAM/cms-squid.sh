#!/bin/bash

# Source the CMS environment
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
elif [ -n "$VO_CMS_SW_DIR" ] ; then
    SW_DIR=$VO_CMS_SW_DIR
else
    SW_DIR=/cvmfs/cms.cern.ch
fi
tmpfile=`mktemp /tmp/tmp.XXXXXXXXXX`
source $SW_DIR/cmsset_default.sh > $tmpfile 2>&1
result=$?
grep 'Your shell is not able to find' $tmpfile > /dev/null
result2=$?
if [ $result != 0 -o $result2 == 0 ] ; then
    cat $tmpfile
    rm -f $tmpfile
    echo "ERROR: CMS software initialisation script cmsset_default.sh failed"
    echo "summary: NO_SETUP_SCRIPT"
    exit $SAME_ERROR
fi
rm -f $tmpfile

# Execute main test script
$SAME_SENSOR_HOME/tests/test_squid.py > squid.out 2>&1
result=$?
cat squid.out
exit $result
