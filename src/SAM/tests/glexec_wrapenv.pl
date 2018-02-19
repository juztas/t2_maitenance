#!/usr/bin/perl -w
# $Id: glexec_wrapenv.pl,v 1.1 2012/04/02 16:09:32 asciaba Exp $
#
# Wrapper script to wrap the current environment into a single
# environment variable GLEXEC_ENV. This variable is passed 
# onto the glexec child process, where it can be unpacked to
# restore the environment variables that were lost when the
# set-uid glexec was invoked.
#
# Intended usage:
#   export GLEXEC_ENV=`glexec_wrapenv.pl`
#   /opt/glite/sbin/glexec glexec_unwrapenv.pl -- <YOUR-COMMAND>
#
# By default the following environment variables are NOT wrapped:
#   HOME LOGNAME USER X509_USER_PROXY _  (yes that's '_' !)
# A user can add more env vars to be excluded using either
#  --exclude=A --exclude=B
# or
#  --exclude=A,B,...
#
# Copyright (c) 2009 by
#   Jan Just Keijser (janjust@nikhef.nl)
#   Nikhef
#   Amsterdam
#   The Netherlands

use strict;
use warnings;

use Compress::Zlib qw(deflateInit Z_OK);
use Getopt::Long   qw(GetOptions);
use MIME::Base64   qw(encode_base64);

# These variables are excluded by default
my @env_blacklist = ( "HOME", "LOGNAME", "USER", "X509_USER_PROXY", "_" );

my @exclude_env;
my $key;
my $buf;
my $encoded_buf = '';
my $output      = '';

GetOptions ("exclude=s" => \@exclude_env);
@exclude_env = split( /,/, join( ',', @exclude_env, @env_blacklist) );

# go through all environment variables and encode them as separate 
# key-value pair entities. This will enable us to later unpack them.
foreach $key (keys(%ENV))
{ 
    if ( ! grep { /$key/ } @exclude_env )
    {
        $buf          = $key . "=" . $ENV{$key};
        $encoded_buf .= encode_base64($buf, '') . " ";
    }
    else
    {
        printf STDERR "Skipping $key\n";
    }
}

# Compress the encoded env vars to save some memory
my $x = deflateInit()
    or die "Cannot create a deflation stream\n" ;

my ($deflated_buf, $status) = $x->deflate( $encoded_buf );
$status == Z_OK or die "deflation failed\n";
$output = $deflated_buf;

($deflated_buf, $status) = $x->flush();
$status == Z_OK or die "deflation failed\n";
$output .= $deflated_buf;

# Finally, encode the compressed stream again and print it out
print encode_base64( $output, '' );

