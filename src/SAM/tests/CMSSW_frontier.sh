#!/bin/bash
#
# Test of FroNtier under CMSSW
#
# Assumes:
#   1) environmental variables SAME_OK, SAME_WARNING and SAME_ERROR are defined
#   2) . $CMS_PATH/cmsset_default.sh has already been run
#
# $Id: CMSSW_frontier.sh,v 1.71 2012/10/24 13:33:10 asciaba Exp $
#
date
node=`uname -n`
printf "node: $node\n"
#
# Choose CMSSW version
#
cmsswvsn=CMSSW_9_0_0
#
#export SCRAM_ARCH=slc6_amd64_gcc491
# Check that environmental variable SAME_OK is set
#
if [ ! "${SAME_OK}" ]
then
   printf "CMSSW_frontier.sh: Error. SAME_OK not defined\n"
   exit 1
fi
#
# Check that environmental variable SAME_WARNING is set
#
if [ ! "${SAME_WARNING}" ]
then
   printf "CMSSW_frontier.sh: Error. SAME_WARNING not defined\n"
   exit 1
fi
#
# Check that environmental variable SAME_ERROR is set
#
if [ ! "${SAME_ERROR}" ]
then
   printf "CMSSW_frontier.sh: Error. SAME_ERROR not defined\n"
   exit 1
fi
#
# Print CMS_PATH
#
printf "CMS_PATH: $CMS_PATH\n"
#
# Check that scramv1 command was defined by . $CMS_PATH/cmsset_default.sh
#
type scramv1 > /dev/null 2>&1
sset=$?
if [ $sset -ne 0 ]
then 
   printf "CMSSW_frontier.sh: Error. scramv1 not found\n"
   exit $SAME_ERROR
fi
#
# Create Working Directory
#
mkdir frontier
cd frontier
current=`pwd`
printf "Current directory is: $current\n"
#
# Set up CMSSW 
#
printf "scramv1 project CMSSW $cmsswvsn ... starting\n"
scramv1 project CMSSW $cmsswvsn
scms=$?
if [ $scms -ne 0 ]
then
   printf "CMSSW_frontier.sh: Error. $cmsswvsn not available\n"
   exit $SAME_WARNING
fi
printf "scramv1 project CMSSW $cmsswvsn ... completed\n"
#
cd $cmsswvsn/src
printf "scramv1 runtime -sh ... starting\n"
eval `scramv1 runtime -sh | grep -v SCRAMRT_LSB_EXIT_REQUEUE | grep -v SCRAMRT_DOMAINNAME | grep -v SCRAMRT_LSB_JOBNAME`
printf "scramv1 runtime -sh ... completed\n"
#
# Return to working directory 
#
cd $current
ever_warning=0
# Execute squid test script
echo
echo "Executing the Squid test"
$SAME_SENSOR_HOME/tests/test_frontier.py 2>&1
resquid=$?
if [ $resquid -eq $SAME_ERROR ]
then 
	ever_warning=2
fi
if [ $resquid -eq $SAME_WARNING ]
then
	ever_warning=1
fi
	 
#
# Print out version
#
printf 'version: $Id: CMSSW_frontier.sh,v 1.71 2012/10/24 13:33:10 asciaba Exp $\n'
#
# Set environmenal variable for FroNtier
#
export FRONTIER_LOG_LEVEL=warning
#
# Create configuration file for cmsRun
#
/bin/cat > ecal_pedestals.py <<EOI
import FWCore.ParameterSet.Config as cms

process = cms.Process("TEST")
process.PoolDBESSource = cms.ESSource("PoolDBESSource",
    DBParameters = cms.PSet(
        messageLevel = cms.untracked.int32(0)
    ),
    timetype = cms.string('runnumber'),
    toGet = cms.VPSet(cms.PSet(
        record = cms.string('EcalPedestalsRcd'),
        tag = cms.string('EcalPedestals_mc')
    )),
    connect = cms.string('frontier://FrontierProd/CMS_CONDITIONS')
)

process.source = cms.Source("EmptySource",
    numberEventsInRun = cms.untracked.uint32(1),
    firstRun = cms.untracked.uint32(1)
)

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(5)
)
process.get = cms.EDAnalyzer("EventSetupRecordDataGetter",
    verbose = cms.untracked.bool(True),
    toGet = cms.VPSet(cms.PSet(
        record = cms.string('EcalPedestalsRcd'),
        data = cms.vstring('EcalPedestals')
    ))
)

process.dump = cms.OutputModule("AsciiOutputModule")

process.p = cms.Path(process.get)
process.ep = cms.EndPath(process.dump)

EOI
printf "configuration script:\n"
cat ecal_pedestals.py
start=`date +%s`
#
# Run cmsRun
#
printf "Squid nogzip Access test for ECAL\n" 1>&2
printf "START TIME: `date` ACTION: Squid nogzip Access test for ECAL\n"
printf "`date` --> running cmsRun ...\n"
cmsRun -p ecal_pedestals.py > stdout.txt 2>stderr.txt
srun=$?
cat stdout.txt
cat stderr.txt
printf "`date` --> DONE\n"
stop=`date +%s`
#
# Check cmsRun exit status
#
if [ $srun -ne 0 ]
then
   printf "CMSSW_frontier.sh: Error $srun from cmsRun\n"
   exit $SAME_ERROR
fi
#
# Check Trying direct connect to server
#
grep -q "Trying direct connect to server" stdout.txt
tgrep=$?
if [ $tgrep -eq 0 ]
then
	printf "CMSSW_frontier.sh: Error. Trying direct connect to CERN server\n"
	exit $SAME_ERROR
fi
#
# Check Trying next proxy
#
grep -q "Trying next proxy" stdout.txt
ngrep=$?
if [ $ngrep -eq 0 ]
then 
	printf "CMSSW_frontier.sh: Warning. one squid proxy failed\n"
	exit $SAME_WARNING
fi
#
# Check ping Warning
#
if [ $ever_warning -eq 1 ]
then
	printf "CMSSW_frontier.sh: Warning from Ping, at least one proxy ping error\n"
	exit $SAME_OK
fi
if [ $ever_warning -eq 2 ]
then 
	printf "CMSSW_frontier.sh: Warning from Ping, all the proxies ping error\n"
	exit $SAME_OK
fi
#
# Exit
#
printf "ELAPSED TIME: $[ $stop - $start ] seconds\n"
printf "OK\n"
exit $SAME_OK
