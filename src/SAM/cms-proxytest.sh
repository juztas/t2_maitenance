#!/bin/bash
#
# CE-cms-proxytest

export LANG=C

warn=0
info=0

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
    exit $SAME_WARNING
fi    

exit $SAME_OK
