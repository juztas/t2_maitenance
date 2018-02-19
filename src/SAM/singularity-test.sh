#!/bin/sh

# some known singularity locations
for LOCATION in \
         /util/opt/singularity/2.2.1/gcc/4.4/bin \
         /util/opt/singularity/2.2/gcc/4.4/bin \
         /uufs/chpc.utah.edu/sys/installdir/singularity/std/bin ; do
     if [ -e "$LOCATION" ]; then
         echo " ... prepending $LOCATION to PATH"
         export PATH="$LOCATION:$PATH"
         break
     fi
done
export PATH
HAS_SINGULARITY="False"
export OSG_SINGULARITY_VERSION=`singularity --version 2>/dev/null`
if [ "x$OSG_SINGULARITY_VERSION" != "x" ]; then
     HAS_SINGULARITY="True"
     export OSG_SINGULARITY_PATH=`which singularity`
else
     # some sites requires us to do a module load first - not sure if we always want to do that
     export OSG_SINGULARITY_VERSION=`module load singularity >/dev/null 2>&1; singularity --version 2>/dev/null`
     if [ "x$OSG_SINGULARITY_VERSION" != "x" ]; then
         HAS_SINGULARITY="True"
         export OSG_SINGULARITY_PATH=`module load singularity >/dev/null 2>&1; which singularity`
     fi
fi

# default image for this glidein
export OSG_SINGULARITY_IMAGE_DEFAULT="/cvmfs/singularity.opensciencegrid.org/bbockelm/cms:rhel6"

# for now, we will only advertise singularity on nodes which can access cvmfs
if [ ! -e "$OSG_SINGULARITY_IMAGE_DEFAULT" ]; then
     HAS_SINGULARITY="False"
fi

# Let's do a simple singularity test by echoing something inside, and then
# grepping for it outside. This takes care of some errors which happen "late"
# in the execing, like:
# ERROR  : Could not identify basedir for home directory path: /
if [ "x$HAS_SINGULARITY" = "xTrue" ]; then
     SINGULARITY_HOME=`mktemp -d`
     echo "$OSG_SINGULARITY_PATH exec --home $SINGULARITY_HOME:/srv --bind /cvmfs --bind $SINGULARITY_HOME:/srv --pwd /srv --scratch /var/tmp --scratch /tmp --containall $OSG_SINGULARITY_IMAGE_DEFAULT echo Hello World | grep Hello World"
     if ! ($OSG_SINGULARITY_PATH exec --home $SINGULARITY_HOME:/srv \
                                      --bind /cvmfs \
                                      --bind $SINGULARITY_HOME:/srv \
                                      --pwd /srv \
                                      --scratch /var/tmp \
                                      --scratch /tmp \
                                      --containall \
                                      "$OSG_SINGULARITY_IMAGE_DEFAULT" \
                                      echo "Hello World" \
                                      | grep "Hello World") 1>&2 \
     ; then
         # singularity simple exec failed - we are done
         echo "ERROR: Singularity simple exec failed.  Disabling support"
	 echo "summary: SINGULARITY_FAILED"
	 /bin/rm -rf $SINGULARITY_HOME
         exit $SAME_ERROR
     fi
     echo "summary: OK"
     /bin/rm -rf $SINGULARITY_HOME
     exit $SAME_OK
fi
echo "ERROR: Could not find singularity on system"
echo "summary: NO_SINGULARITY"
exit $SAME_ERROR
