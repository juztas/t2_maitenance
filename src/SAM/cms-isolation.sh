#! /bin/bash
#
# CE-cms-isolation
#
# This test runs the Singularity and the glexec tests and passes only if one of the tests passes
export NAG_OK=0
export NAG_WARNING=1
export NAG_CRITICAL=2
export NAG_UNKNOWN=3

$SAME_SENSOR_HOME/tests/CE-cms-singularity
result=$?
if [ $result = $SAME_OK ] ; then
    echo
    echo "Singularity test passed"
    exit $result
else
    echo
    echo "Singularity test failed, executing glexec test..."
    echo
fi
$SAME_SENSOR_HOME/tests/glprobe.sh -v 1
result=$?
if [ $result = $NAG_OK ] ; then
    echo "glexec test passed"
else
    echo "glexec test failed"
    echo "Isolation test failed"
fi
if [ $result = $NAG_OK ] ; then
    exit $SAME_OK
elif [ $result = $NAG_CRITICAL ] ; then
    exit $SAME_ERROR
elif [ $result = $NAG_WARNING ] ; then
    exit $SAME_WARNING
fi
exit $result
