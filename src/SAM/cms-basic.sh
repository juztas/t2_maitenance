#!/bin/bash
#
# CE-cms-basic
#
# This test does the following things:
# - looks for the software area
# - sources the CMS environment and checks for errors
# - checks that CMS_PATH is defined
# - checks that the Site Local Config (SLC) exists
# - checks that the SLC defines: TFC, local stageout, sitename and Frontier
# - checks that the TFC exists
#
# String exit codes:
# SW_DIR_UNDEF: location of CMS software directory undefined
# SW_DIR_NOT_READABLE: CMS software directory not existent or unreadable
# NO_SETUP_SCRIPT: could not source cmsset_default.sh
# CMS_PATH_UNDEF: CMS_PATH is undefined
# NO_JOBCONFIG_DIR: ${CMS_PATH}/SITECONF/local/JobConfig does not exist
# NO_SITELOCALCONFIG:
#   ${CMS_PATH}/SITECONF/local/JobConfig/site-local-config.xml does not exist
# NO_TFC: TFC information missing
# NO_LOCALSTAGEOUT: LocalStageOut information missing
# NO_SITENAME: Site name not found
# NO_FRONTIER_CONFIG: FroNtier information missing
# LOCAL_SITE_CONF_GIT_ERROR: site-local-config.xml different from GIT version
#   since more than 72 hours
# LOCAL_SITE_CONF_GIT_WARNING: site-local-config.xml different from GIT version
#   since less than 72 hours
# GIT_NO_ACCESS: cannot access GIT
# TFC_GIT_ERROR: TFC different from GIT version since more than 72 hours
# TFC_GIT_WARNING: TFC different from GIT version since less than 72 hours

info=0
note=0
warning=0
error=0

cp $SAME_SENSOR_HOME/tests/fetch-from-web-gitlab .

# Find software area
if [ -n "$OSG_GRID" ] ; then
    [ -f $OSG_GRID/setup.sh ] && source $OSG_GRID/setup.sh
    if [ -d $OSG_APP/cmssoft/cms ] ; then
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
if [ ! -d $SW_DIR ] ; then
    echo "SwArea: $SW_DIR"
    echo "ERROR: software directory non existent or non readable"
    echo "summary: SW_DIR_NOT_READABLE"
    exit $SAME_ERROR
fi

# Source CMS environment
echo
echo "Printing CMS site local config information..."
echo
echo Hostname: `hostname`
tmpfile=`mktemp /tmp/tmp.XXXXXXXXXX`
echo "SCRAM_ARCH: $SCRAM_ARCH"
source $SW_DIR/cmsset_default.sh > $tmpfile 2>&1
result=$?
echo "SCRAM_ARCH: $SCRAM_ARCH"
if [ $result != 0 ] ; then
    cat $tmpfile
    rm -f $tmpfile
    echo "ERROR: CMS software initialisation script cmsset_default.sh failed"
    echo "summary: NO_SETUP_SCRIPT"
    exit $SAME_ERROR
fi
rm -f $tmpfile

if [ -z "$CMS_PATH" ]; then
    echo "ERROR: CMS_PATH not defined"
    echo "summary: CMS_PATH_UNDEF"
    exit $SAME_ERROR
fi
echo "CMS_PATH: $CMS_PATH"

if [ ! -d $CMS_PATH ] ; then
    echo "ERROR: CMS_PATH directory $CMS_PATH not existing"
    echo "summary: NO_CMS_PATH"
    exit $SAME_ERROR
fi

if [ ! -d ${CMS_PATH}/SITECONF/local/JobConfig ] ; then
    echo "ERROR: JobConfig directory $CMS_PATH/SITECONF/local/JobConfig not existing"
    echo "summary: NO_JOBCONFIG_DIR"
    exit $SAME_ERROR
fi

ConfigFile=${CMS_PATH}/SITECONF/local/JobConfig/site-local-config.xml
echo "SiteLocalConfig: $ConfigFile"

if [ ! -f $ConfigFile ] ; then
    echo "ERROR: Local Configuration file site-local-config.xml not existing"
    echo "summary: NO_SITELOCALCONFIG"
    exit $SAME_ERROR
fi

TFCPath=`sed -nr '/trivialcatalog_file/s/.*:(.+)\?.*$/\1/p' $ConfigFile | uniq`
status=$?
if [ $status != 0 ] ; then
    echo "ERROR: TrivialFileCatalog string missing"
    errorSummary="summary: NO_TFC"
    error=1
else
    echo "TFCPath: $TFCPath"
fi

grep -q "local-stage-out" $ConfigFile
status=$?
if [ $status != 0 ] ; then
    echo "<p>ERROR: LocalStageOut string missing</p>"
    errorSummary="summary: NO_LOCALSTAGEOUT"
    error=1
fi

SiteName=`sed -nr '/<site name/s/^.*\"(.*)\".*$/\1/p' $ConfigFile`
status=$?
if [ $status != 0 ] ; then
    echo "ERROR: site name string missing"
    errorSummary="summary: NO_SITENAME"
    error=1
else
    echo "SiteName: $SiteName"
fi

subSiteName=""
subSiteName=`grep "subsite name" $ConfigFile | cut -d'"' -f2`
if [ -n "$subSiteName" ] ; then
    echo "SubSiteName: $subSiteName"
    subSiteName=_$subSiteName
fi

grep -q "frontier-connect" $ConfigFile
status=$?
if [ $status != 0 ] ; then
    echo "ERROR: Frontier Configuration string missing"
    errorSummary="summary: NO_FRONTIER_CONFIG"
    error=1
fi

if [ $error == 1 ] ; then
    echo "ERROR: invalid local configuration file $ConfigFile"
    echo $errorSummary
    exit $SAME_ERROR
fi

let seconds=`date +%s`-`stat -c%Y $ConfigFile`
let localConfigFileAgeInHours=$seconds/3600
echo "SiteLocalConfigAge: ${localConfigFileAgeInHours} hours"

asCvs=1
cvsUrl="https://gitlab.cern.ch/SITECONF/${SiteName}/raw/master/JobConfig/site-local-config${subSiteName}.xml"
ConfigFileFromCVS=`mktemp /tmp/site-local-config-from-CVS.xml.XXX`
echo "GITCopy: $cvsUrl"
./fetch-from-web-gitlab \"$cvsUrl\" $ConfigFileFromCVS
rc=$?
if [ $rc == 0 ] ; then
  diff -q -w -B $ConfigFile $ConfigFileFromCVS
  if [ $? == 1 ] ; then asCvs=0; fi
  if [ $asCvs == 0 ] ; then
    noConfigDump=1
    cvsMarkupUrl="https://gitlab.cern.ch/SITECONF/${SiteName}/blob/master/JobConfig/site-local-config${subSiteName}.xml"
    ConfigFileMarkup=`mktemp /tmp/site-local-config-from-CVS-Markup.xml.XXX`
    ./fetch-from-web-gitlab \"$cvsMarkupUrl\" $ConfigFileMarkup
    cvsFileDate=`/bin/awk '{i=index($0,"datetime=");if(i>0){s=substr($0,i+10,4) "-" substr($0,i+15,2) "-" substr($0,i+18,2) " " substr($0,i+21,2) ":" substr($0,i+24,2) ":" substr($0,i+27,2) "Z";print s}}' $ConfigFileMarkup`
    let seconds=`date +%s`-`date +%s -d "$cvsFileDate"`
    let cvsFileAgeInHours=$seconds/3600
    echo "GITConfigFileAge: ${cvsFileAgeInHours} hours"
    if [ $localConfigFileAgeInHours -gt 120 ] && [ $cvsFileAgeInHours -gt 120 ] ; then
      error=1
      echo "ERROR: local site configuration file differ from GIT"
      errorSummary="summary: LOCAL_SITE_CONF_GIT_ERROR"
    else
      warning=1
      echo "WARNING: local site configuration file differ from GIT"
      errorSummary="summary: LOCAL_SITE_CONF_GIT_WARNING"
    fi
    diffList=`mktemp /tmp/diflist.XXXX`
    diff $ConfigFile $ConfigFileFromCVS > $diffList
    cat $diffList | sed 's/</\&lt;/g' | sed 's/>/\&gt;/g'
    rm -f $diffList
  else
    echo "Site Local Config GIT check: OK"
  fi
  rm -f $ConfigFileFromCVS
else
  echo "WARNING: failed to access GIT repository via Gitlab"
  errorSummary="summary: GIT_NO_ACCESS"
  note=1
fi

let seconds=`date +%s`-`stat -c%Y $TFCPath`
let localTFCfileAgeInHours=$seconds/3600
echo "LocalTFCAge: ${localTFCfileAgeInHours} hours"

asCvs=1
TFCfileName=`echo $TFCPath | awk -F'/' '{print $NF}'`
cvsUrl="https://gitlab.cern.ch/SITECONF/${SiteName}/raw/master/PhEDEx/${TFCfileName}"
TfcFileFromCVS=`mktemp /tmp/storage-from-CVS.xml.XXXX`
echo "TFCGITCopy: $cvsUrl"
./fetch-from-web-gitlab \"$cvsUrl\" $TfcFileFromCVS
rc=$?

if [ $rc == 0 ] ; then
  diff -q -w -B $TFCPath $TfcFileFromCVS
  if [ $? == 1 ] ; then asCvs=0; fi
  if [ $asCvs == 0 ] ; then
    noTFCDump=1
    cvsMarkupUrl="https://gitlab.cern.ch/SITECONF/${SiteName}/blob/master/PhEDEx/${TFCfileName}"
    TfcFileMarkup=`mktemp /tmp/TFC-from-CVS-Markup.xml.XXX`
    echo "Fetch GIT Markup copy of TFC from $cvsMarkupUrl"
    ./fetch-from-web-gitlab \"$cvsMarkupUrl\" $TfcFileMarkup
    cvsFileDate=`/bin/awk '{i=index($0,"datetime=");if(i>0){s=substr($0,i+10,4) "-" substr($0,i+15,2) "-" substr($0,i+18,2) " " substr($0,i+21,2) ":" substr($0,i+24,2) ":" substr($0,i+27,2) "Z";print s}}' $TfcFileMarkup`
    let seconds=`date +%s`-`date +%s -d "$cvsFileDate"`
    let cvsFileAgeInHours=$seconds/3600
    echo "GITTFCAge: ${cvsFileAgeInHours} hours"
    if [ $localTFCfileAgeInHours -gt 120 ] && [ $cvsFileAgeInHours -gt 120 ] ; then
      error=1
      echo "ERROR: local Trivial Catalog File file differ from GIT"
      errorSummary="summary: TFC_GIT_ERROR"
    else
      warning=1
      echo "WARNING: local Trivial Catalog File file differ from GIT"
      errorSummary="summary: TFC_GIT_WARNING"
    fi
    diffList=`mktemp /tmp/diflist.XXXX`
    diff $TFCPath $TfcFileFromCVS > $diffList
    cat $diffList | sed 's/</\&lt;/g' | sed 's/>/\&gt;/g'
    rm -f $diffList
  else
    echo "TFC GIT check: OK"
  fi
  rm -f $TfcFileFromCVS
else
  echo "WARNING: failed to access GIT repository via Gitlab"
  errorSummary="summary: GIT_NO_ACCESS"
  note=1
fi

if [ -n "$noConfigDump" ] ; then
echo "Site Local Config dump:"
cat $ConfigFile
fi

if [ -n "$noTFCDump" ] ; then
echo "TFC dump:"
cat $TFCPath
fi

if [ $error == 1 ]
then
    echo $errorSummary
  exit $SAME_ERROR
fi

if [ $warning == 1 ]
then
  echo $errorSummary
  exit $SAME_WARNING
fi

if [ $note == 1 ]
then
  echo $errorSummary
  exit $SAME_WARNING
fi

if [ $info == 1 ]
then
  echo "summary: OK"
  exit $SAME_OK
fi
echo
echo "All checks OK"
echo "summary: OK"
exit $SAME_OK
